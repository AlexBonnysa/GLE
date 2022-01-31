from pandas_ods_reader import read_ods
from Operator import Operator
from flask import Blueprint, render_template, abort, request
import BonnysaDBConn
import json
import os
import datetime
import sys
import pandas as pd
from BonnysaDBConn import Postgres_Main_Database
from config.loadData import readJson


fichajes = Blueprint('fichajes_page', __name__, template_folder='templates')

fileName = ""
operators = []
fecha = ""
turno =0
ComprobarOds = False
db = Postgres_Main_Database("BonnysaDB")

def capturarOds(uploaded_file):
    fechaAhora = datetime.datetime.now()
    script_dir = os.path.dirname(__file__) 
    try: 
        if uploaded_file.filename != '':
            fechaActual = fechaAhora.strftime("%d_%m_%Y_%H_%M_%S_")
            fichero = fechaActual+uploaded_file.filename
            rel_path = "ods\{}".format(fichero)
            abs_file_path = os.path.join(script_dir, rel_path)        
            uploaded_file.save(abs_file_path)
    except:
        e = sys.exc_info()[0]
        print("Problema con archivo:",e)
    return abs_file_path

def readOds(filename):
    global ComprobarOds
    try:
        sheet_index = 1
        df = read_ods(filename , sheet_index )
        print (df)    
        for index, row in df.iterrows():            
            if row["unnamed.1"] == "SOTANO":
                break
            if row["unnamed.1"]  is not None and row["unnamed.1"] != "NOMBRE" :
                operator = Operator()
                last_chars = row["unnamed.1"][-3:]
                last_chars = last_chars.strip()                
                if (last_chars.isnumeric()):
                    linea_nueva = last_chars
                else:               
                    operator.setNombre(row["unnamed.1"].upper().strip())
                    operator.setLinea(linea_nueva)
                    operator.setObservacion( row["unnamed.2"])
                    operators.append(operator)
        
        ComprobarOds = True
    except:
        e = sys.exc_info()[0]
        ComprobarOds = False
        print("Error leyengo el fichero", e)
          
    return operators

def comprobarValores():    
    result = 0
    for x in operators:        
        result = result + db.selectOperator("count(*)", "fichajes", fecha, turno ,x.getNombre(),"tuple")[0][0]        
    return result

def getURLIp():
    datosIni = readJson()
    url = "http://{}:{}".format(datosIni["ip2"]["ipServer"], datosIni["ip2"]["port"]) 
    return url

@fichajes.route('/operarios', methods=['GET'])
def operarios():  
    return render_template("fichajes.html", url_asig = getURLIp())


@fichajes.route('/checkValores', methods=['POST'])
def checkValores():
    #Capturamos el fichero    
    fileName=capturarOds(request.files['archivo'])    
    global fecha
    fecha=request.form['fecha']
    global turno
    turno = request.form['turno']    
    global operators
    operators = []
    operators= readOds(fileName)
    if (ComprobarOds == False):
        return "-1"
    return str(comprobarValores())

def getCodigo():
    dicts=[]    
    for x in operators:
        operDict= {}
        resultado = db.seleccionarDatosTurno("code", "operators", x.getNombre(), "tuple")
        if (len(resultado)>0):
            x.setCodigo(str(resultado[0][0]))
        else:
            x.setCodigo("0")
        operDict["nombre"]=x.getNombre()
        operDict["linea"]=x.getLinea()
        operDict["codigo"]= x.getCodigo()
        dicts.append(operDict)
    jsonResult = json.dumps(dicts)
    return jsonResult 

@fichajes.route('/cargarDatos', methods=['POST'])
def cargarDatos():       
    return (getCodigo())

def insertarOperariosSql(response):
    for x in operators:
        valor = next((i for i, item in enumerate(response) if item["nombre"] == x.getNombre()), None)
        if (x.getObservacion() is not None):
            response[valor].update({"observacion": x.getObservacion()})
        else:
            response[valor].update({"observacion": ""})
    return db.insertarDatosturno(response)

@fichajes.route('/insertarOperarios', methods=['POST'])
def insertarOperarios():    
    response = request.get_json()                
    return str(insertarOperariosSql(response)) 
    
def borrarTurno():    
    db.borrarDatosturno(fecha, turno)
    
@fichajes.route('/borrarDatos', methods=['POST'])
def borrarDatos():
    global fecha
    fecha=request.form['fecha']
    global turno
    turno = request.form['turno']
    borrarTurno()
    return (getCodigo())
def comprobarRespuesta(response):
    operDict= {}
    respuesta = db.comprobarOperator(response, 'tuple')
    if (len(respuesta)>0):
        operDict["id"]=int(respuesta[0][0])
        operDict["dni"]=respuesta[0][1]
        operDict["ok"]=True
    else:
        operDict["ok"] = False
    jsonResult = json.dumps(operDict)
    return jsonResult
@fichajes.route('/comprobarCodigo', methods=['POST'])
def comprobarCodigo():
    response = request.get_json()   
    return comprobarRespuesta(response)

def comprobarTurnoActual(response):
    now = datetime.datetime.now() 
    hora = now.strftime("%H:%M:%S")
    return db.comprobarTurno(response, hora, 'tuple')

@fichajes.route('/comprobarTurno', methods=['POST'])
def comprobarTurno():
    response = request.get_json()
    return str(comprobarTurnoActual(response)[0][0])

@fichajes.route('/comprobarFecha', methods=['POST'])
def comprobarFecha():
    now = datetime.datetime.now()  
    fecha = now.strftime("%Y-%m-%d")    
    response = request.get_json()
    fechaResponse = datetime.datetime.strptime(response["fecha"], '%Y-%m-%d')
    fechaNow = datetime.datetime.strptime(fecha, '%Y-%m-%d')
    valor = -1
    if (fechaResponse>fechaNow):   
        
        valor = 1
    
    elif (fechaResponse==fechaNow):        
        
        valor = 0
    
    else:        
        valor = -2   
    
    return str(valor)


