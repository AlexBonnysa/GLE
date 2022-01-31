import psycopg2
# import the error handling libraries for psycopg2
from psycopg2 import OperationalError, errorcodes, errors
import pandas as pd
from ConnDb import ConnDb
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from config.loadData import readJson
from LogData import LogData



class PostgreeConnDB(ConnDb):

    def __init__(self, variable):       
        super(PostgreeConnDB, self).__init__(variable)
        #self.pruebaDB()        
        #self.connectDB()
    
    def print_psycopg2_exception(self, err):
        # get details about the exception
        err_type, err_obj, traceback = sys.exc_info()

        # get the line number when exception occured
        line_num = traceback.tb_lineno

        # print the connect() error
        print ("\npsycopg2 ERROR:", err, "on line number:", line_num)
        print ("psycopg2 traceback:", traceback, "-- type:", err_type)

        # psycopg2 extensions.Diagnostics object attribute
        print ("\nextensions.Diagnostics:", err.diag)

        # print the pgcode and pgerror exceptions
        print ("pgerror:", err.pgerror)
        print ("pgcode:", err.pgcode, "\n")
    
    def connectDB(self):
        try:
            conn_string = "host=" + super().server + " dbname=" + super().database + " user=" + super().username + " password=" + super().password + " port=" + str(super().port)            
            self.conn = psycopg2.connect(conn_string)
                       
        except psycopg2.Error as e:
            super().log.logRegister("error al conectar a la base de dato con esta cadena"+str(e))
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

    def read(self,query, type):
        self.connectDB()
        cursor = self.conn.cursor()
        cursor.execute(query) 

        records = [row for row in cursor.fetchall()]
        
        if not records:
            values =  [0] * len([ x.name for x in cursor.description ])
            heads = [ x.name for x in cursor.description ]
            dictionary = dict(zip(heads, values))

            df =pd.DataFrame.from_dict(dictionary, orient='index')
            df = df.T

        else:
            df = pd.DataFrame(records)
            df.columns=[ x.name for x in cursor.description ]
        
        #self.cursor.close()

        records = df.to_records(index=False)
            #print(records)
        tup = list(records)
        cursor.close()   
        super().closeDb() 

        if type == "dataframe":
            return df
        if type == "tuple":
            return tup               
            
                   
    def selectScadaDate(self, ofid, turno, fecha):        
        query = """select d.id_scada , MIN(date) as fecha_ini, MAX(date) as fecha_fin , (DATE_PART('day', SUM(("date")-(date_start))) * 24 + 
               DATE_PART('hour', SUM(("date")-(date_start))) * 60 +
               DATE_PART('minute', SUM(("date")-(date_start)))) AS DateDifference from work_diary wd inner join devices d on wd.deviceid = d.id where ofid = '{}'
               and turnos_id = {} and date >= '{}' group by id_scada
                """.format(ofid, turno, fecha)
        
               
        return self.selectGlobal(query, "dataframe", "kpi")
    
    def selectScadaDates(self, ofid, turno, fecha):

        query = """select date_start as fecha_ini, date as fecha_fin
                    from work_diary where ofid = '{}' and turnos_id = {} and date >= '{}'  and event in (18,20) and date_start is not null
                """.format(ofid, turno, fecha) 
        return self.selectGlobal(query, "dataframe", "kpi")

    def selectScadaDatesNow(self, ofid, turno, fecha):

        query = """select date as fecha_ini, now() AT TIME ZONE 'Europe/Madrid' as fecha_fin from work_diary wd
                    inner join ofs o on wd.ofid  = o.id
                    where o.status = 'running' and ofid = '{}' and turnos_id = {} and date >= '{}'  and event in (17,19) and date_start is null order by wd.id desc limit 1
                """.format(ofid, turno, fecha) 
        return self.selectGlobal(query, "dataframe", "kpi")

    def selectScadaDatePalet(self, ofid, turno, fecha, fecha2):        
        query = """select d.id_scada , MIN(date) as fecha_ini, MAX(date) as fecha_fin , (DATE_PART('day', SUM(("date")-(date_start))) * 24 + 
               DATE_PART('hour', SUM(("date")-(date_start))) * 60 +
               DATE_PART('minute', SUM(("date")-(date_start)))) AS datedifference from work_diary wd inner join devices d on wd.deviceid = d.id where ofid = '{}'
               and turnos_id = {} and wd.date >= '{}' and date <= '{}'  group by id_scada
                """.format(ofid, turno, fecha2, fecha)
              
        return self.selectGlobal(query, "dataframe", "kpi")
    def selectScadaDateRun(self, ofid, turno, fecha):        
        query = """select (DATE_PART('day', now() - MAX(date)) * 24 + 
               DATE_PART('hour', now() - MAX(date)) * 60 +
               DATE_PART('minute', now() - MAX(date))) AS dateDifference from work_diary wd 
               inner join devices d on wd.deviceid = d.id 
               inner join ofs o on wd.ofid  = o.id
               where ofid = '{}'
               and o.status = 'running'
               and wd.event in (17,19)
               and turnos_id = {}
               and wd.date >= '{}'
               group by id_scada
                """.format(ofid, turno, fecha)
        
                
        return self.selectGlobal(query, "dataframe", "kpi")
    def selectScadaDateRunPalet(self, ofid, turno, fecha, fecha2):        
        query = """select d.id_scada , MIN(date) as fecha_ini, MAX(date) as fecha_fin , (DATE_PART('day', '{}' - MAX(date)) * 24 + 
               DATE_PART('hour', '{}' - MAX(date)) * 60 +
               DATE_PART('minute', '{}' - MAX(date))) AS datedifference from work_diary wd 
               inner join devices d on wd.deviceid = d.id 
               inner join ofs o on wd.ofid  = o.id
               where ofid = '{}'              
               and wd.event in (17,19)
               and turnos_id = {}
               and date <= '{}' and
               wd.date >= '{}'
               group by id_scada
                """.format(fecha,fecha,fecha,ofid,turno,fecha, fecha2)

                
        return self.selectGlobal(query, "dataframe", "kpi")

    def selectMaxDatePallet(self, ofid, turno, fecha):        
        query = """select count(*) as numero, Max(date) as fechamaxima from work_diary wd
                where ofid = {}               
               and wd.event in (1)
               and turnos_id = {}
               and wd.date >= '{}'
                """.format(ofid, turno, fecha)
       
        return self.selectGlobal(query, "dataframe", "kpi")

    def selectData(self, tabla, type, *args, **kwargs):
        self.connectDB()
        df =  super().selectData(tabla, type, *args, **kwargs)        
        return df    

    def selectGlobal(self, query, type="dataframe", tipo= "ninguno"):
        if(self.verbose==2):
            if(tipo=="kpi"):
                self.log.setSql(query)   
                self.log.logRegister("aviso","SENTENCIA SQL KPI")
        self.connectDB()
        df = super().getData(query, type)        
        return df

    def select(self, sele, tablename, var, value, type):               
        query = """
                SELECT {}
                FROM public.{}
                WHERE {} = {};
                """.format(sele, tablename, var, value)
        return self.selectGlobal(query, type)       

    def selectall(self, sele, tablename, type):
        
        query = """
                SELECT {}
                FROM public.{};
                """.format(sele, tablename)
              
        return self.selectGlobal(query, type)  

    def selectAofsById(self, id, type):
        
        query = """
                SELECT p.estado
                FROM public.pedidosllanos p inner join public.ofs o ON o.id_pedido = p.id
                WHERE o.of = '{}';
                """.format(id)       
        return self.selectGlobal(query, type) 

    def selectAOfs(self, sele, tablename, var, value, type):
        
        query = """
                SELECT {}, (select estado from public.pedidosllanos p inner join public.ofs o ON o.id_pedido = p.id where o.id = a.ofid ) as estado,
                (select producto from public.pedidosllanos p inner join public.ofs o ON o.id_pedido = p.id where o.id = a.ofid ) as producto
                FROM public.{} a               
                WHERE {} = {} 
                """.format(sele, tablename, var, value)
        
        return self.selectGlobal(query, type) 

    def selectOfsFin(self, sele, tablename, var, value, type):
        
        query = """
                SELECT {}
                FROM public.{} o inner join pedidosllanos p ON o.id_pedido = p.id             
                WHERE o.{} = {} and p.estado IN ('1', '5');
                """.format(sele, tablename, var, value)
        return self.selectGlobal(query, type)   

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
        return self.selectGlobal(query, type)  
    
    def selectActiveOfEvent(self, sele, tablename, where1, value1, type):
        
        query ="""
               SELECT {}
               FROM public.{}
               WHERE {} in {}
               order by {} asc
                """.format(sele, tablename, where1, value1, where1)
        
        return self.selectGlobal(query, type)  

    def selectall(self, sele, tablename, type):
        
        query = """
                SELECT {}
                FROM public.{};
                """.format(sele, tablename)              
        
        return self.selectGlobal(query, type) 

    def select2(self, sele, tablename, var, value, var2, value2, var3, value3,type ):
        
        query = """
                SELECT {}
                FROM public.{}
                WHERE {} = {}
                and {} = {}
                or {} = {}
                and creation > current_date - interval '15' day;
                """.format(sele, tablename, var, value, var2, value2, var3, value3)
              
        return self.selectGlobal(query, type) 

    def selectOfsGeneral(self, sele, tablename, var, value, type):
        query = """
                SELECT o.{}, p.estado
                FROM public.{} o inner join pedidosllanos p ON o.id_pedido = p.id
                WHERE {} = {};
                """.format(sele, tablename, var, value)

        return self.selectGlobal(query, type)

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
        return self.selectGlobal(query, type)
   
    def selectnorunning(self, sele, tablename, var, value, type):
        query ="""
                SELECT {}
                FROM public.{}
                WHERE {} = {}
                AND status != 'running';
                """.format(sele, tablename, var, value)
              
        return self.selectGlobal(query, type) 
    
    def select_filter(self, sele, tablename,type):
        query = """
                SELECT {}
                FROM public.{}
                ORDER BY id DESC LIMIT 300;
                
                """.format(sele, tablename)
              
        return self.selectGlobal(query, type) 

    def selectOperator(self, sele, tablename, fecha, turno, nombre, type):
        query = """
                SELECT {}
                FROM public.{}
                WHERE fecha = '{}'
                and nombre = '{}'
                and turno_id = {}              
                """.format(sele, tablename, fecha, nombre, turno)
              
        return self.selectGlobal(query, type) 

    def selectTurnoActual(self, hora, type):
        query = """
                    select tipo, id from turnos where   (case when hora_fin<hora_ini then to_timestamp(concat(to_char(  current_date + INTERVAL '1 day', 'YYYY/MM/DD'),' ', '{}'  ), 'YYYY/MM/DD HH24:MI:SS') > 
                    to_timestamp(concat(to_char(current_date , 'YYYY/MM/DD'),' ', hora_ini  ), 'YYYY/MM/DD HH24:MI:SS') and to_timestamp(concat(to_char(  current_date, 'YYYY/MM/DD'),' ', '{}'  ), 'YYYY/MM/DD HH24:MI:SS') <=to_timestamp(concat(to_char(  current_date + INTERVAL '1 day', 'YYYY/MM/DD'),' ', hora_fin  ), 'YYYY/MM/DD HH24:MI:SS')  else '{}' >hora_ini and '{}' <=hora_fin  end)  
                    """.format(hora, hora, hora, hora)                
        return self.selectGlobal(query, type)

    def selectTurnoActualFecha(self, hora, type):
        query = """
                    select tipo, id, hora_ini,
                    (case when '{0}'>='00:00:00' and '{0}' <= (select MIN(hora_fin) from turnos ) then current_date + INTERVAL '1 day' else current_date end) as hora_calculada
                    from turnos 
                    where (case when hora_fin<hora_ini then to_timestamp(concat(to_char(  current_date + INTERVAL '1 day', 'YYYY/MM/DD'),' ', '{0}'  ), 'YYYY/MM/DD HH24:MI:SS') > 
                    to_timestamp(concat(to_char(current_date , 'YYYY/MM/DD'),' ', hora_ini  ), 'YYYY/MM/DD HH24:MI:SS') and to_timestamp(concat(to_char(  current_date, 'YYYY/MM/DD'),' ', '{0}'  ), 'YYYY/MM/DD HH24:MI:SS')
                     <=to_timestamp(concat(to_char(  current_date + INTERVAL '1 day', 'YYYY/MM/DD'),' ', hora_fin  ), 'YYYY/MM/DD HH24:MI:SS')  else '{0}' >hora_ini and '{0}' <=hora_fin  end)  
                    """.format(hora)
                   
        return self.selectGlobal(query, type) 

    def borrarDatosturno(self, fecha, turno):
        query = """
                delete from public.fichajes where fecha = '{}' and turno_id = {}; 
                """.format(fecha, turno)
        return self.insertDB(query)

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
        return self.insertDB(query)

    def comprobarOperator(self, jsonString, type):
        codigo = jsonString
        query = """
                select id, nif from public.operators o where code = {}
                """.format(codigo["codigo"])             
        return self.selectGlobal(query, type) 

    def comprobarTurno(self, jsonString, hora, type):        
        query = """
                select count(*) from public.turnos where id = {} and '{}' < hora_ini
                """.format(jsonString["turno"], hora)             
        return self.selectGlobal(query, type)

    def seleccionarDatosTurno(self, selec, tabla, nombre, type):
        query = """
                select {} from public.{} where upper(nombre) = '{}'
                """.format(selec, tabla, nombre )
        return self.selectGlobal(query, type) 

    def seleccionarTurnosActuales(self, fecha, hora , type):
        query = """
                   select f.id as fichadoId, f.nombre, f.codigo , d.id, d."name", f.operator_id, (select nombre from public.operators op where op.id = f.operator_id) as nombreOperado
                     from public.turnos t inner join public.fichajes f on t.id = f.turno_id inner join devices d on f.linea= d.linea where f.fecha = '{}' and '{}' >=hora_ini and 
                    (case when hora_fin<hora_ini then to_timestamp(concat(to_char( f.fecha + INTERVAL '1 day', 'YYYY/MM/DD'),' ', hora_ini  ), 'YYYY/MM/DD HH24:MI:SS') > 
                    to_timestamp(concat(to_char( f.fecha, 'YYYY/MM/DD'),' ', '{}'  ), 'YYYY/MM/DD HH24:MI:SS')  else '{}' <=hora_fin  end) 
                    """.format(fecha, hora, hora, hora )
                         
        return self.selectGlobal(query, type) 

    def seleccionarTurnosporOperarioActivo(self, operador, fecha, hora, type):
        query = """
                    select f.id as fichadoId, t.tipo as tipo from public.turnos t inner join public.fichajes f on t.id = f.turno_id where f.operator_id = {} and fecha = '{}' 
                    and (case when hora_fin<hora_ini then to_timestamp(concat(to_char( f.fecha + INTERVAL '1 day', 'YYYY/MM/DD'),' ', hora_ini  ), 'YYYY/MM/DD HH24:MI:SS') <
                    to_timestamp(concat(to_char( f.fecha, 'YYYY/MM/DD'),' ', '{}'  ), 'YYYY/MM/DD HH24:MI:SS')  else '{}'>hora_fin  end) 
                    """.format(operador, fecha, hora, hora)                                       
        return self.selectGlobal(query, type) 
    
    def seleccionarOperariosActivos(self, type):
        query = """
                    select * from public.activeoperator
                    """                      
        return self.selectGlobal(query, type) 

    def seleccionarTurnosActivos(self, id, deviceid, type):
            query = """
                    select a.deviceid, a.id from public.activeoperator a where operarioid = {} and deviceid = {}

                    """.format(id, deviceid)                      
            return self.selectGlobal(query, type) 
            
    def updateOfStatus(self,tablename,value,var):
        query = """
                UPDATE public.{} SET status_of = {}
                WHERE id = {};
                """.format(tablename,value,var)
        return self.insertDB(query)
 

    def insertarTurnosActivos(self,deviceid, operarioid, operario, device, nombre, fecha, fichaje_id ):
        query = """
                INSERT INTO public.activeoperator (deviceid, operarioid, operario, device, nombre, atalantago, fichaje_auto) values ({}, {}, {}, '{}', '{}', '{}', {})             
                ;
                """.format(deviceid, operarioid, operario, device, nombre, fecha, fichaje_id)
        
        return self.insertDB(query)

    def borrarOperariosActivo(self,id):
        query = """
                delete from public.activeoperator where id = {}       
                ;
                """.format(id)        
        return self.insertDB(query)
        

    def insertarHistoricoTurnos(self, fichaje_id, fecha, standarevent_id ):
        query = """
                INSERT INTO public.historico_fichajes (fichaje_id, fecha, standarevent_id) values ({}, '{}', {})             
                ;
                """.format(fichaje_id, fecha, standarevent_id)
        
        return self.insertDB(query)

    def actualizarTurnosActivos(self, deviceid, device, id, fichaje_auto):
        query = """
                update public.activeoperator set deviceid = {}, device = '{}', fichaje_auto = {} where id = {}          
                ;
                """.format(deviceid, device, fichaje_auto, id)
             
        return self.insertDB(query)

    def range(self, sele, tablename, value,value2, type ):
        query = """
                SELECT {}
                FROM public.{}
                WHERE fecha_carga >= current_date - interval '{}' day
                AND fecha_carga < current_date + interval '{}' day;
                """.format(sele, tablename, value, value2)
              
        return self.selectGlobal(query, type)   

    def insert(self,tablename,var,value):
        query = """
                INSERT INTO public.{} {}              
                VALUES {};
                """.format(tablename,var,value)
             
        return self.insertDB(query)
    
    def insertLastId(self,tablename,var,value):
        query = """
                INSERT INTO public.{} {}              
                VALUES {} RETURNING id;
                """.format(tablename,var,value)        
        return self.insertDB(query)

    def delete(self,tablename,id):
        query = """
                DELETE FROM public.{}
                WHERE id = {}
                """.format(tablename,id)

        return self.insertDB(query)

    def modify(self,tablename,column,value,idvalue):
        query = """
                UPDATE public.{}
                SET {} = '{}'              
                WHERE id = {};
                """.format(tablename,column,value,idvalue)

        return self.insertDB(query)

    def modifyManual(self, tablename, asig, idvalue):
        query = """
                UPDATE public.{}
                SET {}              
                WHERE id = {};
                """.format(tablename,asig,idvalue)       
        return self.insertDB(query)

    def update_status(self,tablename,value,var):
        query = """
                UPDATE public.{} SET status = {}
                WHERE id = {};
                """.format(tablename,value,var)
        return self.insertDB(query)

    def update(self,tablename,value,var):
        query = """
                UPDATE public.{} SET destrio = {}
                WHERE device = 'Ln{}';
                """.format(tablename,value,var)
        return self.insertDB(query)
   

    def selectallorder(self, sele, tablename, type, order):
        query = """
                SELECT {}
                FROM public.{}
                order by {} 
                ;
                """.format(sele, tablename, order)  
          
        return self.selectGlobal(query, type)

    def select_ofs_by_date(self,rang):
        query = "SELECT * FROM public.ofs WHERE fecha_carga >= current_date - interval '{}' day AND fecha_carga < current_date + interval '{}' day;".format(rang, rang)
        return self.selectGlobal(query)

    def select_orders(self, rang):
        query = "SELECT *, coalesce((SELECT concat('LN', CAST (linea_id AS VARCHAR))  FROM public.ofs where id_pedido = pedidosllanos.id limit 1), ' ') as linea FROM public.pedidosllanos WHERE fecha_carga >= current_date - interval '{}' day AND fecha_carga < current_date + interval '{}' day and estado IN ('1', '5');".format(rang, rang)
        return self.selectGlobal(query)

    def select_pedido_by_id(self, idpedido):
        query = "SELECT * FROM public.pedidosllanos where id = '{}';".format(idpedido)
        return self.selectGlobal(query)

    def select_devices(self):
        query = "SELECT * FROM public.devices;"
        return self.selectGlobal(query)

    def select_linea_incidencia_by_id(self, id):
        query = "SELECT * FROM public.linea_incidencia where id_device = '{}';".format(id)
        return self.selectGlobal(query)

    def select_standar_events(self):
        query = "SELECT * FROM public.standarevents;"
        return self.selectGlobal(query)

    def select_max_orden(self):
        query = "SELECT max(orden) orden FROM public.ofs;"
        return self.selectGlobal(query)
 
        
    def insert_r(self,tablename,var,value):
        self.connectDB()
        query = """
                INSERT INTO public.{} {}              
                VALUES {} RETURNING id;
                """.format(tablename,var,value)             
              
        cursor = self.conn.cursor()
        cursor.execute(query)
        records = cursor.fetchall()        
        self.conn.commit()
        cursor.close()
        self.closeDb()        
        return records
    def select_of_by_id(self, idof):
        query = "SELECT * FROM public.ofs where id = '{}';".format(idof)
        return self.selectGlobal(query)

    def selectOfByMaquinaId(self, maquinaid, fecha):
        query = "select a.ofid as of from activeof a inner join devices d on a.deviceid  = d.id and d.id_scada = '{}' where a.atalantago <= '{}' ".format(maquinaid, fecha)                
        return self.selectGlobal(query)

    def selectOfByMaquinaWorkId(self, maquinaid, fecha):
        query = """
        select wd.ofid as ofid from work_diary wd inner join devices d on 
        wd.deviceid  = d.id and d.id_scada  = '{0}' 
        where wd.event in (20,18) and '{1}' >= wd.date_start  and '{1}' <= wd.date limit 1 """.format(maquinaid, fecha)                     
        return self.selectGlobal(query)
    def selectScadaDateValuesSum(self, fechaIni, fechaFin, idScada, of):
        query = """
            select SUM(scada_cantidad) AS paquetes, SUM(scada_peso) AS peso, SUM(scada_peso) / SUM(scada_cantidad) AS pesomedio
            FROM  scada_valores where scada_fecha >= '{}' and scada_fecha <= '{}'			           
            and scada_id_maquina = '{}' and ofid = {}
        """.format(fechaIni,fechaFin, idScada, of )        
        return self.selectGlobal(query, "dataframe", "kpi")    




                   

        