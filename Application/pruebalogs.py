from LogData import LogData
import pandas as pd
import traceback
    
import psycopg2
# import the error handling libraries for psycopg2
from psycopg2 import OperationalError, errorcodes, errors
"""
log = LogData()    
log.loadCostum("mylog")
log.logRegister("aviso", "prueba")
log.logRegister("error", "prueba")
log.logRegister("critico", "prueba")
log.logRegister("debug", "prueba")
"""
dict = {
    "separator": "",
    "name": "pablo"
    
}
dict2 = {
    "separator": "AND",
    "name": "javier"
}
dict3 = {
    "separator": "OR",
    "name": "javier"
}
dict4 = {
    "separator": "AND",
    "name": "javier"
}
datos = [dict, dict2, dict3, dict4]
#datos.append(dict)
#datos.append(dict2)
sql = ""
dict_names = {'key1': 'Text 1', 'key2': 'Text 2'}
dict_values = {'key1': 0, 'key2': 1} 

df = pd.DataFrame(datos)

for index, row in df.iterrows():
    sql += row["separator"]
    if (row["separator"]=="OR"):
        sql += "("
    sql += " {}={} ".format(df.columns[1], row[1])

InFailedSqlTransaction = errors.lookup('25P02')
try:
    conn = psycopg2.connect("host=localhost dbname=BonnysaDB user=postgres password=postgres")
    query = "select * from ofs"
    df = pd.read_sql(query,conn)
    print(df)

except (Exception,pd.io.sql.DatabaseError) as e:    
    print("sin conexion", str(e))
    
    
else:
   print('Connected!')
   # do stuff
