from datetime import datetime
from BonnysaDBConn import Postgres_Main_Database
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
import psycopg2
import time
import logging
import sys




def comprobamosTurnosDiayHoraActual(fecha, hora):
    return db.seleccionarTurnosActuales(fecha, hora, "dataframe" )

def comprobamosTurnosActiveOperatos(row, fechaHora):   
    resultado = db.seleccionarTurnosActivos(row["operator_id"], row["id"], "tuple")    
    if (len(resultado)==0 or row["operator_id"] == 999999999):
        logging.info('Operarios en tablas fichajes no encontrados en tabla active operator') 
        db.insertarTurnosActivos(row["id"],row["operator_id"], row["codigo"], row["name"], row["nombreoperado"], fechaHora, 1 )
        db.insertarHistoricoTurnos(row["fichadoid"], fechaHora, 15)
        db.insert('loginout','(idoperario,idip,idevento,date)',(row["operator_id"], row["id"] ,'15',str(now)))
    else:        
        if(resultado[0][0]!=row["id"] and row["operator_id"] != 999999999 ):            
            numero =db.actualizarTurnosActivos(row["id"], row["name"], resultado[0][1],1)
            if (numero > 0):
                logging.info('Se ha actualizado la linea : '+str(resultado[0][0])+' a '+""+str(row["id"])+"para el operador: "+ row["nombreoperado"]) 
                db.insertarHistoricoTurnos(row["fichadoid"], fechaHora, 173)           
            logging.info('Actualizacion linea por cambio') 
        else:
            logging.info('Tiene la misma linea. No hacemos nada')     
    
def comenzarProcesoInicio():
    try:
        now = datetime.now()   
        fecha = now.strftime("%Y-%m-%d")
        hora = now.strftime("%H:%M:%S")
        fechaHora = fecha +" "+hora    
        df =comprobamosTurnosDiayHoraActual(fecha, hora)
        logging.info('Numero de Operarios en tabla fichajes: '+str(len(df.index)))                 
        for index, row in df.iterrows():        
            comprobamosTurnosActiveOperatos(row, fechaHora )
    except:
        e = sys.exc_info()[0]
        print(sys.exc_info())
        logging.error('Ha habido un problema con error'+str(e))



def ClosePartial(id):
    result = db.select('*', 'activeof', 'id', id,"dataframe")    
    idvalue = str(result.iloc[0][2])
    quantity = result.iloc[0][3]    
    cajas = str(result.iloc[0][7])
    destrio = str(result.iloc[0][8])   

    pedidoid = db.select('id_pedido', 'ofs', 'id', idvalue,"dataframe")
    palets_completos = db.select('palets_completos', 'pedidosllanos', 'id', str(pedidoid.iloc[0][0]),"dataframe")
    palets_origen = db.select('quantity', 'ofs', 'id', idvalue,"dataframe")
    resquantity = int(palets_completos.iloc[0][0])+int(palets_origen.iloc[0][0])-int(quantity)
    db.modify("pedidosllanos","palets_completos",str(resquantity),str(pedidoid.iloc[0][0]))

    db.modify("ofs","quantity",quantity,idvalue)
    db.modify("ofs","cajas",cajas,idvalue)
    db.modify("ofs","destrio",destrio,idvalue)
    db.modify("ofs","status","open",idvalue)    
    db.delete("activeof",id)




def DatesPartialClose(resultActiveOf, turno):
    ClosePartial(resultActiveOf.id[0])
    now = datetime.now()    
    standarEvent= db.select('*', "standarevents", "type_desc", "'finparcialof'","dataframe")
    ofDatos = db.select('*', "ofs", "id", resultActiveOf.ofid[0], "dataframe" )
    lineDevice = db.select('linea', "devices", "id" , resultActiveOf.deviceid[0] , "tuple")
    valueLastId =db.insertLastId("work_diary", "(deviceid, event, description, date, number, ofid, type, of, turnos_id )",
         "({}, '{}', '{}', '{}', {}, {}, '{}', '{}', {})".format(resultActiveOf.deviceid[0],standarEvent.id[0], standarEvent.description[0] , now, 1, resultActiveOf.ofid[0], "FP",
           resultActiveOf.of[0], turno[0][1]))
    dfDatos = db.selectWorkDiaryLast("work_diary", "dataframe", "date", ofid = resultActiveOf.ofid[0])
    db.modify("work_diary", "date_start", dfDatos.date[0], valueLastId)
    if resultActiveOf.deviceid[0] in [17,10,27,18,19,26]:       
        db2.insert("work_diary_extend", "(id, deviceid, event, description, date, number, ofid, type, of, turno, atalantago )",
         "({}, {}, '{}', '{}', '{}', {}, {}, '{}', '{}', '{}', '{}')".format(valueLastId, resultActiveOf.deviceid[0],standarEvent.id[0], standarEvent.description[0] , now, 1, resultActiveOf.ofid[0], "FP",
           resultActiveOf.of[0], turno[0][0].capitalize(), now))       
    db.insert('"OF_Pesadas_Operarios"', '(id_work_diary, id_pedido, id_linea_produccion, id_devices, "OF", "Descripcion_OF", "Articulo", "Fecha_accion", "Tipo_accion", "Descripcion_accion",\
    "Tiempo_asociado_accion", "Tipo_incidencia", "Peso_neto_mettler", "Cumple_peso", id_operarios, "NIF", "Nombre", "Turno", ofid, nif_index)',
     "({}, {}, {}, {}, '{}', '{}', '{}', '{}', '{}', '{}', {}, '{}', {}, {}, {} , {}, {}, '{}', {}, {} )".format(valueLastId, ofDatos.id_pedido[0], lineDevice[0][0], 
    resultActiveOf.deviceid[0], resultActiveOf.of[0], ofDatos.description[0], ofDatos.model[0], now, standarEvent.id[0], standarEvent.description[0], 2,"FP", "NULL",'NULL','NULL','NULL', 'NULL', turno[0][0].capitalize(),resultActiveOf.ofid[0], 'NULL' ))
    print("el resto de lineas")        


   
def comprobarTurnosEnFechaOperador(row, fecha, hora, fechaHora):
    resultado =db.seleccionarTurnosporOperarioActivo(row["operarioid"], fecha, hora,  "tuple")
    borramos =0    
    if (len(resultado)!=0):
        borramos = db.borrarOperariosActivo(row["id"])         
        db.insertarHistoricoTurnos(resultado[0][0], fechaHora, 16)
        last_oper = db.select('*',"activeoperator","deviceid", row["activeoperator"], "tuple")
        if(len(last_oper )==0):
            print("metodo sin implementar")
            #insertamosDatosparaCierreParcial(row, resultado[1][0] )
    return borramos
    


def comenzarProcesoFin():
    try:
        now = datetime.now()   
        fecha = now.strftime("%Y-%m-%d")
        hora = now.strftime("%H:%M:%S")
        fechaHora = fecha +" "+hora
        operario = db.seleccionarOperariosActivos("dataframe")
        logging.info('Numero de Operarios en tabla Operario Activo: '+str(len(operario.index)))  
        numero = 0 
        for index, row in operario.iterrows():        
            numero = numero +comprobarTurnosEnFechaOperador(row, fecha, hora, fechaHora )
        logging.info("Hemos borrado : "+str(numero)) 
    except:
        e = sys.exc_info()[0]
        logging.error('Ha habido un problema con error'+str(e))

def checkUsersLogOut(line, fechaHora):
    userByLine = None
    userByLine= db.select("*", "activeoperator", "deviceid", line, "dataframe")
    if(len(userByLine)>0):
        for index, row in userByLine.iterrows(): 
            borramos = db.borrarOperariosActivo(row["id"])
            db.insert('loginout','(idoperario,idip,idevento,date,login)',(row["operarioid"],line,'16',fechaHora, str(row["atalantago"])))
            db.insertarHistoricoTurnos('NULL', fechaHora, 16)   

def checkLogOut():
    now = datetime.now()   
    fecha = now.strftime("%Y-%m-%d")
    hora = now.strftime("%H:%M:%S")
    fechaHora = fecha +" "+hora     
    linesList = [7,12,11,20,22, 25,26,19,18,14,13,2,1,16,27,10,17,15]
    turno = db.selectTurnoActual(hora, "tuple")         
    for x in linesList:        
        activeOf=db.select("*", "activeof", "deviceid", x, "dataframe")     
        checkUsersLogOut(x, fechaHora)           
        for index, row in activeOf.iterrows():                      
            if (len(activeOf)>0):                
                DatesPartialClose(activeOf, turno)


if __name__ == "__main__":
    now = datetime.now()
    fechaHora = now.strftime("%Y_%m_%d") 
    db = Postgres_Main_Database("BonnysaDB")
    db2 = Postgres_Main_Database("lake")    
    
    logging.basicConfig(filename='fichado_'+fechaHora+".log", level=logging.DEBUG, format='%(asctime)s;%(levelname)s;%(message)s', datefmt='%m/%d/%Y %I:%M:%S')
    logging.info('INICIO FICHADO LOG OUT')    
    checkLogOut()   
    logging.info('FIN FICHADO LOG OUT')
           

    