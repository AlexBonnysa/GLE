from abc import ABC, abstractmethod
import psycopg2
import pandas as pd
from numpy import array
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from config.loadData import readJson
from LogData import LogData

class ConnDb(ABC):

    
    def __init__(self, variable, data = readJson()):
        self._server = data[variable]["host"]
        self._database =  data[variable]["dbname"]
        self._username = data[variable]["username"] 
        self._password = data[variable]["password"]
        self._port = int(data[variable]["port"])
        self._verbose = int(data["verbose"]["level"])
        self._conn = ""
        self._rowcount = 0 
        self._log = LogData()    
        self._log.loadCostum("mylog")  
        self._select= ""
        self._table = ""  
        pass
    @property   
    def verbose(self):
        return self._verbose
    @property
    def server(self):
        return self._server
    @property
    def log(self):
        return self._log
    @property
    def database(self):
        return self._database
    @property
    def username(self):
        return self._username
    @property
    def password(self):
        return self._password
    @property
    def port(self):
        return self._port
    @property
    def conn(self):
        return self._conn
    @property
    def rowcount(self):
        return self._rowcount
    @conn.setter
    def conn(self, value):
        self._conn = value
    @rowcount.setter
    def rowcount(self, value):
        self._rowcount = value


    def select(self,*args):
        argsJoin = ",".join(args)
        self._select = "Select {}".format(argsJoin)        
    def table(self, tableName):
        self._table = "from {}".format(tableName)
    def whereNormal(self):
        print("sin extender")
    def whereIn(self):
        print ("sin extender")            
    def prepareQuery(self, type):        
        query = "{} {}".format(self._select, self.table)
        return self.getData(query, type)       
    @abstractmethod
    def connectDB(self):
        pass
    @abstractmethod
    def insertDB(self, query):
        pass
    def commitData(self):
        try:
            self.conn.commit()
        except (Exception) as e:
            self.log.logRegister("error","Error a la hora de hacer el commit: "+str(e))  
        
    def closeDb(self):
        try:
            self._conn.close()
            self.log.removeHandler()                  
        except Exception as e:
            self.log.logRegister("error", "Error cerrando la base de datos:"+str(e))
            print("Error cerrando base de datos "+str(e))
    def eval(self, df, type):
        if type == "dataframe":
            return df
        if type == "tuple":
            records = df.to_records(index=False)
            tup = list(records)
            return tup

    def getData2(self, query,type):
        try:
            cur = self.conn.cursor()
            cur.execute(query)
            columns = [column[0] for column in cur.description]
            results = []
            for row in cur.fetchall():
                results.append(dict(zip(columns, row)))
            df =pd.DataFrame(results)
            cur.close()
            self.closeDb()
            
        except Exception as e:
            print("ERROR SENTENCIA SQL: "+e)
        return df
            
       
    def getData(self, query,type):
        df = None
        try: 
            df = pd.read_sql(query, self.conn)
            df = self.eval(df,type)
            self.closeDb()            
        except (UnboundLocalError,Exception,pd.io.sql.DatabaseError) as e:
            self.closeDb()
            self.log.setSql("query")   
            self.log.logRegister("error","Error a la hora de traerse la informacion: "+str(e)) 
            
        
        return df
    def selectData(self, tabla , type, *args, **kwargs):
        argsjoin = ",".join(args)
        query = "SELECT {} FROM {}".format(argsjoin, tabla)
        i = 0
        for key, value in kwargs.items():
            if i == 0:
                query += " WHERE "
            else:
                query += " AND "
            query += "{}='{}'".format(key, value)
            i += 1
        query += ";"
        return self.getData(query, type)


    
    