from os import read
import MySQLdb
import pandas as pd
import psycopg2
from psycopg2.extensions import AsIs
from psycopg2 import OperationalError, errorcodes, errors
import time
import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
import psycopg2.extensions
import PostgresConn
from config.loadData import readJson
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)



def ConMysql(data):   
    server = data["Comer"]["host"]
    database =  data["Comer"]["dbname"]
    username = data["Comer"]["username"] 
    password = data["Comer"]["password"]
    port = int(data["Comer"]["port"])
    df = None
    try: 
        conn = MySQLdb.connect(host=server,port=port,user=username,passwd=password,db=database)
        print("Conexion establecida con la base de datos...'{}' en servidor : {}".format(database, server))  
        sql = '''select cp.id as id, cp.fecha_carga_cp, cp.estado_cp, cp.fecha_descarga_cp, cp.cliente_cp, cp.numero_pedido_cp, cp.empresa_cp, pr.descripcion_p , pr.producto_p ,
        lp.id as id_x, lp.fecha_produccion_lp, lp.articulo_lp, lp.unidades_lp,  lp.lote_cliente_lp, lp.empresa_lp, lp.producto_lp, lp.estado_lp,
        lp.centro_lp, lp.palets_lp, tipo_palets_lp, lp.cajas_por_palet_lp, cl.nombre_c, cl.cliente_c, cp.dir_sum_cp, ds.nombre_ds, cl.poblacion_c, en.descripcion_e,
        (select detalle_e from frf_estado_pedidos ep where ep.id = lp.estado_lp ) as nombre_estado
        from (SELECT * FROM frf_cabecera_pedidos order by id desc limit 600) cp 
        inner join frf_linea_pedidos lp on lp.numero_pedido_lp = cp.id 
        left join frf_envases en on en.envase_e = lp.articulo_lp
        left join frf_clientes cl on cl.cliente_c =  cp.cliente_cp
        left join frf_productos pr on pr.producto_p = en.producto_e
        left join frf_dir_sums ds on concat(ds.cliente_ds, ds.dir_sum_ds) = concat(cp.cliente_cp, cp.dir_sum_cp)
        where lp.empresa_lp='050' and centro_lp='1' and lp.deleted_at IS NULL;'''
        df = pd.read_sql(sql, conn)        
    except Exception as err:
        print("Error de base de datos: {}".format(err))
        quit()
    else:
        conn.close()          
    return df


def cleanFields(df):
    df["descripcion_p"] = df["descripcion_p"].str.replace(r"'", ".")
    df["nombre_c"] = df["nombre_c"].str.replace(r"'", ".")
    df["nombre_ds"] = df["nombre_ds"].str.replace(r"'", ".")
    df["poblacion_c"] = df["poblacion_c"].str.replace(r"'", ".")
    df["empresa_lp"] = df["empresa_lp"].str.replace(r"'", ".")
    df["descripcion_e"] = df["descripcion_e"].str.replace(r"'", ".")
    df["descripcion_e"] = df["descripcion_e"].str.replace(r'\xad', '', regex=True)    
    return df

def ActualizarDat(db, row, df_aux):    
    
    cadena ="fecha_carga='"+str(row["fecha_carga_cp"])+"'"
    cadena = cadena+",fecha_entrega='"+str(row["fecha_descarga_cp"])+"'"
    cadena = cadena+",fecha_produccion='"+str(row["fecha_produccion_lp"])+"'"
    cadena = cadena+",num_pedido='"+str(row["numero_pedido_cp"])+"'"
    cadena = cadena+",producto='"+str(row["descripcion_p"])+"'"
    cadena = cadena+",articulo='"+str(row["articulo_lp"])+"'"   
    cadena = cadena+",num_palets="+str(row["palets_lp"])    
    cadena = cadena+",cliente='"+str(row["nombre_c"])+"'"    
    cadena = cadena+",direccion='"+str(row["nombre_ds"])+"'"
    cadena = cadena+",entrega='"+str(row["poblacion_c"])+"'"
    cadena = cadena+",estado="+str(row["estado_lp"])
    cadena = cadena+",descripcion='"+str(row["descripcion_e"])+"'"    
    cadena = cadena+",envases="+str(row["unidades_lp"])
    cadena = cadena+",cajas="+str(row["cajas_por_palet_lp"])
    cadena = cadena+",empresa='"+str(row["empresa_cp"])+"'"
    cadena = cadena+",codigo_cliente='"+str(row["cliente_cp"])+"'"
    cadena = cadena+",codigo_producto='"+str(row["producto_lp"])+"'"
    cadena = cadena+",centro='"+str(row["centro_lp"])+"'"
    cadena = cadena+",nombre_estado='"+str(row["nombre_estado"])+"'"
    cadena = cadena+",tipo_palet='"+str(row["tipo_palets_lp"])+"'"
    cadena = cadena+",lote_cliente='"+str(row["lote_cliente_lp"])+"'"
    cadena = cadena+",ruta="+str(COMfilter(row["articulo_lp"],row["cliente_c"],row["dir_sum_cp"],df_aux)) 
    db.modifyManual("pedidosllanos", cadena, row["id_x"])    

    
def InsertarDat(db, row, df_aux):
    #print("Datos")
    db.insert("pedidosllanos",'(id,fecha_carga,fecha_entrega,fecha_produccion,num_pedido, producto,articulo,num_palets,palets_asig,palets_completos,cliente,direccion,entrega,estado,descripcion,envases,cajas,ruta,lote_cliente, empresa, codigo_cliente, codigo_producto, centro, tipo_palet, nombre_estado)',\
                (row["id_x"],str(row["fecha_carga_cp"]),str(row["fecha_descarga_cp"]),str(row["fecha_produccion_lp"]),str(row["numero_pedido_cp"]),row["descripcion_p"],\
                row["articulo_lp"],row["palets_lp"],row["palets_lp"],"0",str(row["nombre_c"]),str(row["nombre_ds"]),str(row["poblacion_c"]),str(row["estado_lp"]),row["descripcion_e"],\
                str(row["unidades_lp"]),str(row["cajas_por_palet_lp"]),COMfilter(row["articulo_lp"],row["cliente_c"],row["dir_sum_cp"],df_aux),str(row["lote_cliente_lp"]),row["empresa_cp"], row["cliente_cp"], row["producto_lp"], row["centro_lp"], row["tipo_palets_lp"], row["nombre_estado"]))
    #print("insertado "+str(row["id_x"])) 
       
def CompareDat(db, df, df_aux):   
    i = 0
    y= 0    
    compare = db.selectall("id", "pedidosllanos", "dataframe")
    for index, row in df.iterrows():
            try:
                if int(row["id_x"]) in compare.values:                    
                    ActualizarDat(db, row, df_aux)
                    y = y+1
                else:                    
                    InsertarDat(db, row, df_aux)
                    i = i+1
            except Exception as err:
                print("Error {} en linea {} con id de pedido {}".format(err, i+y, row["id_x"]))

    print("Se han insertado {} registros".format(i))
    print("Se han actualizado {} registros".format(y))    
def IniProcess():
    print("Inicio")
    start_time = time.time()
    datos = readJson()      
    df = ConMysql(datos)
    db = PostgresConn.Database(datos) 
    df_aux = db.read("SELECT * FROM public.fichas_tecnicas;", "dataframe")     
    df = cleanFields(df)
    CompareDat(db, df, df_aux)
    print("Fin del proceso en --- %s seconds ---" % (time.time() - start_time))    

def COMfilter(COM,cliente,dir_sum,df):
    ruta = 0
    try:
        if not df.loc[(df["articulo"] == str(COM)) & (df["cliente"].str.replace(' ', '') == cliente) & (df["dir_sum"].str.replace(' ', '') == dir_sum)].empty:
            ruta = str(int(df.loc[(df["articulo"] == str(COM)) & (df["cliente"].str.replace(' ', '') == cliente) & (df["dir_sum"].str.replace(' ', '') == str(dir_sum))].id.to_string(index=False)))
        
        elif not df.loc[(df["articulo"] == str(COM)) & (df["cliente"].str.replace(' ', '') == cliente) & (df["dir_sum"].str.replace(' ', '') == '')].empty:
            ruta = str(int(df.loc[(df["articulo"] == str(COM)) & (df["cliente"].str.replace(' ', '') == cliente) & (df["dir_sum"].str.replace(' ', '') == '')].id.to_string(index=False)))
        
        elif not df.loc[(df["articulo"] == str(COM)) & (df["cliente"].str.replace(' ', '') == '') & (df["dir_sum"].str.replace(' ', '') == '')].empty:
            ruta = str(int(df.loc[(df["articulo"] == str(COM)) & (df["cliente"].str.replace(' ', '') == '') & (df["dir_sum"].str.replace(' ', '') == '')].id.to_string(index=False)))

    except:
        ruta = 0

    return ruta


if __name__ == "__main__":    
    IniProcess()