import socket
import threading
import time
from loguru import logger
import psycopg2
from psycopg2.extensions import AsIs
from datetime import datetime
import pandas as pd
import os
from BonnysaDBConn import Postgres_Main_Database
import logging

class BizerbaThread(threading.Thread):
    def __init__(self, threadID, ip):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.db = Postgres_Main_Database("Metller")
        self.sql = Postgres_Main_Database("BonnysaDB")
        self.sqlLake = Postgres_Main_Database("lake")
        value = self.sql.select('*', 'devices', 'id', self.threadID, 'dataframe')
        self.rute = r'\\192.168.5.51\Output\{}.txt'.format(value['description'][0])
        #self.rute = r'C:\Users\lis-solution\Desktop\Lin36.txt'
        self.old_file = []
        self.OFID = 0
        self.ip = ip
        logging.basicConfig(filename=r"C:\Program Files\Bonnysa\Application\logs\Bizerbas.log",
					format='%(asctime)s %(message)s', 
					filemode='w')
        self.logger=logging.getLogger()  
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("{} creado con éxito".format(self.ip))

    def parsehora(self, t):
        hora_minuto = t[:2]+':'+t[2:]
        
        return hora_minuto

    def parsedate(self, d):
        date_form = d[4:]+'-'+d[2:4]+'-'+d[:2]
        return date_form

    def parseweigth(self, w):
        sweitgth = w.split(";")
        weitgth = int(sweitgth[-1])

        return weitgth
    
    def getTurnByHour(self):
        now = datetime.now()
        hora = now.strftime("%H:%M:%S")
        turno = self.sql.selectTurnoActual(hora, "tuple") 
        if len(turno)>0:
            return turno[0][1]
        else:
            return None

    def readfile(self):
        with open(self.rute) as f:
            lines = []
            
            for line in f:
                lines.append(line)
                #self.logger.info(line)
        return lines

    def parse_line(self, sline, control, valueId, turno,standarEvent):
        #control_line = sline[0]+sline[1]+sline[2]
        con1 = int( sline[0]+sline[1]) % 10 == 0
        con2 = int(sline[2]) != 0 
        if con1 and con2:
            hora = self.parsehora(sline[-2])
            fecha = self.parsedate(sline[-5])
            peso = self.parseweigth(sline[-6])
            self.insert(control, peso, hora, fecha)
            self.checkValuesOf(peso, hora, fecha, valueId, turno, standarEvent)
        
        else:
            pass

    def readlines(self, lines):
        control = self.checkof()
        #control = True
        standarEvent = self.getStandardEvent()
        turno = self.getTurn()
        valueId = self.datesNoLineOnce(standarEvent, turno)
        if (control == False):
            self.sql.updateOfStatus('devices', 0, self.threadID)
            self.logger.info("La Línea {} NO TIENE OF abierta y esta funcionando, se pone a 0 el update mostramos el banner".format(self.ip))
        for line in lines:
            sline = line.split("|")
            try:
                self.parse_line(sline, control, valueId, turno, standarEvent)

            except ValueError:
                #self.logger.info("Linea no parseable")
                pass    
            
            except:
                #self.logger.info("Error parseando")
                pass
    
    def insert(self,control, peso, hora, fecha):
        date = fecha+" "+hora #2020-09-29 09:47:37
        #self.logger.info(datetime.now().date())
        #self.logger.info(datetime.now().time())

        if control == True:
            date = datetime.now()
            #self.logger.info('Pesada registrada')
            #self.logger.info("Pesada insertada {} gr".format(peso))
            self.db.insert('pesadas','(codigo,peso_neto,fecha,ip,ofid)',(str(0),str(peso),str(date),str(self.ip),str(self.OFID)))
            #self.logger.info("Peso {}, en la ip {} para la OF: {}".format(peso, self.ip, self.OFID))
        else:
            pass
    def checkStatusOf(self):        
        result = self.sql.select("status_of", "devices","id",str(self.threadID),"tuple")
        return result[0][0]

    def insertOf(self, peso, hora, fecha, valueId, turno, standarEvent):
        date = fecha+" "+hora #2020-09-29 09:47:37
        self.db.insert('pesadas','(codigo,peso_neto,fecha,ip,ofid)',(str(0),str(peso),str(date),str(self.ip),str(0)))
        self.datesNoLineMultiple(standarEvent, turno, peso, valueId)
        
    def check_status(self):
        try:
            new_file = self.readfile()
            self.sql.update_status('devices', 1, self.threadID)
            return new_file
        
        except FileNotFoundError:                
                self.logger.info("No existe el archivo para {}".format(self.ip))
                #self.sql.updateOfStatus('devices', 1, self.threadID)
                self.old_file = []


    def getStandardEvent(self):
        return self.sql.select('*', "standarevents", "type_desc", "'lineasinof'","dataframe")           
    
    def getTurn(self):
        now = datetime.now()
        hora = now.strftime("%H:%M:%S")
        turno = self.sql.selectTurnoActual(hora, "tuple")
        return turno[0][0].capitalize()

    def datesNoLineOnce(self, standarEvent, turno): 
        now = datetime.now()               
        valueLastId =self.sql.insertLastId("work_diary", "(deviceid, event, description, date, number, ofid, type, of, turnos_id )",
         "({}, '{}', '{}', '{}', {}, {}, '{}', '{}', {})".format(int(self.threadID),standarEvent.id[0], standarEvent.description[0] , now, 1, 0, "FP",
           "", self.getTurnByHour()))
        if int(self.threadID) in [17,10,27,18,19,26]:       
            self.sqlLake.insert("work_diary_extend", "(id, deviceid, event, description, date, number, ofid, type, of, turno, atalantago )",
            "({}, {}, '{}', '{}', '{}', {}, {}, '{}', '{}', '{}', '{}')".format(valueLastId, int(self.threadID),standarEvent.id[0], standarEvent.description[0] , now, 1, 0, "FP",
           "", turno, now))
        return valueLastId 

    def datesNoLineMultiple(self, standarEvent, turno, peso, valueLastId):
        now = datetime.now()
        self.sql.insert('"OF_Pesadas_Operarios"', '(id_work_diary, id_pedido, id_linea_produccion, id_devices, "OF", "Descripcion_OF", "Articulo", "Fecha_accion", "Tipo_accion", "Descripcion_accion",\
        "Tiempo_asociado_accion", "Tipo_incidencia", "Peso_neto_mettler", "Cumple_peso", id_operarios, "NIF", "Nombre", "Turno", ofid, nif_index)',
        "({}, {}, '{}', {}, '{}', '{}', '{}', '{}', '{}', '{}', {}, '{}', {}, {}, {} , {}, {}, '{}', {}, {} )".format(valueLastId, 0, 'SIN LINEA', 
        int(self.threadID), "", "", "", now, standarEvent.id[0], standarEvent.description[0], 2,"FP", peso,'NULL','NULL','NULL', 'NULL', turno ,0, 'NULL' ))
    

    def checkof(self):
        result = self.sql.select("*", "activeof","deviceid",str(self.threadID),"dataframe")
        if result.empty:
            return (False)

        else:
            self.OFID = result["ofid"][0]
            return (True)
    def checkValuesOf(self, peso, hora, fecha, valueId, turno, standarEvent):

        
        self.insertOf(peso, hora, fecha, valueId, turno, standarEvent)
                 
    def run(self):
        while True:
            try:
                control = self.checkof()
                #self.logger.info("Se han detectado {} líneas diferentes".format(len(diff_lines))) 
                if control == True:
                   self.sql.updateOfStatus('devices', 1, self.threadID)
                   self.logger.info("La Línea {} TIENE OF abierta , se pone a 1 el update status correcto".format(self.ip)) 
                new_file = self.check_status()

                diff_lines = [x for x in new_file if x not in self.old_file]
                          

                if new_file == self.old_file:
                    self.logger.info("Archivos iguales")                    
                    pass
                
                else:
                    self.logger.info("Arhivos diferentes")                    
                    self.readlines(diff_lines)
                    self.old_file = new_file

                self.logger.info("Ciclo completado, se han insertado {} líneas, se inicia 17 segundos de delay".format(len(diff_lines)))
                time.sleep(17)
            
            except TypeError:
                time.sleep(17)

            except :
                self.logger.info("Error en el programa")
                self.old_file = []       

def main(bizerbas):
    print("Inicializacion del sistema de captura de datos Bizerba")
    for key in bizerbas:
        #creamos la conexión a la base de datos
        threadID =  bizerbas[key] # este ID debe ser el de dispositivo
        ip = key
        Bizerbathread = BizerbaThread(threadID, ip)
        Bizerbathread.start()
        #run(r'\\192.168.5.51\Output\Lin13A.txt')

if __name__ == '__main__':
    #main({'192.168.200.10':11, "192.168.200.17":12,"192.168.200.1":16})
    main({'192.168.200.10':11, "192.168.200.17":12, "192.168.200.2":15, "192.168.200.3":17, "192.168.200.20":10, "192.168.200.1":16, "192.168.200.6":18, "192.168.200.4":19})

    
