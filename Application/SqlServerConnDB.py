
import pyodbc
# import the error handling libraries for psycopg2
import pandas as pd
from ConnDb import ConnDb
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from config.loadData import readJson
from LogData import LogData
from PostgreeConnDB import PostgreeConnDB
import time
from datetime import date, datetime
from MysqlConnDB import MysqlConnDB



class SqlServerConnDB(ConnDb):

    def __init__(self, variable):       
        super(SqlServerConnDB, self).__init__(variable)
        #self.pruebaDB()        
        #self.connectDB()  
  
    
    def connectDB(self):
        try:                       
            self.conn =pyodbc.connect("DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={0}; database={1}; \
       trusted_connection=no;UID={2};PWD={3}".format(super().server,super().database,super().username,super().password))            
                       
        except Exception as e:
            print("error al conectar a la base de dato con esta cadena",str(e))
            super().log.logRegister("error al conectar a la base de dato con esta cadena",str(e))
            quit()
        else:
            pass

    def insertDB(self, query):
        try:
            self.connectDB()            
            mycursor = self.conn.cursor()
            mycursor.execute(query)                      
            super().commitData()            
            self.rowcount =mycursor.rowcount
            mycursor.close()   
            super().closeDb()                                                        
        except (Exception) as e:            
            self.log.logRegister("error","Error a la hora de insertar o actualizar o borrar un valor: "+str(e))
            self.log.logRegister("aviso", query)             
            
    def selectScadaDateValues(self, fechaIni, idScada):
        query = """
            select SUM(ValorVelocidad) AS paquetes, SUM(ValorOEE) AS peso, SUM(ValorOEE) / SUM(ValorVelocidad) AS pesomedio
            FROM  ValoresProduccion where FORMAT (Fecha, 'yyyy-MM-dd HH:mm:ss') >= '{}'  
			and MaquinaID = '{}'
        """.format(fechaIni,idScada )
       
        
        return self.selectGlobal(query, "dataframe", "kpi")

    def selectScadaDateValuesSum(self, fechaIni, fechaFin, idScada):
        query = """
            select SUM(ValorVelocidad) AS paquetes, SUM(ValorOEE) AS peso, SUM(ValorOEE) / SUM(ValorVelocidad) AS pesomedio
            FROM  ValoresProduccion where (FORMAT (Fecha, 'yyyy-MM-dd HH:mm:ss') >= '{}' and FORMAT(Fecha, 'yyyy-MM-dd HH:mm:ss') <= '{}') 			           
            and MaquinaID = '{}'
        """.format(fechaIni,fechaFin, idScada )        
        
        return self.selectGlobal(query, "dataframe", "kpi")   
    
    def selectData(self, tabla, type, *args, **kwargs):
        self.connectDB()
        df =  super().selectData(tabla, type, *args, **kwargs)        
        return df

    def selecMaxData(self, type, id):
        query = """
            select id, ValorVelocidad AS paquetes, ValorOEE AS peso, FORMAT (Fecha, 'yyyy-MM-dd HH:mm:ss') as fecha, MaquinaID as maquinaid 
            FROM  ValoresProduccion where id > '{}'
        """.format(id)        
        
        return self.selectGlobal(query, "dataframe", "kpi") 
             

    def selectGlobal(self, query, type, tipo="Ninguno"):
        if(self.verbose==2):
            if(tipo=="kpi"):
                self.log.setSql(query)   
                self.log.logRegister("aviso","SENTENCIA SQL KPI")
        self.connectDB()
        df = super().getData(query, type)        
        return df
    

  




                   

        