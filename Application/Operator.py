class Operator:
    def __init__(self):
        self.__id = 0
        self.__nombre = ""
        self.__observacion = ""
        self.__linea = 0
        self.__codigo = 0

    def getId(self):
        return self.__id

    def setId(self, id):
        self.__id = id
    def getNombre(self):
        return self.__nombre
    def setNombre(self, nombre):
        self.__nombre = nombre
    def getObservacion(self):
        return self.__observacion
    def setObservacion(self, observacion):
        self.__observacion = observacion
    def getLinea (self):
        return self.__linea
    def setLinea(self, linea):
        self.__linea = linea
    def setCodigo (self, codigo):
        self.__codigo = codigo
    def getCodigo (self):
        return self.__codigo
    


