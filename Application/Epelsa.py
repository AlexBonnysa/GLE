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
    def __init__(self, ip, ID, Bcon, Mcon, port = 1000):
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
        logging.basicConfig(filename=r"C:\Program Files\Bonnysa\Application\logs\Epelsa.log", 
					format='%(asctime)s %(message)s', 
					filemode='w')
        self.logger=logging.getLogger()  
        self.logger.setLevel(logging.DEBUG)

        self.logger.info("{} creado con éxito, ID {}".format(self.ip, self.ID))

    def insertar(self):
        # poner un if para 131 y 132 y 130
        options = ['131','132','130','211','212','210']
        results = ['13A','13B','13M','21A','21B','21M']
        print(self.pesada[0])

        if self.pesada[0] in options: self.pesada[0] = results[options.index(self.pesada[0])]
        print(self.pesada[0])
        self.logger.info("Datos recibidos en la línea {}, peso {}, fecha = {}, en IP: {}".format(self.pesada[0], self.pesada[1], datetime.datetime.now(), self.ip))
        actualof = self.Bcon.select("*", "activeof","device","'Ln"+str(self.pesada[0])+"'","dataframe")
        d_tara = self.Bcon.select("aux_2", "devices","name","'Ln"+str(self.pesada[0])+"'","dataframe").aux_2.to_list()[0]
        pesada = float(self.pesada[1])*1000 - d_tara
        
        if actualof.empty:
            self.logger.info("NO ENCUENTRA OF en IP: {}".format(self.ip))

            if self.pesada[0] in results: self.pesada[0] = options[results.index(self.pesada[0])]

            self.Mcon.insert('destrios','(pesada,ip,ofid,linea)',(pesada,str(self.ip),0,str(self.pesada[0])))

        else:
            #sumas destrio total al destrio antiguo
            destrio = actualof.iloc[0][8]
            bruto = destrio + pesada
            self.Bcon.update("activeof",str(bruto),str(self.pesada[0]))

            if self.pesada[0] in results: self.pesada[0] = options[results.index(self.pesada[0])]

            self.logger.info("Peso registrado con Éxito!!, destrío total en la OF {} de {} gr en IP: {}".format(actualof.iloc[0]['ofid'], bruto, self.ip))
            self.Mcon.insert('destrios','(pesada,ip,ofid,linea)',(pesada,str(self.ip),actualof.iloc[0]['ofid'],str(self.pesada[0])))

    def run(self):
        while True:
            try:
                # Tracking de estado 
                self.logger.info("Conectando a báscula en IP: {}".format(self.ip))
                self.Bcon.update_status('devices', 2, self.ID)
                self.s.connect( self.address )
                self.logger.info("Conectado a la báscula, {} en IP: {}".format(datetime.datetime.now(), self.ip))
                self.control = True

            except OSError:
                self.Bcon.update_status('devices', 2, self.ID)
                self.logger.info("Se ha desconectado en IP: {}".format(self.ip))
                self.s.close()
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.settimeout(10)
                time.sleep(20)
            
            except:
                self.Bcon.update_status('devices', 2, self.ID)
                self.logger.info("imposible conectar en IP: {}".format(self.ip))
                self.control = False
                time.sleep(20)

            while self.control:
                try: 
                    data = self.s.recv(300).decode("ascii")
                    data_limpio = data.strip()
#busco el texto kg para posicionarme                
                    pos_kg=data_limpio.find("kg")
# si lo encuentro es que he recibido una trama buena de peso
                    if pos_kg > 0:
#desde la posicion donde encontre el texto "kg", me muevo a la izquierda para coger el valor
                        peso=data_limpio[pos_kg-6:pos_kg]
                        peso = peso.strip()
# linea, me quedo los 2 ultimos caracteres de la trama
                        linea = int(data_limpio[-4:])
                        self.pesada = [str(linea), peso]
                        print(self.pesada)
                        self.insertar()
                        
                    else:
    # si llega trama y no lleva el texto "kg", es que recibo basura por apagado
    # pongo el valor a false para que fuerce a conectar
                        self.control = False
                        self.logger.info("No llega bien en IP: {}".format(self.ip))
            
                        self.Bcon.update_status('devices', 1, self.ID)

                except socket.timeout:
                    #self.logger.info( "Timeout, testeando conexión, {}".format(datetime.datetime.now()))
                    try:
                        self.s.sendall(b' ')
                        self.Bcon.update_status('devices', 1, self.ID)
                        self.count_anti_block = 0
                        
                    except Exception as e:
                        self.logger.info(e)
                        self.Bcon.update_status('devices', 2, self.ID)
                        self.logger.info("Error de conexion tras timeout en IP: {}".format(self.ip))
                        self.control = False 
                
                except:
                    self.Bcon.update_status('devices', 2, self.ID)
                    self.logger.info("Error de conexion en IP: {}".format(self.ip))
                    self.control = False      

def main(destrio):
    print("Inicializacion del sistema de básculas Epelsa")
    for key in destrio:
        destriothread = destrioThread(key,destrio[key], Postgres_Main_Database("BonnysaDB"), Postgres_Main_Database("Metller"))
        #destrioThread = destrioThread(key, destrio[key], BonnysaDBConn.Postgres_Main_Database())
        destriothread.start()

if __name__ == '__main__':
    main({"192.168.5.157":21, "192.168.5.206":22, "192.168.5.159":23, "192.168.5.199":24, '192.168.5.212':28, '192.168.5.214':29})
