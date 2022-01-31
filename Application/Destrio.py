import socket
import psycopg2
from psycopg2.extensions import AsIs
import pandas as pd
import time
import datetime
from BonnysaDBConn import Postgres_Main_Database
import threading
import logging

destrioThreads = []
class destrioThread(threading.Thread):
    def __init__(self, ip, ID, Bcon, Mcon, port = 4305):
        threading.Thread.__init__(self)
        self.pesada = [None, None]
        self.ID = ID
        self.ip = ip
        self.address = (ip, port)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(10)
        self.Bcon = Bcon
        self.Mcon = Mcon
        self.control = False
        self.count_anti_block = 0

        logging.basicConfig(filename=r"C:\Program Files\Bonnysa\Application\logs\Destrio_mettler.log", 
					format='%(asctime)s %(message)s', 
					filemode='w')
        self.logger=logging.getLogger()  
        self.logger.setLevel(logging.DEBUG)

        self.logger.info("{} creado con éxito, ID {}".format(self.ip, self.ID))

    def insertar(self):
        self.logger.info("Datos recibidos en la línea {}, peso {}, fecha = {}, en IP: {}".format(self.pesada[0], self.pesada[1], datetime.datetime.now(), self.ip))
        actualof = self.Bcon.select("*", "activeof","device","'Ln"+str(self.pesada[0])+"'","dataframe")
        d_tara = self.Bcon.select("aux_2", "devices","name","'Ln"+str(self.pesada[0])+"'","dataframe").aux_2.to_list()[0]
        pesada = float(self.pesada[1])*1000 - d_tara
        
        if actualof.empty:
            self.logger.info("NO ENCUENTRA OF en IP: {}".format(self.ip))
            self.Mcon.insert('destrios','(pesada,ip,ofid,linea)',(pesada,str(self.ip),0,str(self.pesada[0])))

        else:
            #sumas destrio total al destrio antiguo
            destrio = actualof.iloc[0][8]
            bruto = destrio + pesada
            self.Bcon.update("activeof",str(bruto),str(self.pesada[0]))
            self.logger.info("Peso registrado con Éxito!!, destrío total en la OF {} de {} gr en IP: {}".format(actualof.iloc[0]['ofid'], bruto, self.ip))
            self.Mcon.insert('destrios','(pesada,ip,ofid,linea)',(pesada,str(self.ip),actualof.iloc[0]['ofid'],str(self.pesada[0])))
            
    def run(self):
        while True:
            try:
                # Tracking de estado 
                self.logger.info("Conectado a báscula...")
                self.Bcon.update_status('devices', 2, self.ID)
                self.s.connect( self.address )
                self.logger.info("Conectado al servidor, {}".format(datetime.datetime.now()))
                self.control = True

            except OSError:
                self.Bcon.update_status('devices', 2, self.ID)
                self.logger.info("Se ha desconectado")
                self.s.close()
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.settimeout(10)
                time.sleep(20)
            
            except:
                self.Bcon.update_status('devices', 2, self.ID)
                self.logger.info("imposible conectar")
                self.control = False
                time.sleep(20)

            while self.control:
                try: 
                    data = self.s.recv(300)
                    data = data.decode("ascii")
                    spacedata = data.split('\r\n')
                    #self.logger.info(spacedata)
                    self.Bcon.update_status('devices', 1, self.ID)

                    for i in spacedata:
                        if 'LINEA' in i:
                            self.pesada[0] = i[-2:]

                        if 'Bruto' in i:
                            self.pesada[1] = i[-7:-3]

                    if self.pesada[0] is not None and self.pesada[1] is not None:
                        self.insertar()
                        self.pesada = [None, None]
                        self.count_anti_block = 0

                    if spacedata[0] == '':
                        self.count_anti_block =  self.count_anti_block + 1
                        if self.count_anti_block > 100:
                            self.pesada = [None, None]
                            self.Bcon.update_status('devices', 2, self.ID)
                            self.logger.info("Error por desconeción, excepción de antiblock")
                            self.control = False
                            self.s.close()
                            self.count_anti_block = 0


                except socket.timeout:
                    #self.logger.info( "Timeout, testeando conexión, {}".format(datetime.datetime.now()))
                    try:
                        self.s.sendall(b' ')
                        self.Bcon.update_status('devices', 1, self.ID)
                        self.count_anti_block = 0
                    except Exception as e:
                        self.pesada = [None, None]
                        self.logger.info(e)
                        self.Bcon.update_status('devices', 2, self.ID)
                        self.logger.info("Error de conexion tras timeout")
                        self.control = False 
                
                except:
                    self.pesada = [None, None]
                    self.Bcon.update_status('devices', 2, self.ID)
                    self.logger.info("Error de conexion")
                    self.control = False          

def main(destrio):
    print("Inicializacion del sistema de captura de datos Mettler en Destrío")
    for key in destrio:
        destriothread = destrioThread(key,destrio[key], Postgres_Main_Database("BonnysaDB"), Postgres_Main_Database("Metller"))
        #destrioThread = destrioThread(key, destrio[key], BonnysaDBConn.Postgres_Main_Database())
        destriothread.start()

if __name__ == '__main__':
    main({"192.168.5.86":9})
