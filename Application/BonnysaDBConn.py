import pandas as pd
import psycopg2
import json
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from config.loadData import readJson




class Postgres_Main_Database:
    """PostgreSQL Database class. For the LISApp"""
   

    def __init__(self,  variable, datos = readJson()):        

        data = datos
        self.host = data[variable]["host"]
        self.username = data[variable]["username"]
        self.password = data[variable]["password"]
        self.port = data[variable]["port"]
        self.dbname = data[variable]["dbname"]
        self.conn = psycopg2.connect(host=self.host,port=self.port,user=self.username,password=self.password,dbname=self.dbname)
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    
    def write(self,query):
        self.cursor.execute(query)   
        #self.cursor.close()

    def read(self,query, type):
        self.cursor.execute(query) 

        records = [row for row in self.cursor.fetchall()]
        
        if not records:
            values =  [0] * len([ x.name for x in self.cursor.description ])
            heads = [ x.name for x in self.cursor.description ]
            dictionary = dict(zip(heads, values))

            df =pd.DataFrame.from_dict(dictionary, orient='index')
            df = df.T

        else:
            df = pd.DataFrame(records)
            df.columns=[ x.name for x in self.cursor.description ]
        
        #self.cursor.close()

        records = df.to_records(index=False)
            #print(records)
        tup = list(records)

        if type == "dataframe":
            return df
        if type == "tuple":
            return tup

    def eval(self, df, type):
        #if df.empty:
            #df =  pd.DataFrame({0 : [0]})
            #tup = []

        if type == "dataframe":
            return df
        if type == "tuple":
            records = df.to_records(index=False)
            tup = list(records)
            return tup


    def select(self, sele, tablename, var, value, type):
        query = """
                SELECT {}
                FROM public.{}
                WHERE {} = {};
                """.format(sele, tablename, var, value)        
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

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
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def selectWorkDiaryLast(self, tabla , type, *args, **kwargs):
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
        query += "and event in (19,17)"
        query+= "order by id desc limit 1"
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)  

    def selectall(self, sele, tablename, type):
        query = """
                SELECT {}
                FROM public.{};
                """.format(sele, tablename)
              
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def selectAofsById(self, id, type):
        query = """
                SELECT p.estado
                FROM public.pedidosllanos p inner join public.ofs o ON o.id_pedido = p.id
                WHERE o.of = '{}';
                """.format(id)       
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def selectAOfs(self, sele, tablename, var, value, type):
        query = """
                SELECT {}, (select estado from public.pedidosllanos p inner join public.ofs o ON o.id_pedido = p.id where o.id = a.ofid ) as estado,
                (select producto from public.pedidosllanos p inner join public.ofs o ON o.id_pedido = p.id where o.id = a.ofid ) as producto
                FROM public.{} a               
                WHERE {} = {} 
                """.format(sele, tablename, var, value)
        
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def selectOfsFin(self, sele, tablename, var, value, type):
        query = """
                SELECT {}
                FROM public.{} o inner join pedidosllanos p ON o.id_pedido = p.id             
                WHERE o.{} = {} and p.estado IN ('1', '5');
                """.format(sele, tablename, var, value)
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)  

    def selectPersonalizado(self, tablename, tuplaSelect, tuplaWhere, tuplaOrder, type):

        query ="""
               SELECT {}
               FROM public.{}
                """.format(tuplaSelect, tablename)
        if (len(tuplaWhere)>0):
            query ="""
            """.format(tuplaWhere)
        if (len(tuplaOrder)>0):
            query ="""
            """.format(tuplaWhere)
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)
    
    def selectActiveOfEvent(self, sele, tablename, where1, value1, type):

        query ="""
               SELECT {}
               FROM public.{}
               WHERE {} in {}
               order by {} asc
                """.format(sele, tablename, where1, value1, where1)
        
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def selectall(self, sele, tablename, type):
        query = """
                SELECT {}
                FROM public.{};
                """.format(sele, tablename)
              
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)


    def select2(self, sele, tablename, var, value, var2, value2, var3, value3,type ):
        query = """
                SELECT {}
                FROM public.{}
                WHERE {} = {}
                and {} = {}
                or {} = {}
                and creation > current_date - interval '15' day;
                """.format(sele, tablename, var, value, var2, value2, var3, value3)
              
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def selectOfsGeneral(self, sele, tablename, var, value, type):
        query = """
                SELECT o.{}, p.estado
                FROM public.{} o inner join pedidosllanos p ON o.id_pedido = p.id
                WHERE {} = {};
                """.format(sele, tablename, var, value)

        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def selectOfs(self, sele, tablename, var, value, var2, value2, var3, value3,type ):
        query = """
                SELECT o.{}, producto
                FROM public.{} o inner join pedidosllanos p ON o.id_pedido = p.id
                WHERE {} = {}
                and p.estado IN ('1', '5')
                and ({} = {}
                or {} = {})
                and creation > current_date - interval '15' day order by orden;                
                """.format(sele, tablename, var, value, var2, value2, var3, value3)          
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)
   
    def selectnorunning(self, sele, tablename, var, value, type):
        query ="""
                SELECT {}
                FROM public.{}
                WHERE {} = {}
                AND status != 'running';
                """.format(sele, tablename, var, value)
              
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)
    
    def select_filter(self, sele, tablename,type):
        query = """
                SELECT {}
                FROM public.{}
                ORDER BY id DESC LIMIT 300;
                
                """.format(sele, tablename)
              
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def selectOperator(self, sele, tablename, fecha, turno, nombre, type):
        query = """
                SELECT {}
                FROM public.{}
                WHERE fecha = '{}'
                and nombre = '{}'
                and turno_id = {}              
                """.format(sele, tablename, fecha, nombre, turno)
              
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def selectTurnoActual(self, hora, type):
        query = """
                    select tipo, id from turnos where   (case when hora_fin<hora_ini then to_timestamp(concat(to_char(  current_date + INTERVAL '1 day', 'YYYY/MM/DD'),' ', '{}'  ), 'YYYY/MM/DD HH24:MI:SS') > 
                    to_timestamp(concat(to_char(current_date , 'YYYY/MM/DD'),' ', hora_ini  ), 'YYYY/MM/DD HH24:MI:SS') and to_timestamp(concat(to_char(  current_date, 'YYYY/MM/DD'),' ', '{}'  ), 'YYYY/MM/DD HH24:MI:SS') <=to_timestamp(concat(to_char(  current_date + INTERVAL '1 day', 'YYYY/MM/DD'),' ', hora_fin  ), 'YYYY/MM/DD HH24:MI:SS')  else '{}' >hora_ini and '{}' <=hora_fin  end)  
                    """.format(hora, hora, hora, hora)                
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def borrarDatosturno(self, fecha, turno):
        query = """
                delete from public.fichajes where fecha = '{}' and turno_id = {}; 
                """.format(fecha, turno)
        self.cursor.execute(query)
        self.conn.commit()

    def insertarDatosturno(self, jsonString):
        insertar = jsonString
        values =""
        for i in range(len(insertar)):
            linea = int(insertar[i]["linea"])
            if (linea==13 or linea==21):
                linea = linea * 10              
            values = values + "('{}', {}, '{}', {}, {}, {}, '{}', '{}')"\
            .format(insertar[i]["nombre"], linea, insertar[i]["fecha"], int(insertar[i]["turno"]), int(insertar[i]["codigo"]), int(insertar[i]["id"]),insertar[i]["nif"], insertar[i]["observacion"])
            if (len(insertar)-1>i):
                values = values +","

        query = """
                insert into public.fichajes (nombre, linea, fecha, turno_id, codigo, operator_id, operator_nif, observaciones )  values {}
                """.format(values)        
        self.cursor.execute(query)
        self.conn.commit()
        return self.cursor.rowcount

    def comprobarOperator(self, jsonString, type):
        codigo = jsonString
        query = """
                select id, nif from public.operators o where code = {}
                """.format(codigo["codigo"])             
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def comprobarTurno(self, jsonString, hora, type):        
        query = """
                select count(*) from public.turnos where id = {} and '{}' < hora_ini
                """.format(jsonString["turno"], hora)             
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def seleccionarDatosTurno(self, selec, tabla, nombre, type):
        query = """
                select {} from public.{} where upper(nombre) = '{}'
                """.format(selec, tabla, nombre )
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def seleccionarTurnosActuales(self, fecha, hora , type):
        query = """
                   select f.id as fichadoId, f.nombre, f.codigo , d.id, d."name", f.operator_id, (select nombre from public.operators op where op.id = f.operator_id) as nombreOperado
                     from public.turnos t inner join public.fichajes f on t.id = f.turno_id inner join devices d on f.linea= d.linea where f.fecha = '{}' and '{}' >=hora_ini and 
                    (case when hora_fin<hora_ini then to_timestamp(concat(to_char( f.fecha + INTERVAL '1 day', 'YYYY/MM/DD'),' ', hora_ini  ), 'YYYY/MM/DD HH24:MI:SS') > 
                    to_timestamp(concat(to_char( f.fecha, 'YYYY/MM/DD'),' ', '{}'  ), 'YYYY/MM/DD HH24:MI:SS')  else '{}' <=hora_fin  end) 
                    """.format(fecha, hora, hora, hora )
                         
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def seleccionarTurnosporOperarioActivo(self, operador, fecha, hora, type):
        query = """
                    select f.id as fichadoId, t.tipo as tipo from public.turnos t inner join public.fichajes f on t.id = f.turno_id where f.operator_id = {} and fecha = '{}' 
                    and (case when hora_fin<hora_ini then to_timestamp(concat(to_char( f.fecha + INTERVAL '1 day', 'YYYY/MM/DD'),' ', hora_ini  ), 'YYYY/MM/DD HH24:MI:SS') <
                    to_timestamp(concat(to_char( f.fecha, 'YYYY/MM/DD'),' ', '{}'  ), 'YYYY/MM/DD HH24:MI:SS')  else '{}'>hora_fin  end) 
                    """.format(operador, fecha, hora, hora)                                       
        df = pd.read_sql(query, self.conn)        
        return self.eval(df,type)
    
    def seleccionarOperariosActivos(self, type):
        query = """
                    select * from public.activeoperator
                    """                      
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def seleccionarTurnosActivos(self, id, deviceid, type):
            query = """
                    select a.deviceid, a.id from public.activeoperator a where operarioid = {} and deviceid = {}

                    """.format(id, deviceid)                      
            df = pd.read_sql(query, self.conn)
            return self.eval(df,type)
            
    def updateOfStatus(self,tablename,value,var):
        query = """
                UPDATE public.{} SET status_of = {}
                WHERE id = {};
                """.format(tablename,value,var)
        self.cursor.execute(query)
        self.conn.commit()
 

    def insertarTurnosActivos(self,deviceid, operarioid, operario, device, nombre, fecha, fichaje_id ):
        query = """
                INSERT INTO public.activeoperator (deviceid, operarioid, operario, device, nombre, atalantago, fichaje_auto) values ({}, {}, {}, '{}', '{}', '{}', {})             
                ;
                """.format(deviceid, operarioid, operario, device, nombre, fecha, fichaje_id)
        
        self.cursor.execute(query)
        self.conn.commit()

    def borrarOperariosActivo(self,id):
        query = """
                delete from public.activeoperator where id = {}       
                ;
                """.format(id)        
        self.cursor.execute(query)
        self.conn.commit()
        return self.cursor.rowcount
        

    def insertarHistoricoTurnos(self, fichaje_id, fecha, standarevent_id ):
        query = """
                INSERT INTO public.historico_fichajes (fichaje_id, fecha, standarevent_id) values ({}, '{}', {})             
                ;
                """.format(fichaje_id, fecha, standarevent_id)
        
        self.cursor.execute(query)
        self.conn.commit()

    def actualizarTurnosActivos(self, deviceid, device, id, fichaje_auto):
        query = """
                update public.activeoperator set deviceid = {}, device = '{}', fichaje_auto = {} where id = {}          
                ;
                """.format(deviceid, device, fichaje_auto, id)
             
        self.cursor.execute(query)
        self.conn.commit()
        return self.cursor.rowcount

    def range(self, sele, tablename, value,value2, type ):
        query = """
                SELECT {}
                FROM public.{}
                WHERE fecha_carga >= current_date - interval '{}' day
                AND fecha_carga < current_date + interval '{}' day;
                """.format(sele, tablename, value, value2)
              
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)  

    def insert(self,tablename,var,value):
        query = """
                INSERT INTO public.{} {}              
                VALUES {};
                """.format(tablename,var,value)        
        self.cursor.execute(query)
        self.conn.commit()
    
    def insertLastId(self,tablename,var,value):
        query = """
                INSERT INTO public.{} {}              
                VALUES {} RETURNING id;
                """.format(tablename,var,value)             
        self.cursor.execute(query)
        res = self.cursor.fetchone()[0]
        self.conn.commit()
                
        return res

    def delete(self,tablename,id):
        query = """
                DELETE FROM public.{}
                WHERE id = {}
                """.format(tablename,id)

        self.cursor.execute(query)
        self.conn.commit()

    def modify(self,tablename,column,value,idvalue):
        query = """
                UPDATE public.{}
                SET {} = '{}'              
                WHERE id = {};
                """.format(tablename,column,value,idvalue)

        self.cursor.execute(query)
        self.conn.commit()
    
    def modifyMultiple(self,tablename, id, valor, **kwargs):
        query = "UPDATE public.{} set ".format(tablename)
        i = 0       
        for key, value in kwargs.items():            
            query += "{}='{}'".format(key, value)
            if (i!=len(kwargs)-1):
                query += ","
                i+=1                        
        query += "WHERE {} = {}".format(id, valor)        
        self.cursor.execute(query)
        self.conn.commit()

    def modifyManual(self, tablename, asig, idvalue):
        query = """
                UPDATE public.{}
                SET {}              
                WHERE id = {};
                """.format(tablename,asig,idvalue)       
        self.cursor.execute(query)
        self.conn.commit()

    def update_status(self,tablename,value,var):
        query = """
                UPDATE public.{} SET status = {}
                WHERE id = {};
                """.format(tablename,value,var)
        self.cursor.execute(query)
        self.conn.commit()

    def update(self,tablename,value,var):
        query = """
                UPDATE public.{} SET destrio = {}
                WHERE device = 'Ln{}';
                """.format(tablename,value,var)
        self.cursor.execute(query)
        self.conn.commit()

    def update(self,tablename,value,var):
        query = """
                UPDATE public.{} SET destrio = {}
                WHERE device = 'Ln{}';
                """.format(tablename,value,var)
        self.cursor.execute(query)
        self.conn.commit()

    def selectallorder(self, sele, tablename, type, order):
        query = """
                SELECT {}
                FROM public.{}
                order by {} 
                ;
                """.format(sele, tablename, order)  
        print('query')   
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def selectTimeWork(self, ofId, type ):
        query = """
            select  
            max(date) as fecha_maxima, (EXTRACT(epoch FROM (SELECT (now()-max(date))))/60) as minutos_calculo
            from 
            work_diary 
            where 
            ofid={} and event in (17,19,171);
        """.format(ofId)
        df = pd.read_sql(query, self.conn)
        return self.eval(df,type)

    def selectPesadas(self, ofId, fecha, peso):
        query = """
            select 
                count(peso_neto) as paquetes,sum(peso_neto) as peso,(sum(peso_neto)/count(peso_neto)) as peso_medio 
            from 
                pesadas 
            where 
                ofid='{}'
                and fecha>='{}'
                and peso_neto > {}
        """.format(ofId, fecha, peso)              
        df = pd.read_sql(query, self.conn)
        return df
        
    def selectPaqueteMinuto(self, sele, where1, where2):
        query = """
                SELECT {}
                FROM public.sgp_bonnysa_envases_lineas
                WHERE envase_e = '{}' and linea = '{}';
                """.format(sele, where1, where2)
               
        df = pd.read_sql(query, self.conn)
        return df
    def selectKpiLinea(self):
        query = """
            select ko3.linea, ko3.ofid, ko2.paquetes, ko2.paquetesporminuto , ko2.paqueteminrealofturno , ko2.pesomedio , ko2.sobrepeso , ko2.tiempoof 
            from kpi_of ko2 inner join 
            (select MAX(ko.id) as idKpi, a.ofid as ofid, d.linea as linea
            from activeof a inner join devices d on a.deviceid = d.id inner join kpi_of ko on ko.ofid  = a.ofid group by a.ofid, d.linea) ko3 on ko3.idKpi = ko2.id 
        """
        df = pd.read_sql(query, self.conn)
        return df
    def selectKpiSumByOf(self, ofid):
        query = """
        select ofid, SUM(paquetes) as paquetes, SUM(paquetesporminuto) as paquetesporminuto,SUM(paqueteminrealofturno) as paqueteminrealofturno, SUM(pesomedio) as pesomedio , SUM(sobrepeso) as sobrepeso , SUM(tiempoof) as tiempoof 
        from kpi_of ko2 where ofid  = {} group by ofid
        """.format(ofid)
        df = pd.read_sql(query, self.conn)
        return df
if __name__ == "__main__":
    sql = Postgres_Main_Database("BonnysaDB")
    #sql2 = Postgres_Main_Database("Metller")
    #sql3 = Postgres_Main_Database("lake")  
    #print("Conectado a la base de datos, con IP: " + sql.host + "Usamos la base de datos: "+ sql.dbname)
    #print("Conectado a la base de datos, con IP: " + sql2.host + "Usamos la base de datos: "+ sql2.dbname)
    #print("Conectado a la base de datos, con IP: " + sql3.host + "Usamos la base de datos: "+ sql3.dbname)
