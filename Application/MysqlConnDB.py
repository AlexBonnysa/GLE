import MySQLdb
import pandas as pd
from ConnDb import ConnDb
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from config.loadData import readJson




class MysqlConnDB(ConnDb):

    def __init__(self, variable):       
        super(MysqlConnDB, self).__init__(variable)               
        #self.connectDB()
    
    
    
    def connectDB(self):
        try: 
            self.conn = MySQLdb.connect(host=super().server,port=super().port,user=super().username,passwd=super().password,db=super().database)            
        except Exception as err:
            print("Error en la conexion a la base de datos: {}".format(err))
            super().log.logRegister("error", str(err))
            
    def insertDB(self, query):
        try:
            mycursor = self.conn.cursor()
            mycursor.execute(query)
            super().commitData()
            super().closeDb()
        except (Exception) as e:
            self.log.logRegister("error",str(e))
        else:
            super().rowcount  = mycursor.rowcount    
   


#db = MysqlConnDB("Comer")
#query = db.selectData("frf_productos", "dataframe", "id", "descripcion_p", id =4 )
#query = db.insertDB("insert into frf_vias (descripcion_v) values ('hola holita')")
#print("datos: "+str(query))
                   

        