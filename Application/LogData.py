import logging
from datetime import datetime
import os
class LogData:
    def __init__(self):
        self.__metodo = "" 
        self.__clase = ""
        self.__file  = ""
        self.__ofId = ""
        self.__pedido = "" 
        self.__modelo = ""
        self.__s = ";"
        self.__ruta = ""
        self.__statusOf =""
        self.__ip =""
        self.__sql = ""  
        self.logger = None
        self.handler1 = None

    def loadCostum(self, name):
        directorioRaiz = os.path.dirname(__file__)
        now = datetime.now()        
        filename='Error.log'      
        logRuta = "logs"
        file = os.path.join(logRuta, filename) 
        dest_path = os.path.join(directorioRaiz, file)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)         
        self.handler1 = logging.FileHandler(dest_path)        
        self.handler1.setLevel(logging.DEBUG)
        formatter = logging.Formatter(fmt='%(asctime)s;%(levelname)s;%(message)s', datefmt='%d/%m/%Y;%H:%M:%S')         
        self.handler1.setFormatter(formatter)        
        self.logger.addHandler(self.handler1)

    def removeHandler(self):
        self.logger.removeHandler(self.handler1)
        self.handler1.close()        
                              
        
    def loadDefault(self):
        directorioRaiz = os.path.dirname(__file__)
        now = datetime.now()
        fechaHora = now.strftime("%Y_%m_%d")
        filename='fichado_'+fechaHora+".log"        
        logRuta = "logs"
        file = os.path.join(logRuta, filename) 
        dest_path = os.path.join(directorioRaiz, file)
        self.logger = logging.getLogger("CFD")
        logging.basicConfig(filename=dest_path, level=logging.DEBUG, format='%(asctime)s;%(levelname)s;%(message)s', datefmt='%d/%m/%Y;%H:%M:%S')        
        #logging.basicConfig(filename=dest_path, level=logging.ERROR, format='%(asctime)s;%(levelname)s;%(message)s', datefmt='%d/%m/%Y;%H:%M:%S')
    def getMetodo(self):
        return self.__metodo
    def setMetodo(self, value):
        self.__metodo  = value
    def getfile(self):
        return self.__file
    def setfile(self, file):
        self.__file = file
    def setOfId(self, ofId):
        self.__ofId = ofId
    def setPedido(self, pedido):
        self.__pedido = pedido
    def setModelo(self, modelo):
        self.__modelo = modelo
    def setRuta(self, ruta):
        self.__ruta = ruta
    def setIp(self, ip):
        self.__ip = ip
    def setStatusOf(self, statusOf):
        self.__statusOf = statusOf
    def setSql(self, sql):
        self.__sql = sql                
    
    def logRegister(self, type, mensaje):
        cadena = ""
        cadena += self.__metodo+self.__s+self.__ruta+self.__s+self.__file+self.__s+self.__ofId+self.__s
        cadena += self.__pedido+self.__s+self.__modelo+self.__s+self.__ip+self.__s+self.__statusOf
        cadena += self.__s+self.__sql
        cadena += self.__s+mensaje
        if (type == "aviso"):
            self.logger.info(cadena)            
        elif (type == "error"):
            self.logger.error(cadena)
        elif (type == "critico"):
            self.logger.critical(cadena)
        elif (type == "debug"):
            self.logger.debug(cadena)
    def __del__(self):
        try:
            self.logger.removeHandler(self.handler1)
            self.handler1.close()
        except Exception as e:
            pass