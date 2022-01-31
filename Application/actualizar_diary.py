from datetime import datetime
from BonnysaDBConn import Postgres_Main_Database
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
import psycopg2
import time
import logging
import sys    
    
now = datetime.now()
fechaHora = now.strftime("%Y_%m_%d") 
db = Postgres_Main_Database("BonnysaDB")

df = db.selectData("work_diary", "dataframe", "id", "to_char( date, 'HH24:MI:SS') as hora")
    
for index, row in df.iterrows():
    datos =  db.selectTurnoActual(row["hora"], "tuple")
    if len(datos)>0:
        db.modify("work_diary","turnos_id", datos[0][1], row["id"])