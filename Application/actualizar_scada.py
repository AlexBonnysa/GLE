from datetime import datetime
from BonnysaDBConn import Postgres_Main_Database
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
from SqlServerConnDB import SqlServerConnDB
import psycopg2
import time
import sys
import logging
import pandas as pd
from PostgreeConnDB import PostgreeConnDB
from Lisapp import recolectarDatosScadaFuncion, insertDataKpiPerMinuteSql
from LogData import LogData

def getActualTurn(hora):    
    return db.selectTurnoActualFecha(hora, "tuple")

def dataInsertPostgreTable(of, turno, id, fecha, maquinaid, peso, paquetes):
    db.insert("scada_valores","(scada_id,scada_fecha,scada_id_maquina,scada_peso,scada_cantidad,ofid,turnoid)", "({},'{}', '{}', {}, {}, {}, {})".format(id, fecha, maquinaid, peso, paquetes, of, turno))

def getOfAndTurnByScadaId(dfScada):    
    for index, row in dfScada.iterrows():
        if row["maquinaid"] !="":
            df = db.selectOfByMaquinaId(row["maquinaid"], row["fecha"])
            if df is None or len(df)==0:
                of = db.selectOfByMaquinaWorkId(row["maquinaid"], row["fecha"])
                if of is None or len(of)==0:
                    of = "Null"
                else:
                    of = of.ofid[0]
            else: 
                of = df.of[0]
            turno = extracHourFromDataframe(row["fecha"])            
            dataInsertPostgreTable(of, turno[0][1], row["id"], row["fecha"], row["maquinaid"], (round(row["peso"], 4)), row["paquetes"] )

def insertKpiRequest():
    activeOf = db.selectData("activeof","dataframe", "*")
    now = datetime.now()
    hora = now.strftime("%H:%M:%S")
    turnoActual = getActualTurn(hora)
    for index, row in activeOf.iterrows():         
        dic = recolectarDatosScadaFuncion(row["ofid"])
        insertDataKpiPerMinuteSql(dic,row["ofid"], turnoActual[0][1], now)   
   
def extracHourFromDataframe(datetime):
    fecha =pd.Timestamp(datetime)
    fecha = fecha.to_pydatetime(fecha).strftime("%H:%M:%S")   
    return getActualTurn(fecha)


def getValuesFromScada(id):
    df = dbSql.selecMaxData("dataframe", id)    
    return df


def updateScadaProcess():    
    df = db.selectData("scada_valores","dataframe", "MAX(scada_id) as ultimo")      
    if (len(df)>0 and df.ultimo[0]>=0 and df.ultimo[0] is not None):        
        df2=getValuesFromScada(df.ultimo[0]) 
        getOfAndTurnByScadaId(df2)

def procesoInicial():     
    df2=getValuesFromScada(684292) 
    getOfAndTurnByScadaId(df2)

if __name__ == "__main__":
    now = datetime.now()
    fechaHora = now.strftime("%Y_%m_%d") 
    db = PostgreeConnDB("BonnysaDB")
    dbSql = SqlServerConnDB("scada")        
    logging.basicConfig(filename='updateScada_'+fechaHora+".log", level=logging.DEBUG, format='%(asctime)s;%(levelname)s;%(message)s', datefmt='%m/%d/%Y %I:%M:%S')
    logging.info('INICIO PROCESO ACTUALIZAR SCADA')    
    updateScadaProcess()
    logging.info('FIN PROCESO ACTUALIZAR KPI')    
    logging.info('INICIO PROCESO ACTUALIZAR KPI')
    insertKpiRequest() 
    logging.info('FIN PROCESO ACTUALIZAR KPI')
