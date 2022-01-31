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

Mettlerthreads = []
class MettlerThread(threading.Thread):
    def __init__(self, threadID, ip, port = 23, OFID = 000):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.OFID = OFID
        self.ip = ip
        self.port = port
        self.address = (self.ip, self.port)       
        self.db = Postgres_Main_Database("Metller")
        self.sql = Postgres_Main_Database("BonnysaDB")
        self.sqlLake = Postgres_Main_Database("lake")
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.control = True
        self.client.settimeout(10)

        logging.basicConfig(filename=r"C:\Program Files\Bonnysa\Application\logs\Mettler.log", 
					format='%(asctime)s %(message)s', 
					filemode='w')
        self.logger=logging.getLogger()  
        self.logger.setLevel(logging.DEBUG)


        self.logger.info("{} creado con éxito".format(self.ip))
    
    def getTurnByHour(self):
        now = datetime.now()
        hora = now.strftime("%H:%M:%S")
        turno = self.sql.selectTurnoActual(hora, "tuple") 
        if len(turno)>0:
            return turno[0][1]
        else:
            return None

    def checkValuesOf(self):
        valor = self.checkStatusOf()
        if (valor == 1):
            self.startconn()
            values =  self.getdata()
            if values[1] != False:                        
                self.sql.updateOfStatus('devices', 0, self.threadID)
                self.logger.info("La Línea {} NO TIENE OF abierta y esta funcionando, se pone a 0 el update mostramos el banner".format(self.ip))
                self.insertOf(values)
                self.closeconn()       
    def run(self):
        while True:
            try:
                self.control = self.checkof()
                if self.control == True:
                    self.sql.updateOfStatus('devices', 1, self.threadID)
                    self.logger.info("La Línea {} TIENE OF abierta y esta funcionando, se pone a 1 el update status correcto".format(self.ip))
                self.checkconn()                
                if self.control == True:
                    self.checkconn()
                    self.startconn()                    
                    self.sql.update_status('devices', 1, self.threadID)
                    while self.control:
                        values =  self.getdata()
                        if values[1] == False:
                            break
                        self.insert(values)
                        self.control = self.checkof()
                        if self.control == True:
                            pass
                        
                        elif self.control == False:
                            self.closeconn()
                            break
                
                elif self.control == False:
                    time.sleep(5)
                    self.checkValuesOf()                        
                    self.logger.info("Línea {}, Sin OF".format(self.ip))
            
            except socket.timeout as e:
                self.logger.info( "Timeout IP línea {}, testeando conexión, {} con error: {}".format(self.ip, datetime.now(), str(e)))
                self.client.sendall(b' ')

            except  ConnectionRefusedError as e:
                    self.sql.update_status('devices', 2, self.threadID)
                    self.logger.info("El equipo {}, nos deniega la conexión, reinicio obligado del equipo con error: ".format(self.ip, str(e)))
                    time.sleep(120)

            except Exception as e:
                #self.closeconn()
                self.sql.update_status('devices', 2, self.threadID)
                time.sleep(10)
                self.logger.info("Inicio de revisión de acceso por PING con error : {}".format(str(e)))
                
    def closeconn(self):
        try:
            self.client.send(bytes("WD_STOP\r\n",'ascii'))
            self.client.shutdown(socket.SHUT_RDWR)
            time.sleep(1)

        except Exception as e :
            self.logger.info("Cierre inesperado: ".format(str(e)))

        self.client.close()

    def startconn(self):
        try:
            self.client.send(bytes("WD_SET_PROT 2\r\n",'ascii'))
            self.client.send(bytes("WD_SET_FORMAT 3\r\n",'ascii'))
            self.client.send(bytes("WD_SET_TYPE 1\r\n",'ascii'))
            self.client.send(bytes("WD_START\r\n",'ascii'))
        except Exception as e:
            self.logger.info("Error en enviar data en startconn con error: ".format(str(e)))

    def checkconn(self):
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(10)
            while True:
                try:
                    self.client.send(bytes("WD_TEST\r\n",'ascii'))
                    data = self.client.recv(300)
                    result = data.decode("ascii")

                    if result == "WD_OK\r\n":
                        self.logger.info("Conexión activa")
                        self.sql.update_status('devices', 1, self.threadID)
                        break

                    else:
                        self.logger.info("Con conexión pero sin respuesta")
                        
                        

                except socket.timeout as e:
                    self.logger.info ("Conectando Hilo de IP: " + self.ip + ", por el puerto (telnet):  "+str(self.port)+"y con error de timeout en el check: "+str(e))
                    try:
                        self.client.connect(self.address)
                        self.logger.info("Conectado a {}".format(self.ip))
                    
                    except Exception as  e:
                        self.logger.info("Imposible conectar a {}, equipo sin conexión con error: ".format(self.ip, str(e)))
                        self.sql.update_status('devices', 2, self.threadID)
                        pass
                
                except OSError:
                    self.client.connect(self.address)
                
                except Exception as e:
                    self.logger.info("Error de conexion en la IP:"+str(self.ip)+" de la línea"+str(self.threadID)+"con error :"+str(e))
                    self.sql.update_status('devices', 2, self.threadID)
                    time.sleep(5)
    
    def getdata(self):
        try:
            data = self.client.recv(22)
            result = data.decode("ascii")
            if "g" in result:
                gadata= result.split('g')
                spacedata = gadata[0].split(' ')
                num = spacedata[0]
                peso = spacedata[-1]
                #self.logger.info("Pesada, {} gr, IP de Línea {} a las {}".format(peso,self.ip,datetime.now()))
                return(["ok",num,peso, self.ip])

            else:
                peso = "Error"
                num = "Error"
                return(["error",num,peso, self.ip])
                
        except socket.timeout as e:
            self.logger.info("Timeout esperando datos, IP de Línea {} a las {} con error {}".format(self.ip,datetime.now(), str(e))) 
            return(["timeout",self.check_ping(),"timeout",self.ip])

        except Exception as e:
            self.logger.info("Error a la hora {} cuando obtenemos datos con getdata con error : {}".format(self.ip,datetime.now(), str(e))) 
            time.sleep(1)

    def insert(self,values):
        if values[0] == "ok":
            date = datetime.now()
            self.db.insert('pesadas','(codigo,peso_neto,fecha,ip,ofid)',(str(values[1]),str(values[2]),str(date),str(values[3]),str(self.OFID)))
        else:
            pass

    def insertOf(self,values):
        if values[0] == "ok":
            date = datetime.now()
            self.db.insert('pesadas','(codigo,peso_neto,fecha,ip,ofid)',(str(values[1]),str(values[2]),str(date),str(values[3]),str(0)))
            self.datesPartialClose(values[2])
        else:
            pass
    def checkof(self):
        result = self.sql.select("*", "activeof","deviceid",str(self.threadID),"dataframe")
        if result.empty:
            return (False)

        else:
            self.OFID = result["ofid"][0]
            return (True)
    def checkStatusOf(self):        
        result = self.sql.select("status_of", "devices","id",str(self.threadID),"tuple")
        return result[0][0]

    def datesPartialClose(self, peso):
        now = datetime.now()
        hora = now.strftime("%H:%M:%S")
        turno = self.sql.selectTurnoActual(hora, "tuple")      
        standarEvent= self.sql.select('*', "standarevents", "type_desc", "'lineasinof'","dataframe")    
        valueLastId =self.sql.insertLastId("work_diary", "(deviceid, event, description, date, number, ofid, type, of , turnos_id)",
         "({}, '{}', '{}', '{}', {}, {}, '{}', '{}', {})".format(int(self.threadID),standarEvent.id[0], standarEvent.description[0] , now, 1, 0, "FP",
           "", self.getTurnByHour()))
        if int(self.threadID) in [17,10,27,18,19,26]:       
            self.sqlLake.insert("work_diary_extend", "(id, deviceid, event, description, date, number, ofid, type, of, turno, atalantago )",
            "({}, {}, '{}', '{}', '{}', {}, {}, '{}', '{}', '{}', '{}')".format(valueLastId, int(self.threadID),standarEvent.id[0], standarEvent.description[0] , now, 1, 0, "FP",
           "", turno, now))       
        self.sql.insert('"OF_Pesadas_Operarios"', '(id_work_diary, id_pedido, id_linea_produccion, id_devices, "OF", "Descripcion_OF", "Articulo", "Fecha_accion", "Tipo_accion", "Descripcion_accion",\
        "Tiempo_asociado_accion", "Tipo_incidencia", "Peso_neto_mettler", "Cumple_peso", id_operarios, "NIF", "Nombre", "Turno", ofid, nif_index)',
        "({}, {}, {}, {}, '{}', '{}', '{}', '{}', '{}', '{}', {}, '{}', {}, {}, {} , {}, {}, '{}', {}, {} )".format(valueLastId, 0, "SIN LINEA", 
        int(self.threadID), "", "", "", now, standarEvent.id[0], standarEvent.description[0], 2,"FP", peso,'NULL','NULL','NULL', 'NULL', turno ,0, 'NULL' ))

def check_ping(self):
    response = os.system("ping -n 1 " + self.ip)
    if response == 0:
        pingstatus = True
    else:
        pingstatus = False

    return pingstatus

def main(mettlers):
    print("Inicializacion del sistema de captura de datos Mettler")
    for key in mettlers:
        #creamos la conexión a la base de datos
        threadID = mettlers[key] # este ID debe ser el de dispositivo
        ip = key
        Mettlerthread = MettlerThread(threadID, ip)
        Mettlerthread.start()


if __name__ == '__main__':
    main({"192.168.200.6":1, "192.168.200.7":2, "192.168.200.9":7, "192.168.200.12":13, "192.168.200.14":14, "192.168.200.15":20})
    

