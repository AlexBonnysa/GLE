from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask.json import load
import pandas as pd
from pandas.core.frame import DataFrame
import datetime
import os.path, sys
import json
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from PostgreeConnDB import PostgreeConnDB
from config.loadData import readJson
from . import asignacion
from . import Actualizar_pedidos



#settings
asignacion.secret_key = "770071010"

#Creamos la variable global last_ofs para agilizar las querys individuales   
datosIni = readJson()
sql = PostgreeConnDB("BonnysaDB")
last_ofs = sql.select_ofs_by_date(14)


 

@asignacion.route("/asignaciones")
def Index():

    return render_template("asignaciones.html")

@asignacion.route("/getAsignacionesData")
def getAsignacionesData():
    #Querys en la base de datos
    pedidos = sql.select_orders(7) # El número define los días por dentrale y por detras del actual, del que se quieren registros
    ofs = sql.select_ofs_by_date(14)
    global last_ofs 
    last_ofs = ofs

    #Campos adicionales a la base de datos para cuadrar con el front
    pedidos['check'] = ""
    pedidos['desplegable'] = ""
    pedidos['palets_sin_asignar'] = pedidos['num_palets'] - pedidos['palets_asig']

    #Cambiar formatos de fecha datetime a string
    pedidos['fecha_carga'] = pedidos['fecha_carga'].map(lambda ts: ts.strftime("%Y-%m-%d"))
    pedidos['fecha_entrega'] = pedidos['fecha_entrega'].map(lambda ts: ts.strftime("%Y-%m-%d"))
    pedidos['fecha_produccion'] = pedidos['fecha_produccion'].map(lambda ts: ts.strftime("%Y-%m-%d"))
    pedidos['producto'] = pedidos['codigo_producto']+'-'+pedidos['producto']
    pedidos['cliente'] =  pedidos['codigo_cliente']+'-'+pedidos['cliente']
    #dataframe ordenado para formatear a array de arrays
    etl_pedidos = pedidos[['check','desplegable','id','fecha_carga', 'fecha_entrega', 'fecha_produccion', 'num_pedido',  'producto', 'articulo',\
        'lote_cliente', 'cliente', 'num_palets', 'cajas', 'linea', 'palets_asig', 'palets_completos', 'palets_sin_asignar', 'nombre_estado']]

    #Crear un array de arrays de pedidos
    array_of_arrays = etl_pedidos.to_dict('split')

    return  array_of_arrays

@asignacion.route("/getOfAsignacion", methods = ["POST","GET"])
def getOfAsignacion():
    # Transformar el valor de petición a un int
    idpedido = request.args['data']
    ofs = last_ofs.loc[last_ofs['id_pedido'] == int(idpedido)]
    ofs = ofs.set_index('id')
    #dataframe ordenado para formatear a array de arrays
    etl_ofs = ofs[['status', 'originalquantity', 'destrio', 'description', 'linea_id', 'quantity']]
    #Crear un array de arrays de pedidos
    array_of_arrays = etl_ofs.to_dict('split')

    return  array_of_arrays

@asignacion.route("/asignaciondirecta", methods = ["POST","GET"])
def asignaciondirecta():
    column_names = ['error', 'id_pedido', 'id', 'status', 'originalquantity', 'destrio', 'description', 'linea_id', 'quantity']
    res = pd.DataFrame(columns = column_names)
    response = request.get_json()
    for i in response['obj']['pedidos']:
        try:
            #Comparamos los pallets antiguos con los nuevos y modificamos el pedido
            pedido = sql.select_pedido_by_id(i)

            date = datetime.datetime.today()
            pallets = pedido["palets_asig"][0]
            line = response['obj']['linea']
            
            #Buscamos el id de la línea asignada
            devices = sql.select_devices()
            idline = int(devices.loc[devices['linea'] == int(line), 'id'])
            incidencias = sql.select_linea_incidencia_by_id(idline)
            events = sql.select_standar_events()

            incidencia_1 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_1']), ['description'])].values[0][0]
            incidencia_2 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_2']), ['description'])].values[0][0]
            incidencia_3 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_3']), ['description'])].values[0][0]
            incidencia_4 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_4']), ['description'])].values[0][0]
            incidencia_5 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_5']), ['description'])].values[0][0]
            incidencia_6 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_6']), ['description'])].values[0][0]
            incidencia_7 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_7']), ['description'])].values[0][0]
            incidencia_8 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_8']), ['description'])].values[0][0]
            incidencia_9 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_9']), ['description'])].values[0][0]          
            
            """ que asigne un orden a las lineas nuevas """
            orden = sql.select_max_orden()
            if orden["orden"][0] is None:
                max_orden = 1
            else: 
                max_orden =int(orden["orden"][0]) + 1
            
            #ver que los campos encajen
            ofid = sql.insert_r('ofs','(of,description,quantity,model,status,originalquantity,okquantity,incidenciatop1,incidenciatop2,incidenciatop3,incidenciatop4,incidenciatop5,incidenciatop6,incidenciatop7,incidenciatop8,incidenciatop9,cicletime,cajas,destrio,linea,creation,id_pedido,linea_id,ruta,cliente,fecha_carga,fecha_produccion,lote_cliente, orden)',\
                (pedido["num_pedido"][0],pedido["descripcion"][0],pallets,pedido["articulo"][0],'new',pallets,"1",incidencia_1,incidencia_2,incidencia_3,incidencia_4,incidencia_5,incidencia_6,incidencia_7,incidencia_8,incidencia_9,"1",pedido["cajas"][0],"0",str(idline),str(date),pedido["id"][0],str(response['obj']['linea']),pedido["ruta"][0],pedido["cliente"][0],str(pedido["fecha_carga"][0]),str(pedido["fecha_produccion"][0]),pedido["lote_cliente"][0], max_orden))
            
            sql.modify('pedidosllanos',"palets_asig",0,str(pedido['id'][0]))

            row = sql.select_of_by_id(ofid[0][0])
            
            #dataframe ordenado para formatear a array de arrays
            res_row = row[['id_pedido', 'id', 'status', 'originalquantity', 'destrio', 'description', 'linea_id', 'quantity']]
            res_row.loc[:, "error"] = 'False'

            res = res.append(res_row)

        except Exception as e:
            print(e)
            res_row = pd.DataFrame(data = ['True',0,0,0,0,0,0,0,0] ,columns = column_names)
            res = res.append(res_row)

    
    res = res.set_index('id')
    #Crear un array de arrays de pedidos
    array_of_arrays = res.to_dict('split')
    
    pedidos = []
    for i in response['obj']['pedidos']:
        pedido = sql.select_pedido_by_id(i).to_dict('split')
        pedidos.append(pedido['data'][0])

    array_of_arrays['pedidos'] = pedidos
    return array_of_arrays

@asignacion.route("/asignacionparcial", methods = ["POST","GET"])
def asignacionparcial():
    column_names = ['error', 'id_pedido', 'id', 'status', 'originalquantity', 'destrio', 'description', 'linea_id', 'quantity']
    res = pd.DataFrame(columns = column_names)
    
    response = request.get_json()
    
    for i in range(len(response['partialAsign'])): #me falta el id de pedido en cada objeto
        try:
            #Comparamos los pallets antiguos con los nuevos y modificamos el pedido
            pedido = sql.select_pedido_by_id(response['partialAsign'][i]['idpedido'])

            date = datetime.datetime.today()
            pallets = response['partialAsign'][i]['cant']
            line = response['partialAsign'][i]['lane']
            
            #Buscamos el id de la línea asignada
            devices = sql.select_devices()
            idline = int(devices.loc[devices['linea'] == int
            (line), 'id'])
            incidencias = sql.select_linea_incidencia_by_id(idline)
            events = sql.select_standar_events()

            incidencia_1 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_1']), ['description'])].values[0][0]
            incidencia_2 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_2']), ['description'])].values[0][0]
            incidencia_3 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_3']), ['description'])].values[0][0]
            incidencia_4 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_4']), ['description'])].values[0][0]
            incidencia_5 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_5']), ['description'])].values[0][0]
            incidencia_6 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_6']), ['description'])].values[0][0]
            incidencia_7 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_7']), ['description'])].values[0][0]
            incidencia_8 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_8']), ['description'])].values[0][0]
            incidencia_9 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_9']), ['description'])].values[0][0]          

            #ver que los campos encajen
            """ que asigne un orden a las lineas nuevas """
            orden = sql.select_max_orden()
            max_orden =int(orden["orden"][0]) + 1
            ofid = sql.insert_r('ofs','(of,description,quantity,model,status,originalquantity,okquantity,incidenciatop1,incidenciatop2,incidenciatop3,incidenciatop4,incidenciatop5,incidenciatop6,incidenciatop7,incidenciatop8,incidenciatop9,cicletime,cajas,destrio,linea,creation,id_pedido,linea_id,ruta,cliente,fecha_carga,fecha_produccion,lote_cliente, orden)',\
                (pedido["num_pedido"][0],pedido["descripcion"][0],pallets,pedido["articulo"][0],'new',pallets,"1",incidencia_1,incidencia_2,incidencia_3,incidencia_4,incidencia_5,incidencia_6,incidencia_7,incidencia_8,incidencia_9,"1",pedido["cajas"][0],"0",str(idline),str(date),pedido["id"][0],line,pedido["ruta"][0],pedido["cliente"][0],str(pedido["fecha_carga"][0]),str(pedido["fecha_produccion"][0]),pedido["lote_cliente"][0], max_orden))
            
            new_pallets = int(pedido["palets_asig"][0]) - int(pallets)
            sql.modify('pedidosllanos',"palets_asig",new_pallets,str(pedido['id'][0]))

            row = sql.select_of_by_id(ofid[0][0])

             #dataframe ordenado para formatear a array de arrays
            res_row = row[['id_pedido', 'id', 'status', 'originalquantity', 'destrio', 'description', 'linea_id', 'quantity']]
            res_row.loc[:, "error"] = 'False'

            res = res.append(res_row)
        
        except:
            res_row = pd.DataFrame(data = [['True',0,0,0,0,0,0,0,0]] ,columns = column_names)
            res = res.append(res_row)

    res = res.set_index('id')
    #Crear un array de arrays de pedidos
    array_of_arrays = res.to_dict('split')
    
    pedidos = []
    for i in range(len(response['partialAsign'])):
        pedido = sql.select_pedido_by_id(response['partialAsign'][i]['idpedido']).to_dict('split')
        pedidos.append(pedido['data'][0])

    array_of_arrays['pedidos'] = pedidos
    return array_of_arrays

@asignacion.route("/editAsignacion", methods = ["POST","GET"])
def editAsignacion():
    column_names = ['error', 'id_pedido', 'id', 'status', 'originalquantity', 'destrio', 'description', 'linea_id', 'quantity']
    res = pd.DataFrame(columns = column_names)
    #si of es new no se modifica
    response = request.get_json()

    if sql.select_of_by_id(response['obj']['idOF']).status[0] == 'new' or sql.select_of_by_id(response['obj']['idOF']).status[0] == 'open':
        try:   
            #idpedido = response['obj']['id']
            line = response['obj']['linea']
            idOf = response['obj']['idOF']
            pallets_asignados = response['obj']['asignados']
            pallets_originales = response['obj']['originales']

            #Buscamos el id de la línea asignada
            devices = sql.select_devices()
            idline = int(devices.loc[devices['linea'] == int(line), 'id'])
            incidencias = sql.select_linea_incidencia_by_id(idline)
            events = sql.select_standar_events()

            #se actualizan las incidencias en función de la línea
            incidencia_1 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_1']), ['description'])].values[0][0]
            sql.modify('ofs',"incidenciatop1",incidencia_1,idOf)
            incidencia_2 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_2']), ['description'])].values[0][0]
            sql.modify('ofs',"incidenciatop2",incidencia_2,idOf)
            incidencia_3 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_3']), ['description'])].values[0][0]
            sql.modify('ofs',"incidenciatop3",incidencia_3,idOf)
            incidencia_4 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_4']), ['description'])].values[0][0]
            sql.modify('ofs',"incidenciatop4",incidencia_4,idOf)
            incidencia_5 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_5']), ['description'])].values[0][0]
            sql.modify('ofs',"incidenciatop5",incidencia_5,idOf)
            incidencia_6 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_6']), ['description'])].values[0][0]
            sql.modify('ofs',"incidenciatop6",incidencia_6,idOf)
            incidencia_7 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_7']), ['description'])].values[0][0]
            sql.modify('ofs',"incidenciatop7",incidencia_7,idOf)
            incidencia_8 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_8']), ['description'])].values[0][0]
            sql.modify('ofs',"incidenciatop8",incidencia_8,idOf)
            incidencia_9 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_9']), ['description'])].values[0][0]
            sql.modify('ofs',"incidenciatop9",incidencia_9,idOf)

            #modificamos los valores que nos vienen de la llamada
            sql.modify('ofs',"linea_id",line,idOf)
            sql.modify('ofs',"linea",idline,idOf)
            sql.modify('ofs',"originalquantity",pallets_asignados,idOf)
            sql.modify('ofs',"quantity",pallets_asignados,idOf)

            row = sql.select_of_by_id(idOf)

            #modificacmos el pedido
            pedido = sql.select_pedido_by_id(row['id_pedido'][0])

            palets_modificados =  int(pallets_originales) - int(pallets_asignados)

            mod_pallets = pedido['palets_asig'][0] + palets_modificados
            sql.modify('pedidosllanos',"palets_asig",mod_pallets,row['id_pedido'][0])

            #dataframe ordenado para formatear a array de arrays
            res_row = row[['id_pedido', 'id', 'status', 'originalquantity', 'destrio', 'description', 'linea_id', 'quantity']]
            #res_row['error'] = 'False'
            res_row.loc[:, "error"] = 'False'
            
        except:
            #dataframe ordenado para formatear a array de arrays
            res_row = pd.DataFrame(data = [['True',0,0,0,0,0,0,0,0]] ,columns = column_names)

    else:
        idOf = response['obj']['idOF']
        row = sql.select_of_by_id(idOf)
        res_row = pd.DataFrame(data = [['True','La OF ha sido usada',0,0,0,0,0,0,0]] ,columns = column_names)

    res = res.append(res_row)
    res = res.set_index('id')
    array_of_arrays = res.to_dict('split')

    pedido = sql.select_pedido_by_id(row['id_pedido'][0]).to_dict('split')
    array_of_arrays['pedidos'] = pedido['data'][0]

    return array_of_arrays

@asignacion.route("/deleteAsignacion", methods = ["POST","GET"])
def deleteAsignacion():
    response = request.get_json()
    if sql.select_of_by_id(response['idOF']).status[0] != 'running':
        try:
            
            ofid = response['idOF']
            of = sql.select_of_by_id(ofid)

            pallets_terminados = of['originalquantity'][0] - of['quantity'][0]
            pallets_restantes = of['originalquantity'][0] - pallets_terminados
            idpedido =  of['id_pedido'][0]

            pedido = sql.select_pedido_by_id(idpedido)

            pallets_pedido = int(pedido['palets_asig'][0]) + int(pallets_restantes)

            sql.modify('pedidosllanos',"palets_asig",pallets_pedido,idpedido)
            sql.modify('pedidosllanos',"palets_completos",pallets_terminados,idpedido)

            sql.delete("ofs", ofid)
            
            res_row = pd.DataFrame(data = [['False',0]] ,columns = ['error','text'])
            
        except:
            res_row = pd.DataFrame(data = [['True',0]] ,columns = ['error','text'])
    
    else:
        idpedido = sql.select_of_by_id(response['idOF']).id_pedido[0]
        res_row = pd.DataFrame(data = [['True','La OF está siendo usada y no puede borrarse']] ,columns = ['error','text'])

    array_of_arrays = res_row.to_dict('split')

    pedido = sql.select_pedido_by_id(idpedido).to_dict('split')
    array_of_arrays['pedidos'] = pedido['data'][0]

    return array_of_arrays

@asignacion.route("/refresh", methods =["POST"])
def refresh():    
    Actualizar_pedidos.IniProcess()
    res_row = pd.DataFrame(data = [['True',0]] ,columns = ['error','text'])
    array_of_arrays = res_row.to_dict('split')

    return array_of_arrays

@asignacion.route('/getLinea', methods=['GET'])
def getLinea():
    ip = "'"+str(request.remote_addr)+"'"
    result = sql.select('linea', 'devices', 'ip', ip,"dataframe")
    linea = str(result['linea'][0])
    print('linea'+linea)
    return linea

if __name__ == '__main__':    
    sql = PostgreeConnDB("BonnysaDB")    
    
