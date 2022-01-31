from posixpath import pardir
from LogData import LogData
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sys
import os
import pandas as pd
from BonnysaDBConn import Postgres_Main_Database
from datetime import datetime, timedelta
import ast
from shutil import copyfile, get_unpack_formats
import base64
import json
import logging
import socket
from PostgreeConnDB import PostgreeConnDB
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from config.loadData import readJson
from utils.DirectoryUtils import DirectoryUtils
from MysqlConnDB import MysqlConnDB
from SqlServerConnDB import SqlServerConnDB
from ImageConverterPdf import ImageConverterPdf

datosIni = readJson()
db = Postgres_Main_Database("BonnysaDB")
dbMetller = Postgres_Main_Database("Metller")
dbLake = Postgres_Main_Database("lake")
dbMysql = MysqlConnDB("Comer")
log = LogData()    
log.loadCostum("mylog2")   


def getURLIp():
    datosIni = readJson()    
    url = "http://{}:{}".format(datosIni["ip2"]["ipServer"], datosIni["ip2"]["port"])     
    return url


def getPaths(id):    
    directorioRaiz = os.path.dirname(__file__)
    pdfRuta = "static\proceso\\"
    idRuta = str(id)+"\\"    
    dest_path = os.path.join(directorioRaiz, pdfRuta, idRuta)
    return dest_path

def processAndGenFiles(rute, dest_path, file_name, id):
    copyfile(rute.strip(), dest_path+file_name)
    imageC = ImageConverterPdf()    
    imageC.TransformImage(dest_path,file_name, id)

def genImageFromPdf(id, source_path):
    dest_path = getPaths(id)   
    file_name = str(id)+".pdf"   
    dir = DirectoryUtils()
    dir.createDirectory(dest_path)
    try:    
        if source_path.iloc[0][0] == 0:
            dir.deleteFilesInDirectory(dest_path)
            return
        else:
            rute = r"{}".format(source_path.iloc[0][0])
        exist = dir.checkIfFileNameExist(dest_path+file_name)
        if exist:        
            same =dir.checkIfFileIstheSame(dest_path+file_name, rute.strip())
            if not same:            
                dir.deleteFilesInDirectory(dest_path)
                processAndGenFiles(rute, dest_path, file_name, id)           
        else:        
            processAndGenFiles(rute, dest_path, file_name, id)
    except Exception as e:              
        try:
            log.logRegister("Error en el proceso de copiar fichas técnicas", str(e))  
            dir.deleteFilesInDirectory(dest_path)
        except:
            log.logRegister("Error fatal en el proceso de borrado de fichas técnias", str(e))
        log.removeHandler()

    

def copypdf (id,source_path):
    #Cambiar cada vez que se mueve de carpera
    directorioRaiz = os.path.dirname(__file__)
    pdfRuta = "static\docs\PDF0.pdf"
    try:
        rutaRelativa = "static\docs\PDF"
        dest_path = os.path.join(directorioRaiz, rutaRelativa)        
        file_name = str(id)+".pdf"
        if source_path.iloc[0][0] == 0:
            rute = os.path.join(directorioRaiz, pdfRuta)
        else:
            rute = r"{}".format(source_path.iloc[0][0])
        #INSERTAMOS LOGS
        log.setRuta(rute)
        log.setfile(dest_path+file_name)
        log.setMetodo(sys._getframe().f_code.co_name)
        copyfile(rute.strip(), dest_path+file_name)
        log.removeHandler()    
    except Exception as e:
        print("Sin conexión con las fichas técnicas")        
        log.logRegister("error", str(e))
        log.removeHandler()
        rute = os.path.join(directorioRaiz, pdfRuta)
        copyfile(rute.strip(), dest_path+file_name)

from fichajes import fichajes
from asignacion import asignacion


app = Flask(__name__, static_url_path='/static')

app.register_blueprint(fichajes)
app.register_blueprint(asignacion)
#settings
app.secret_key = "770072020"

def getOfs(idip):
    return db.selectAOfs('*', 'activeof', 'deviceid', idip,"tuple")

def getDataIp():
    ip = str(request.remote_addr)    
    return db.selectData('devices', "dataframe" ,'*', ip = ip)

def getOperByLine():
    result = getDataIp()
    operario =  db.selectData("activeoperator", "tuple", "count(*)", deviceid = result.id[0])
    return operario[0][0]

def getTurnByHour():
    now = datetime.now()
    hora = now.strftime("%H:%M:%S")
    turno = db.selectTurnoActual(hora, "tuple") 
    if len(turno)>0:
        return turno[0][1]
    else:
        return None

def addDateCloseOf(of, id):
    print("OF:", of)
    print("ID:", id)
    dfDatos = db.selectWorkDiaryLast("work_diary", "dataframe", "date", ofid = of)
    db.modify("work_diary", "date_start", dfDatos.date[0], id)

def getUrl(ruta):
    ruta = db.selectData("fichas_tecnicas", "dataframe", "ruta", id = ruta )
    if len(ruta)==0 or ruta.ruta[0] is None:
        return "static/docs/PDF0.pdf"
    else: return ruta.ruta[0].strip()

    
def getRouteUrl(incs):
    if len(incs)>0:
        ruta = incs[0][24]
        return "static/docs/PDF0.pdf" if ruta == 0 else getUrl(ruta)
        
    

@app.route("/")
def Index():    
    result = getDataIp()
    path = getPaths(result['id'][0])    
    dir = DirectoryUtils()
    fileList = dir.listFilesInDirectory(path)

    imgRouta = {}

    if not result.empty:
        idip = result['id'][0]
        ofid = db.select('ofid', 'activeof', 'deviceid', idip,"dataframe")
                

        if ofid.empty:
            #incs = [(0,0)]
            incs = [(0, 0, 0, 0, 0, 0, 0, 0, 'nulo', 'nulo', 'nulo', 'nulo', 'nulo', 'nulo', 'nulo', 'nulo', 'nulo','nulo', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)]

        else:
            incs = db.select('*', 'ofs', 'id', str(ofid['ofid'][0]),"tuple")
        
        #ofs = db.select('*', 'activeof', 'deviceid', idip,"tuple")
        ruta = getRouteUrl(incs)        

        return render_template("index.html", ofs=getOfs(idip), ficheros = len(fileList), incs = incs, ruta = idip, operario = getOperByLine(), url_asig = getURLIp())
    else:        
        return("La Ip no esta registrada en la bbdd {}".format(str(request.remote_addr) ))
  

@app.route("/add_ok", methods = ["POST"])
def add_ok  ():    
    result = getDataIp()
    idip = str(result['id'][0])

    if request.method == "POST":
        result = db.select('ofid', 'activeof', 'deviceid', idip,"dataframe")

        if result.empty:
            flash("Seleccione una Orden de fabricación")
        
        else:
            #idvalue = result['ofid'][0]
            now = datetime.now()
            formvalues = dict(request.form)
            result = db.select('*', 'activeof', 'deviceid', idip,"dataframe")
            acid = str(result.iloc[0][0])
            idvalue = str(result.iloc[0][2])
            quantity = result.iloc[0][3]
            code = str(result.iloc[0][4])

            result = db.select('*', 'ofs', 'id', idvalue,"dataframe")
            modquantity = result.iloc[0][7]
            cicletime = result.iloc[0][17]
            resquantity = quantity - modquantity

            result = db.select('*', 'standarevents', 'type_desc', "'"+formvalues["Register"]+"'","dataframe")
            event = str(result.iloc[0][0])
            desc = str(result.iloc[0][3])
            typ = str(result.iloc[0][4])

            oktime = modquantity / cicletime
        
            db.modify("activeof","quantity",str(resquantity),acid)
            db.insert('work_diary','(deviceid,event,description,date,of,number,ofid,type, turnos_id)',(idip,event,desc,str(now),code,str(oktime),idvalue,typ, getTurnByHour()))

            if resquantity == 0:
                closetof(acid)

        return redirect(url_for("Index"))

@app.route("/add_incidencia", methods = ["POST","GET"])
def add_fast():    
    result = getDataIp()
    idip = str(result.iloc[0][0])
    now = datetime.now()

    if request.method == "GET":
        ofs = db.select('*', 'activeof', 'deviceid', idip,"tuple")
        logs = db.select('*','open_events','deviceid',idip,'tuple')
    
        return render_template("incidencia_particular.html",logs = logs, ofs=getOfs(idip),url_asig = getURLIp())


    elif request.method == "POST":
        formvalues = dict(request.form)
        if formvalues["incidencia"] == "particular":

            result = db.select('*', 'standarevents', 'type_desc', "'"+formvalues["incidencia"]+"'","dataframe")
            event = str(result.iloc[0][0])
            hours = formvalues["hour"]
            minutes = formvalues["min"]
            quantity = int(hours)*60 + int(minutes)
            desc = formvalues["description"]
            typ = formvalues["tipo"]

            result = db.select('*', 'activeof', 'deviceid', idip,"dataframe")
            if result.empty:
                idvalue = 0
                code = 0
            
            else:
                idvalue = str(result.iloc[0][2])
                code = str(result.iloc[0][4])

            db.insert('work_diary','(deviceid,event,description,date,of,number,ofid,type, turnos_id)',(idip,event,desc,str(now),code,str(quantity),idvalue,typ, getTurnByHour()))
            flash("Incidencia registrada")
            return redirect(url_for("add_fast"))

        elif formvalues["incidencia"] == "timeron":
            device = str(result.iloc[0][1])
            result = db.select('*', 'standarevents', 'type_desc', "'"+formvalues["incidencia"]+"'","dataframe")
            event = str(result.iloc[0][0])
            desc = formvalues["description"]
            typ = formvalues["tipo"]
            type_desc = formvalues["incidencia"]
            name = formvalues["name"]

            result = db.select('*', 'activeof', 'deviceid', idip,"dataframe")
            if result.empty:
                idvalue = 0
                code = 0
            
            else:
                idvalue = str(result.iloc[0][2])
                code = str(result.iloc[0][4])

            db.insert('open_events','(deviceid,idevent,type_desc,starttime,description,device,type,of,ofid,name)',(idip,event,type_desc,str(now),desc,device,typ,code,idvalue,name))

            flash("Contador de incidencia inicializado")
            return redirect(url_for("add_fast"))

        else:
            result = db.select('ofid', 'activeof', 'deviceid', idip,"dataframe")
            if result.empty:
                flash("Seleccione una Orden de fabricación")

            else:
                result = db.select('*', 'standarevents', 'type_desc', "'"+formvalues["incidencia"]+"'","dataframe")
                result = result.loc[(result.id_device == int(idip))]
                event = str(result.iloc[0][0])
                quantity = result.iloc[0][2]
                typ = str(result.iloc[0][4])

                result = db.select('*', 'activeof', 'deviceid', idip,"dataframe")
                idvalue = str(result.iloc[0][2])
                code = str(result.iloc[0][4])

                numerodeincidencia = formvalues["incidencia"]
                numeroinc = int(numerodeincidencia[-1])
                textoincidencia = db.select('*', 'ofs', 'id', int(idvalue),"dataframe")
                desc = textoincidencia.iloc[0][7+numeroinc]

                db.insert('work_diary','(deviceid,event,description,date,of,number,ofid,type, turnos_id)',(idip,event,desc,str(now),code,str(quantity),idvalue,typ, getTurnByHour()))

                """ Insertar Defecto de Paquete si se selecciona atasco mordaza"""
                if formvalues["incidencia"] == "incidencia1":
                     numerodeincidencia = "incidencia9"
                     numeroinc = int(numerodeincidencia[-1])
                     desc = textoincidencia.iloc[0][7+numeroinc]
                     db.insert('work_diary','(deviceid,event,description,date,of,number,ofid,type, turnos_id)',(idip,event,desc,str(now),code,str(quantity),idvalue,typ, getTurnByHour()))
                
            return redirect(url_for("Index"))

@app.route("/login", methods = ["POST","GET"])
def login():    
    result = getDataIp()
    idip = str(result.iloc[0][0])
    name = str(result.iloc[0][1])
    now = datetime.now()
    ofs = db.select('*', 'activeof', 'deviceid', idip,"tuple")

    if int(idip) in [3, 10, 17, 18, 19]: #Ventana de las líneas 13 y 21
        if request.method == "GET" and (int(idip) == 10 or int(idip) == 17 or int(idip) == 3):
            log_A = db.select('*', 'activeoperator', 'deviceid', '17',"tuple") #Zona A de línea 13
            log_B = db.select('*', 'activeoperator', 'deviceid', '10',"tuple") #Zona B de línea 13
            log_M = db.select('*', 'activeoperator', 'deviceid', '27',"tuple") #Zona Mixta de línea 13
            return render_template("login_extend.html", logs_A = log_A, logs_B = log_B, logs_M = log_M, ofs=getOfs(idip), operario = getOperByLine(), url_asig = getURLIp() )
        
        elif request.method == "GET" and (int(idip) == 18 or int(idip) == 19):
            log_A = db.select('*', 'activeoperator', 'deviceid', '18',"tuple") #Zona A de línea 21
            log_B = db.select('*', 'activeoperator', 'deviceid', '19',"tuple") #Zona B de línea 21
            log_M = db.select('*', 'activeoperator', 'deviceid', '26',"tuple") #Zona Mixta de línea 21
            return render_template("login_extend.html", logs_A = log_A, logs_B = log_B, logs_M = log_M, ofs=getOfs(idip), operario = getOperByLine(), url_asig = getURLIp())
        
        elif request.method == "POST":
            code = int(request.form['usercode'])
            zona = int(request.form['zona'])

            if code in db.selectall('*', 'activeoperator', "dataframe").operario.to_list() and code != 0:
                flash("ya registrado en la línea {}".format(db.select('*', 'activeoperator', 'operario', code, "dataframe").device.to_list()[0]))
            
            elif code not in db.selectall('*', 'activeoperator', "dataframe").operario.to_list() or code == 0:
                try:
                    result = db.select('*', 'operators', 'code', code,"dataframe")
                    idvalue = result.iloc[0][0]
                except:
                    idvalue = 0

                if idvalue == 0:
                        flash("Inexistente")

                else:
                    idvalue = str(result.iloc[0][0])
                    nameo = result.iloc[0][2]
                    if zona == 0 and (int(idip) == 18 or int(idip) == 19):#Zona Mixta de línea 21
                        db.insert('loginout','(idoperario,idip,idevento,date)',(idvalue, '26','15',str(now)))
                        name = db.select ('name', 'devices', 'id', '26','dataframe').name.to_list()
                        db.insert('activeoperator','(deviceid,operarioid,operario,device,nombre)',('26',idvalue,code,name[0],nameo)) 
                    
                    elif zona == 1 and (int(idip) == 18 or int(idip) == 19):#Zona A de línea 21
                        db.insert('loginout','(idoperario,idip,idevento,date)',(idvalue, '18','15',str(now)))
                        name = db.select ('name', 'devices', 'id', '18','dataframe').name.to_list()
                        db.insert('activeoperator','(deviceid,operarioid,operario,device,nombre)',('18',idvalue,code,name[0],nameo))
                    
                    elif zona == 2 and (int(idip) == 18 or int(idip) == 19):#Zona B de línea 21
                        db.insert('loginout','(idoperario,idip,idevento,date)',(idvalue, '19','15',str(now)))
                        name = db.select ('name', 'devices', 'id', '19','dataframe').name.to_list()
                        db.insert('activeoperator','(deviceid,operarioid,operario,device,nombre)',('19',idvalue,code,name[0],nameo))
                    
                    elif zona == 0 and (int(idip) == 17 or int(idip) == 10 or int(idip) == 3):#Zona Mixta de línea 13
                        db.insert('loginout','(idoperario,idip,idevento,date)',(idvalue, '27','15',str(now)))
                        name = db.select ('name', 'devices', 'id', '27','dataframe').name.to_list()
                        db.insert('activeoperator','(deviceid,operarioid,operario,device,nombre)',('27',idvalue,code,name[0],nameo))
                    
                    elif zona == 1 and (int(idip) == 17 or int(idip) == 10 or int(idip) == 3):#Zona A de línea 13
                        db.insert('loginout','(idoperario,idip,idevento,date)',(idvalue, '17','15',str(now)))
                        name = db.select ('name', 'devices', 'id', '17','dataframe').name.to_list()
                        db.insert('activeoperator','(deviceid,operarioid,operario,device,nombre)',('17',idvalue,code,name[0],nameo))
                    
                    elif zona == 2 and (int(idip) == 17 or int(idip) == 10 or int(idip) == 3):#Zona B de línea 13
                        db.insert('loginout','(idoperario,idip,idevento,date)',(idvalue, '10','15',str(now)))
                        name = db.select ('name', 'devices', 'id', '10','dataframe').name.to_list()
                        db.insert('activeoperator','(deviceid,operarioid,operario,device,nombre)',('10',idvalue,code,name[0],nameo))

                    else:
                        flash("Zona no contemplada")

            return redirect(url_for("login"))   
    
    else:#Ventana de las líneas menos 13 y 21
        if request.method == "GET":
            logs = db.select('*', 'activeoperator', 'deviceid', idip,"tuple")
            return render_template("login.html", logs = logs, ofs=getOfs(idip), operario = getOperByLine(), url_asig = getURLIp())
        
        elif request.method == "POST":
            code = int(request.form['usercode'])

            if code in db.selectall('*', 'activeoperator', "dataframe").operario.to_list() and code != 0:
                #print(db.select('*', 'activeoperator', 'operario', code, "dataframe").device.to_list())
                flash("ya registrado en la línea {}".format(db.select('*', 'activeoperator', 'operario', code, "dataframe").device.to_list()[0]))
                
            elif code not in db.selectall('*', 'activeoperator', "dataframe").operario.to_list() or code == 0:
                try:
                    result = db.select('*', 'operators', 'code', code,"dataframe")
                    idvalue = result.iloc[0][0]
                except:
                    idvalue = 0

                if idvalue == 0:
                    flash("Inexistente")

                else:
                    idvalue = str(result.iloc[0][0])
                    nameo = result.iloc[0][2]
                    db.insert('loginout','(idoperario,idip,idevento,date)',(idvalue, idip,'15',str(now)))
                    db.insert('activeoperator','(deviceid,operarioid,operario,device,nombre)',(idip,idvalue,code,name,nameo))
                    flash("Registrado en el sistema")
                
            return redirect(url_for("login"))
def login2(id,idip):
    name = str(db.select('*', 'devices', 'id',"'" +idip+"'","dataframe").iloc[0][1])
    result = db.select('*', 'operators', 'id', id,"dataframe")
    code = result.code[0]
    idvalue = str(result.iloc[0][0])
    nameo = result.iloc[0][2]
    now = datetime.now()
    db.insert('loginout','(idoperario,idip,idevento,date)',(idvalue, idip,'15',str(now)))
    db.insert('activeoperator','(deviceid,operarioid,operario,device,nombre)',(idip,idvalue,code,name,nameo))

def anyadirAuxiliar(idDevice,now):
    resultActiveOf = db.select('*', 'activeof', 'deviceid', idDevice,"dataframe")

    if(len(resultActiveOf)>0):
        desc = "Cierre parcial de OF por un Logout de un operario"
        desc2 = "Inicio parcial de una OF cerrada anteriormente por un Logout de un operario"
        quantity = 1
        typ = "FP"
    standarID1 =db.select("id", "standarevents", "type_desc", "Inicioparcialoflogin", "tuple")
    standarID2 =db.select("id", "standarevents", "type_desc", "finparcialoflogout", "tuple")
    db.insert('work_diary','(deviceid,event,description,date,of,number,ofid,type, turnos_id)',(idDevice, standarID1[0][0] ,desc,str(now),resultActiveOf.of[0],str(quantity),resultActiveOf.ofid[0],typ, getTurnByHour()))
    db.insert('work_diary','(deviceid,event,description,date,of,number,ofid,type, turnos_id)',(idDevice, standarID2[0][0] ,desc2,str(now),resultActiveOf.of[0],str(quantity),resultActiveOf.ofid[0],typ, getTurnByHour()))  


def anyadirStandarEventLogOut(idDevice,now):
    listaDatos= []
    resultActiveOf = db.select('*', 'activeof', 'deviceid', idDevice,"dataframe")

    if(len(resultActiveOf)>0):
        desc = "Cierre parcial de OF por un Logout de un operario"
        desc2 = "Inicio parcial de una OF cerrada anteriormente por un Logout de un operario"
        quantity = 1
        typ = "FP"
        dict1 = {"descripcion": desc}
        dict2 = {"descripcion": desc2}         
        standardIds =db.selectActiveOfEvent("id", "standarevents", "type_desc", "('{}', '{}')".format("Inicioparcialoflogin", "finparcialoflogout"), "tuple" )
        dict1["id"] = standardIds[0][0]
        dict2["id"] = standardIds[1][0]
        listaDatos.append(dict1)
        listaDatos.append(dict2)
        for i in range(2):
            db.insert('work_diary','(deviceid,event,description,date,of,number,ofid,type, turnos_id)',(idDevice,listaDatos[i].get("id"), listaDatos[i].get("descripcion") ,str(now),resultActiveOf.of[0],str(quantity),resultActiveOf.ofid[0],typ, getTurnByHour()))    
        

@app.route("/logout/<string:id>")
def logout(id):    
    result = getDataIp()
    idip = str(result.iloc[0][0])

    result = db.select('*', 'activeoperator', 'id', id,"dataframe")
    idvalue = str(result.operarioid[0])
    login = str(result.atalantago[0])
    idDevice =  result.deviceid[0] 
    now = datetime.now()
    
    anyadirStandarEventLogOut(idDevice,now)   

    db.delete('activeoperator',id)
    db.insert('loginout','(idoperario,idip,idevento,date,login)',(idvalue, idip,'16',str(now),login))
    flash("Deslogueado del sistema correctamente")
    return redirect(url_for("login"))

def logout2(id,idip):
    result = db.select('*', 'activeoperator', 'id', id,"dataframe")
    idvalue = str(result.operarioid[0])
    login = str(result.atalantago[0])
    idDevice =  result.deviceid[0]
    now = datetime.now()

    anyadirStandarEventLogOut(idDevice,now) 

    db.delete('activeoperator',id)
    db.insert('loginout','(idoperario,idip,idevento,date,login)',(idvalue, idip,'16',str(now),login))

@app.route("/of", methods = ["POST","GET"])
def of():    
    result = getDataIp()
    idip = str(result.iloc[0][0])
    name = str(result.iloc[0][1])
    now = datetime.now()
    ofs = db.selectAOfs('*', 'activeof', 'deviceid', idip,"tuple")
    date = datetime.today()-timedelta(days=13)
    date = date.strftime('%Y-%m-%d')

    ofas = db.selectOfs('*', 'ofs','linea',idip ,'status', "'new'", 'status', "'open'","tuple")
    ofas.sort(key=lambda tup: tup[0])

    if request.method == "GET":
        return render_template("of.html", ofs = ofs, ofas = ofas, operario = getOperByLine(), url_asig = getURLIp())
    
    elif request.method == "POST":
        code = request.form['ofcode']

        result = db.selectOfsFin('*', 'ofs', 'id', code,"dataframe")
        idvalue = result.iloc[0][0]

        if idvalue == 0:
            flash("Incompleta para inciar o el estado del pedido no es correcto")
            return redirect(url_for("of"))

        else:
            idvalue = str(result.iloc[0][0])
            of = str(result.iloc[0][1])
            quantity = str(result.iloc[0][3])
            model = str(result.iloc[0][4])
            status = str(result.iloc[0][5])
            cajas = str(result.iloc[0][18])
            destrio = str(result.iloc[0][19])
            originalquantity = str(result.iloc[0][6])
            ruta = str(result.iloc[0][24])

            oktime = str(result.iloc[0][3]/ result.iloc[0][17])
            ruta = int(ruta)
            cliente = str(result.iloc[0][25])
            fecha_carga = str(result.iloc[0][27])
            fecha_produccion = str(result.iloc[0][28])
            lote_cliente = str(result.iloc[0][29])
                       
            log.setModelo(model)
            log.setPedido(of)
            log.setOfId(idvalue)

            activeornot = db.select('*', 'activeof', 'deviceid', idip, "dataframe")
            
            if status == "new":
                if activeornot.empty:
                    db.insert('work_diary','(deviceid,event,description,date,of,number,ofid,type, turnos_id)',(idip,"17","Abrir OF",str(now),of,oktime,idvalue,"IT", getTurnByHour()))
                    db.insert('activeof','(deviceid,ofid,quantity,of,device,model,cajas,destrio,originalquantity,ruta,cliente,fecha_carga,fecha_produccion,lote_cliente)',(idip,idvalue,quantity,of,name,model,cajas,destrio,originalquantity,ruta,cliente,fecha_carga,fecha_produccion,lote_cliente))
                    db.modify("ofs","status","running",idvalue)
                    flash("Incializada, recuerde cerrarla al terminar de trabajar")
                    ruta = db.select('ruta', 'fichas_tecnicas', 'id', ruta,"dataframe")
                    genImageFromPdf(idip,ruta)
                    return redirect(url_for("of"))
                else:
                    flash(" en curso, cierre la OF antes de iniciar otra")
                    return redirect(url_for("of"))

            elif status == "open":
                if activeornot.empty:
                    db.insert('work_diary','(deviceid,event,description,date,of,number,ofid,type, turnos_id)',(idip,"19","Reabrir OF",str(now),of,oktime,idvalue,"IP", getTurnByHour()))
                    db.insert('activeof','(deviceid,ofid,quantity,of,device,model,cajas,destrio,originalquantity,ruta,cliente,fecha_carga,fecha_produccion,lote_cliente)',(idip,idvalue,quantity,of,name,model,cajas,destrio,originalquantity,ruta,cliente,fecha_carga,fecha_produccion,lote_cliente))
                    db.modify("ofs","status","running",idvalue)
                    flash("Reabierta, recuerde cerrarla al terminar de trabajar")
                    ruta = db.select('ruta', 'fichas_tecnicas', 'id', ruta,"dataframe")
                    genImageFromPdf(idip,ruta)                    
                    return redirect(url_for("of"))
                else:
                    flash(" en curso, cierre la OF antes de iniciar otra")
                    return redirect(url_for("of"))

            elif status == "close":
                flash("Está cerrada, conectate con el administrador si desea reabrirla")
                return redirect(url_for("of"))

            else:
                flash("No disponible en el sistema")
                return redirect(url_for("of"))


@app.route("/closetof/<string:id>")
def closetof(id):
    now = datetime.now()

    result = db.select('*', 'activeof', 'id', id,"dataframe")
    ipid = str(result.iloc[0][1])
    idvalue = str(result.iloc[0][2])
    quantity = result.iloc[0][3]
    code = str(result.iloc[0][4])
    cajas = str(result.iloc[0][7])
    destrio = str(result.iloc[0][8])    
    dic = recolectarDatosScadaFuncion(result.ofid[0])       
    insertDataKpiPerMinuteSql(dic,result.ofid[0], getTurnByHour(), now) 
    
    result2 = db.select('cicletime', 'ofs', 'id', idvalue,"dataframe")
    restime = str(quantity / result2.iloc[0][0])

    pedidoid = db.select('id_pedido', 'ofs', 'id', idvalue,"dataframe")
    palets_completos = db.select('palets_completos', 'pedidosllanos', 'id', str(pedidoid.iloc[0][0]),"dataframe")
    palets_origen = db.select('quantity', 'ofs', 'id', idvalue,"dataframe")
    resquantity = int(palets_completos.iloc[0][0])+int(palets_origen.iloc[0][0])-int(quantity)
    db.modify("pedidosllanos","palets_completos",str(resquantity),str(pedidoid.iloc[0][0]))

    db.modify("ofs","quantity",str(quantity),idvalue)
    db.modify("ofs","status","close",idvalue)
    db.modify("ofs","cajas",cajas,idvalue)
    db.modify("ofs","destrio",destrio,idvalue)
     
    lastId =db.insertLastId('work_diary','(deviceid,event,description,date,of,number,ofid,type, turnos_id)',(ipid,"18","Cierre total OF",str(now),code,restime,idvalue,"FT", getTurnByHour()))
    db.delete("activeof",id)
    addDateCloseOf(idvalue, lastId )
    

    flash("Cerrada Totalmente")
    ruta0 = pd.DataFrame({0:[0]}, index=[0])    
    genImageFromPdf(ipid,ruta0)
    return redirect(url_for("of"))

@app.route("/closepof/<string:id>")
def closepof(id):
    now = datetime.now()

    result = db.select('*', 'activeof', 'id', id,"dataframe")
    ipid = str(result.iloc[0][1])
    idvalue = str(result.iloc[0][2])
    quantity = result.iloc[0][3]
    code = str(result.iloc[0][4])
    cajas = str(result.iloc[0][7])
    destrio = str(result.iloc[0][8])

    result2 = db.select('cicletime', 'ofs', 'id', idvalue,"dataframe")
    restime = str(quantity / result2.iloc[0][0])

    pedidoid = db.select('id_pedido', 'ofs', 'id', idvalue,"dataframe")
    palets_completos = db.select('palets_completos', 'pedidosllanos', 'id', str(pedidoid.iloc[0][0]),"dataframe")
    palets_origen = db.select('quantity', 'ofs', 'id', idvalue,"dataframe")
    resquantity = int(palets_completos.iloc[0][0])+int(palets_origen.iloc[0][0])-int(quantity)
    db.modify("pedidosllanos","palets_completos",str(resquantity),str(pedidoid.iloc[0][0]))

    db.modify("ofs","quantity",quantity,idvalue)
    db.modify("ofs","cajas",cajas,idvalue)
    db.modify("ofs","destrio",destrio,idvalue)
    db.modify("ofs","status","open",idvalue)
    lastId =db.insertLastId('work_diary','(deviceid,event,description,date,of,number,ofid,type, turnos_id)',(ipid,"20","Cierre Parcial OF",str(now),code,restime,idvalue,"FP", getTurnByHour()))
    db.delete("activeof",id)
    addDateCloseOf(idvalue, lastId )
    
    flash("Cerrada Parcialmente")
    ruta0 = pd.DataFrame({0:[0]}, index=[0])
    print("CERRADO PARCIALMENTE CON DT", ruta0)    
    genImageFromPdf(ipid,ruta0)
    return redirect(url_for("of"))
   
@app.route("/closetimer/<string:id>")
def closetimer(id):
    now = datetime.now()

    result = db.select('*', 'open_events', 'id', id,"dataframe")
    ipid = str(result.iloc[0][1])
    desc = str(result.iloc[0][6])
    typ = str(result.iloc[0][8])
    code = str(result.iloc[0][9])
    idvalue = str(result.iloc[0][10])

    interval = now - result.iloc[0][4]
    quantity = int((interval.seconds)/60)+ ((interval.seconds) % 60 > 0)

    db.insert('work_diary','(deviceid,event,description,date,of,number,ofid,type,turnos_id)',(ipid,"23",desc,str(now),code,str(quantity),idvalue,typ, getTurnByHour()))
    db.delete("open_events",id)

    flash("Incidencia cerrada Totalmente")
    return redirect(url_for("add_fast"))

@app.route("/modtimer", methods = ["POST","GET"])
def modtimer():
    formvalues = dict(request.form)

    db.modify("open_events","name",formvalues["name"],formvalues["id"])
    db.modify("open_events","type",formvalues["tipo"],formvalues["id"])
    db.modify("open_events","description",formvalues["description"],formvalues["id"])

    flash("Incidencia Modificada Correctamente")
    return redirect(url_for("add_fast"))

@app.route("/pdf")
def pdf():
    ip = "'"+str(request.remote_addr)+"'"
    result = db.select('*', 'devices', 'ip', ip,"dataframe")
    idip = str(result.iloc[0][0])

    ofs = db.select('*', 'activeof', 'deviceid', idip,"tuple")

    return render_template("pdfread.html", ofs=getOfs(idip), operario = getOperByLine(), url_asig = getURLIp())

@app.route("/pedidos")
def pedidos():   
    result = getDataIp()
    idip = str(result.iloc[0][0])
    print(idip)
    
    if idip == '0':
        print("ERROR no se permite esta IP")
        return render_template("layout.html", url_asig = getURLIp())
    
    else:
        ofs = db.select('*', 'activeof', 'deviceid', idip,"tuple")
        pedidos = db.range('*', 'pedidosllanos', 7,7, "dataframe" )
        pedidos = pedidos.astype(str).to_json(orient='records')
        pedidos = ast.literal_eval(pedidos)

        return render_template("pedidos.html", ofs=getOfs(idip), pedidoss = pedidos, operario = getOperByLine(), url_asig = getURLIp())

@app.route("/asignacion/<string:id>")
def asignacion(id):    
    result = getDataIp()
    idip = str(result.iloc[0][0])
    
    ofs = db.select('*', 'activeof', 'deviceid', idip,"tuple")
    selection = db.select('*', 'pedidosllanos', 'id', id,"tuple")
    pedidos = db.selectnorunning('*', 'ofs','id_pedido',id, "tuple")
    
    return render_template("asignacion.html",ofs=getOfs(idip), pedidos = pedidos, selection = selection, operario = getOperByLine(), url_asig = getURLIp() )

@app.route("/destrio", methods = ["POST","GET"])
def destrio():    
    result = getDataIp()
    idip = str(result.iloc[0][0])
    ofs = db.select('*', 'activeof', 'deviceid', idip,"tuple")

    weigths = db.select('*', 'activeof', 'deviceid', idip,"tuple")

    return render_template("destrio.html", ofs=getOfs(idip), weigths= weigths, operario = getOperByLine(), url_asig = getURLIp())
        
@app.route("/modweight", methods = ["POST","GET"])
def modweight():
    formvalues = dict(request.form)
    new_weigth = float(formvalues["add"])*1000
    peso = int(formvalues["peso"])+int(new_weigth)
    db.modify("activeof","destrio",str(peso),formvalues["id"])

    flash("Destrío registrado")
    return redirect(url_for("destrio"))

@app.route("/select_line", methods = ["POST","GET"])
def select_line():
    formvalues = dict(request.form)
    print(formvalues)
    if formvalues["action"] == "create":

        if formvalues["linea"].isnumeric() == True:
            oldpalets = db.select('palets_asig', 'pedidosllanos', 'id', int(formvalues["id"]),"dataframe")
            newpalets = int(oldpalets.iloc[0][0])-int(formvalues["palets"])
            date = datetime.today().strftime('%Y-%m-%d')
           
            #linea id
            idline = db.select('id', 'devices', 'linea', int(formvalues["linea"]),"dataframe")
            idline= int(idline.iloc[0][0])
            incidencias = db.select('*', 'linea_incidencia', 'id_device', idline, "dataframe")
    
            events = db.selectall('*','standarevents','dataframe')

            incidencia_1 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_1']), ['description'])].values[0][0]
            incidencia_2 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_2']), ['description'])].values[0][0]
            incidencia_3 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_3']), ['description'])].values[0][0]
            incidencia_4 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_4']), ['description'])].values[0][0]
            incidencia_5 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_5']), ['description'])].values[0][0]
            incidencia_6 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_6']), ['description'])].values[0][0]
            incidencia_7 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_7']), ['description'])].values[0][0]
            incidencia_8 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_8']), ['description'])].values[0][0]
            incidencia_9 = events.loc[(events.id == int(incidencias.iloc[0]['id_event_9']), ['description'])].values[0][0]          

            db.insert('ofs','(of,description,quantity,model,status,originalquantity,okquantity,incidenciatop1,incidenciatop2,incidenciatop3,incidenciatop4,incidenciatop5,incidenciatop6,incidenciatop7,incidenciatop8,incidenciatop9,cicletime,cajas,destrio,linea,creation,id_pedido,linea_id,ruta,cliente,fecha_carga,fecha_produccion,lote_cliente)',\
               (str(formvalues["pedido"]),str(formvalues["desc"]),str(formvalues["palets"]),str(formvalues["com"]),'new',str(formvalues["palets"]),"1",incidencia_1,incidencia_2,incidencia_3,incidencia_4,incidencia_5,incidencia_6,incidencia_7,incidencia_8,incidencia_9,"1",str(formvalues["cajas"]),"0",str(idline),date,str(formvalues["id"]),str(formvalues["linea"]),str(formvalues["ruta"]),str(formvalues["cliente"]),str(formvalues["fecha_carga"]),str(formvalues["fecha_produccion"]),str(formvalues["lote_cliente"])))
            db.modify('pedidosllanos',"palets_asig",str(newpalets),str(formvalues["id"]))
    
            return redirect(url_for("asignacion", id = formvalues["id"]))

        else:
            flash("No se ha asigando ninguna Línea")
            return redirect(url_for("asignacion", id = formvalues["id"]))
    
    elif formvalues["action"] == "edit":
        oldpalets = db.select('originalquantity', 'ofs', 'id', int(formvalues["id"]),"dataframe")
        newres = int(oldpalets.iloc[0][0]) - int(formvalues["palets"])

        oldpalets = db.select('palets_asig', 'pedidosllanos', 'id', int(formvalues["idpedido"]),"dataframe")
        newpalets = int(oldpalets.iloc[0][0]) + newres

        db.modify('pedidosllanos',"palets_asig",str(newpalets),str(formvalues["idpedido"]))
        #linea id
        idline = db.select('id', 'devices', 'linea', int(formvalues["linea"]),"dataframe")
        idline= int(idline.iloc[0][0])
        db.modify("ofs","linea",str(idline),formvalues["id"])
        db.modify("ofs","linea_id",formvalues["linea"],formvalues["id"])
        db.modify("ofs","originalquantity",formvalues["palets"],formvalues["id"])
        db.modify("ofs","quantity",formvalues["palets"],formvalues["id"])

        return redirect(url_for("asignacion", id = formvalues["idpedido"]))
    
    elif formvalues["action"] == "erase":
        oldpalets = db.select('palets_asig', 'pedidosllanos', 'id', int(formvalues["idpedido"]),"dataframe")
        newpalets = int(oldpalets.iloc[0][0])+int(formvalues["palets"])
        db.modify('pedidosllanos',"palets_asig",str(newpalets),str(formvalues["idpedido"]))
        db.delete("ofs",formvalues["id"])
        return redirect(url_for("asignacion", id = formvalues["idpedido"]))
    
    elif formvalues["action"] == "erase2":
        oldpalets = db.select('palets_asig', 'pedidosllanos', 'id', int(formvalues["idpedido"]),"dataframe")
        newpalets = int(oldpalets.iloc[0][0])+int(formvalues["palets"])
        db.modify('pedidosllanos',"palets_asig",str(newpalets),str(formvalues["idpedido"]))
        db.delete("ofs",formvalues["id"])
        return redirect(url_for("of"))
        
    else:
        flash("Error")
        return redirect(url_for("asignacion", id = formvalues["idpedido"]))

@app.route("/refresh", methods =["POST"])
def refresh():
    ip = str(request.remote_addr)
    print("Ejecución de refresco desde la IP: {}".format(ip))
    os.system("python Actualizar_pedidos.py")
    return redirect(url_for("pedidos"))

@app.route("/checklist/<string:id>")
def checklist(id):    
    result = getDataIp()
    idip = str(result.iloc[0][0])
    ofs = db.select('*', 'activeof', 'deviceid', idip,"tuple")

    try:
        com = db.select('model', 'ofs', 'id', id,"dataframe").model.to_list()
        cajas = db.select('cajas', 'ofs', 'id', id,"dataframe")
        palets = db.select('quantity', 'ofs', 'id', id,"dataframe")
        multiplicador =  cajas['cajas'][0] * palets['quantity'][0]
        
        parts = db.select('*', 'estructura_articulos', 'idestructura', "'"+com[0]+"'","dataframe")
        
        parts = parts.round({3:2})
        parts['cantidads'] =  parts.cantidads*multiplicador
        records = parts.to_records(index=False)
        parts = list(records)
        return render_template("checklist.html", parts = parts, idof = id, ofs=getOfs(idip), operario = getOperByLine(), url_asig = getURLIp() )
    
    except:
        return render_template("checklist.html", idof = id, ofs=getOfs(idip), operario = getOperByLine(), url_asig = getURLIp())

@app.route("/incidencia_contador",  methods = ["POST","GET"])
def incidencia_contador():    
    result = getDataIp()
    idip = str(result.iloc[0][0])
    name = str(result.iloc[0][1])
    now = datetime.now()
    ofs = db.select('*', 'activeof', 'deviceid', idip,"tuple")
    logs = db.select('*','open_events','deviceid',idip,'tuple')
   
    if request.method == "GET":
        return render_template("incidencia_contador.html",logs = logs, ofs=getOfs(idip), operario = getOperByLine(), url_asig = getURLIp())
    
    elif request.method == "POST":
        formvalues = dict(request.form)
        device = str(result.iloc[0][1])
        result = db.select('*', 'standarevents', 'type_desc', "'"+formvalues["incidencia"]+"'","dataframe")
        event = str(result.iloc[0][0])
        desc = formvalues["description"]
        typ = formvalues["tipo"]
        type_desc = formvalues["incidencia"]
        name = formvalues["name"]
        checklist = db.select('description','open_events','deviceid',idip,'dataframe')
        
        if desc in checklist['description'].tolist():
            flash("Contador ya inicializado, cierrelo para iniciar otro")
            return redirect(url_for("incidencia_contador"))
        
        else:
            try:
                db.insert('open_events','(deviceid,idevent,type_desc,starttime,description,device,type,of,ofid,name)',(idip,event,type_desc,str(now),desc,device,typ,ofs[0][4],ofs[0][2],name))
            except:
                db.insert('open_events','(deviceid,idevent,type_desc,starttime,description,device,type,of,ofid,name)',(idip,event,type_desc,str(now),desc,device,typ,0,0,name))
            flash("Contador de incidencia inicializado")
            return redirect(url_for("incidencia_contador"))

@app.route("/closetimer2/<string:id>")
def closetimer2(id):
    now = datetime.now()

    result = db.select('*', 'open_events', 'id', id,"dataframe")
    ipid = str(result.iloc[0][1])
    desc = str(result.iloc[0][6])
    typ = str(result.iloc[0][8])
    code = str(result.iloc[0][9])
    idvalue = str(result.iloc[0][10])

    interval = now - result.iloc[0][4]
    quantity = int((interval.seconds)/60)+ ((interval.seconds) % 60 > 0)

    db.insert('work_diary','(deviceid,event,description,date,of,number,ofid,type, turnos_id)',(ipid,"23",desc,str(now),code,str(quantity),idvalue,typ, getTurnByHour()))
    db.delete("open_events",id)

    flash("Incidencia cerrada Totalmente")
    return redirect(url_for("incidencia_contador"))

@app.route('/getState', methods=['GET','POST'])
def getState():   
   
    main_device = getDataIp()
    main_device['id'] = 1
    asociated_device = db.select('*','devices','id', str(main_device['aux_1'][0]),'dataframe')
    asociated_device['id'] = 2

    frames = [main_device, asociated_device]
    devices_short = pd.concat(frames)
    devices_short = devices_short [["id","status"]].dropna()
    #print(devices_short[["id","status"]].to_dict('split')) 
    #devices_short[["id","status"]].to_dict('split')

    return devices_short[["id","status"]].to_dict('split')

@app.route('/getEstado', methods=['POST'])
def getEstado():

    response = request.get_json()
    datos = db.selectAofsById(response['json']['id'],'dataframe')    
    return datos.iloc[0][0]

@app.route('/move', methods=['GET','POST'])
def move():

    list_of_operators = request.get_json()
    idip = str(db.select('*', 'devices', 'ip', "'"+str(request.remote_addr)+"'","dataframe").iloc[0][0])
    ofs = db.select('*', 'activeof', 'deviceid', idip,"tuple")
    for i in ['zonaM','zonaA','zonaB']:
        for j in list_of_operators['obj'][i]:
            
            try:
                linea = j['linea']
                operario = j['id']
                #zona = list_of_operators['obj'][i][0]['zona']
                operarioid = j['operarioid']
                if idip in ['10','17','27','3']:
                    zonas = {'zonaM':27, 'zonaA':17, 'zonaB':10}

                elif idip in ['18','19','26']:
                    zonas = {'zonaM':26, 'zonaA':18, 'zonaB':19}
                #a = db.select('deviceid', 'activeoperator', 'id', operario,"dataframe").deviceid[0]

                if str(zonas.get(i)) != linea:
                    logout2(int(operario),linea)
                    login2(int(operarioid),str(zonas.get(i)))

                
                #me logeo en la linea
            except:
                print('Sin datos')
    
    return "true"

@app.route('/logout_all', methods=['GET','POST'])
def logout_all():    
    result = getDataIp()
    idip = result.iloc[0][0]
    
    if idip in [3, 10, 17]:
        for j in [10,17,27]:
            log = db.select('operarioid', 'activeoperator', 'deviceid', str(j),"dataframe").operarioid.to_list()
            login = db.select('atalantago', 'activeoperator', 'deviceid', str(j),"dataframe").atalantago.to_list()
            real_idip = db.select('deviceid', 'activeoperator', 'deviceid', str(j),"dataframe").deviceid.to_list()
            for i in log:
                
                result = db.select('*', 'operators', 'id', i,"dataframe")
                code = result.code[0]
                idvalue = str(result.iloc[0][0])
                nameo = result.iloc[0][2]
                anyadirStandarEventLogOut(real_idip[0],datetime.now()) 
                db.delete('activeoperator',db.select('id', 'activeoperator', 'deviceid', str(j),"dataframe").id.to_list()[0])
                db.insert('loginout','(idoperario,idip,idevento,date,login)',(idvalue, real_idip[0],'16',str(datetime.now()),str(login[0])))

        
    elif idip in [18, 19]:
        for j in [18,19,26]:
            log = db.select('operarioid', 'activeoperator', 'deviceid', str(j),"dataframe").operarioid.to_list()
            login = db.select('atalantago', 'activeoperator', 'deviceid', str(j),"dataframe").atalantago.to_list()
            real_idip = db.select('deviceid', 'activeoperator', 'deviceid', str(j),"dataframe").deviceid.to_list()
            for i in log:
                result = db.select('*', 'operators', 'id', i,"dataframe")
                code = result.code[0]
                idvalue = str(result.iloc[0][0])
                nameo = result.iloc[0][2]
                anyadirStandarEventLogOut(real_idip[0],datetime.now()) 
                db.delete('activeoperator',j)
                db.insert('loginout','(idoperario,idip,idevento,date,login)',(idvalue, real_idip[0],'16',str(datetime.now()),str(login[0])))
                
    flash("Deslogueados Todos los operarios")
    return redirect(url_for("login"))

@app.route("/modposition", methods = ["POST","GET"])
def modposition():
     id = request.args['id']
     newData = request.args['newData']
     db.modifyManual("ofs","orden = "+newData,id)
     return 'ok'
     
@app.route('/getStatusOf', methods=['GET'])
def getStatusOf():
    log.setMetodo(sys._getframe().f_code.co_name)
    status_of=str(1)    
    try:
        ip = "'"+str(request.remote_addr)+"'"
        result = getDataIp()
        status_of = str(result['status_of'][0])
        log.setIp(ip)
        log.setStatusOf(status_of)
        if(datosIni["verbose"]["level"]== 2):
            log.logRegister("aviso", "statusOf")
            log.removeHandler()
    except Exception as e:
        log.logRegister("error", str(e))
        log.removeHandler()  
    
    return status_of

@app.route("/configuracion_linea", methods = ["POST","GET"])
def configuracion_linea():    
    result = getDataIp()
    idip = str(result.iloc[0][0])
    lineaActualSelect =  str(result.iloc[0][4])
    lineasDevices =  db.selectallorder('*','devices','tuple', 'linea')

    ofs = db.select('*', 'activeof', 'deviceid', idip,"tuple")
    return render_template("configuracion_linea.html", lineasDev=lineasDevices, lineaActualSelect=lineaActualSelect, ofs=getOfs(idip), operario = getOperByLine(), url_asig = getURLIp())

@app.route('/getLinea', methods=['GET'])
def getLinea():    
    result = getDataIp()
    lineaActual = str(result['name'][0])
    return lineaActual

@app.route('/updateLinea', methods = ["POST","GET"])
def updateLinea():    

    result = getDataIp()
    lineaActual = str(result['linea'][0])

    response = request.get_json()
    lineaNueva = response['json']['lineaNueva']

    """  tomo ip linea actual, para asignarsela a la linea nueva.  """
    resultLineaActual = db.select('ip, id', 'devices', 'linea', lineaActual,"dataframe")
    ipLineaActual = str(resultLineaActual['ip'][0])
    idLineaActual = str(resultLineaActual['id'][0])

    """  tomo ip linea nueva, para asignarsela a la linea antigua.  """
    resultLineaNueva = db.select('ip, id', 'devices', 'linea', lineaNueva,"dataframe")
    ipLineaNueva = str(resultLineaNueva['ip'][0])
    idLineaNueva = str(resultLineaNueva['id'][0])

    """ a linea actual, le asigno la ip de la nueva para no perderla """
    db.modify('devices',"ip",ipLineaNueva,idLineaActual)

    """ a linea nueva, le asigno la ip de la actual (o sea la anterior) """
    db.modify('devices',"ip",ipLineaActual,idLineaNueva)
    """ flash("Línea actualizada correctamente") """
    return redirect(url_for("configuracion_linea"))
def checkLen(df, valor):
    if len(df)==0:
        return 0
    else:
        return valor
def calcPackagePerMinute(df2, df3, dic):
    if df3 is None or len(df3)==0:
        suma = 0
    else:
        suma = df3.datedifference[0]
    if df2 is None or len(df2)==0 or df2.datedifference[0] is None:
        dateDif = 0
    else:
        dateDif = df2.datedifference[0]    
    if suma+dateDif ==0:
        dic["paquetesPorMinuto"] =  0
        dic["tiempoOf"] = 0
    else:        
        dic["tiempoOf"] = dateDif+suma
        dic["paquetesPorMinuto"] = dic["paquetes"]/(dateDif+suma)

def calcPalletPerTurn(df, df2, df3, ofs, dic, pesos):
     
    if pesos is None or len(pesos)==0 or pesos.unidades_e[0] is None or pesos.unidades_e[0] <=0 :
        unidades = 1         
    else:
        unidades= pesos.unidades_e[0]
    if len(df)==0:
        pallet = 0
    else:
        pallet = df.numero[0]    
    if len(ofs)==0:
        cajas = 0
    else:
        cajas = ofs.caja[0] *unidades
    
    if cajas == 0 or pallet ==0:
        dic["paqueteMinRealOfTurno"] = 0
        return
    if len(df2)==0 or df2.datedifference[0] is None:
        dateDif1 = 0
    else:
        dateDif1 = df2.datedifference[0]    
    if len(df3)==0 or df3.datedifference[0] is None:
        dateDif2 = 0
    else:
        dateDif2 = df3.datedifference[0]    
    if dateDif1 == 0 and dateDif2 == 0:
        dic["paqueteMinRealOfTurno"] = 0
        return
    dic["paqueteMinRealOfTurno"]  = pallet * cajas / (dateDif1 + dateDif2)
def calcoverweight(pesos, dic):
    if pesos is None or len(pesos)==0:
        pesoNeto = 0
    else:
        pesoNeto = pesos.peso_neto_e[0] *1000  
    if pesos is None or len(pesos)==0 or pesos.unidades_e[0] is None or pesos.unidades_e[0] <=0 :
        unidades = 1         
    else:
        unidades= pesos.unidades_e[0]
    pesoTotal = pesoNeto/unidades    
    if pesoTotal == 0:
        dic["sobrepeso"]= 0
    else:
        dic["sobrepeso"]= (dic["pesomedio"] - pesoTotal)/ pesoTotal *100       

def ScadaPackageCal(df, df2, id_scada, dic, dbPost, of):
    dbSql = SqlServerConnDB("scada")
    sumaPaquetes = 0
    sumaPeso = 0
    sumaPromedio = 0
    cont = 0
    for index, row in df.iterrows():
            paquetesScada = dbPost.selectScadaDateValuesSum(row["fecha_ini"], row["fecha_fin"], id_scada , of)
            if paquetesScada is not None and paquetesScada.paquetes[0] is not None:
                sumaPaquetes = sumaPaquetes + paquetesScada.paquetes[0]
                sumaPeso = sumaPeso + paquetesScada.peso[0]
                sumaPromedio = sumaPromedio + paquetesScada.pesomedio[0]
                cont = cont +1    
    for index, row in df2.iterrows():
            paquetesScada = dbPost.selectScadaDateValuesSum(row["fecha_ini"], row["fecha_fin"], id_scada, of )
            if paquetesScada is not None and paquetesScada.paquetes[0] is not None:
                sumaPaquetes = sumaPaquetes + paquetesScada.paquetes[0]
                sumaPeso = sumaPeso + paquetesScada.peso[0]
                sumaPromedio = sumaPromedio + paquetesScada.pesomedio[0]
                cont = cont +1
    dic["paquetes"] = int(sumaPaquetes)
    if cont == 0:
        dic["pesomedio"] = 0
    else :
        dic["pesomedio"] = float((sumaPromedio/cont)*1000)  

def insertDataKpiPerMinuteSql(dict, of, turn, date):
    dfoki = db.selectData("kpi_of","dataframe", "id", ofid = of, turno = turn, fecha_kpi = date.strftime("%Y-%m-%d"))
    if len(dfoki)>0 and dfoki.id[0] is not None:
        db.modifyMultiple("kpi_of", "id", dfoki.id[0], paquetes = dict["paquetes"], 
        pesomedio = dict["pesomedio"], sobrepeso = dict["sobrepeso"], 
        paqueteMinRealOfTurno= dict["paqueteMinRealOfTurno"], tiempoOf = dict["tiempoOf"], 
        paquetesPorMinuto = dict["paquetesPorMinuto"], fecha = date.strftime("%Y-%m-%d %H:%M:%S"))            
    else:
        db.insert("kpi_of", "(ofid, turno, fecha_kpi, paquetes, pesomedio, sobrepeso, paqueteMinRealOfTurno, tiempoOf, paquetesPorMinuto )", 
        "({}, {}, '{}', {}, {}, {}, {}, {}, {} )".format(of, turn, date.strftime("%Y-%m-%d"), 
        dict["paquetes"], dict["pesomedio"], dict["sobrepeso"], dict["paqueteMinRealOfTurno"], dict["tiempoOf"], dict["paquetesPorMinuto"] ))

def recolectarDatosScadaFuncion(actOfs):
    dic = {}    
    ofs = db.selectOfsFin('model, o.cajas as caja', 'ofs', 'id', actOfs, "dataframe")    
    dbPost = PostgreeConnDB("BonnysaDB")
    dbMysqlCom = MysqlConnDB("Comer")
    dbMysqlCom.connectDB() 
    now = datetime.now()
    hora = now.strftime("%H:%M:%S")
    turnoActual = dbPost.selectTurnoActualFecha(hora, "tuple")
    fecha =pd.Timestamp(turnoActual[0][3])
    fecha = fecha.to_pydatetime(fecha).strftime("%Y-%m-%d")  
    #Calcular Paquetes por Minuto
    fechaTurno = str(fecha)+" "+str(turnoActual[0][2])
    recolecMinutosFin = dbPost.selectScadaDate(actOfs, turnoActual[0][1], fechaTurno)
    recolecMinutosCurso = dbPost.selectScadaDateRun(actOfs, turnoActual[0][1], fechaTurno)
    paquetesEscada = None
    if len(recolecMinutosFin)==0 or recolecMinutosFin.id_scada[0] is None:
        dic["paquetesPorMinuto"] = 0
        dic["paquetes"] = 0
        dic["tiempoOf"] = 0
        dic["pesomedio"]= 0        
    else:
        controltiemposScada = dbPost.selectScadaDates(actOfs, turnoActual[0][1], fechaTurno )
        controltiemposScadaNow = dbPost.selectScadaDatesNow(actOfs, turnoActual[0][1], fechaTurno)
        ScadaPackageCal(controltiemposScada, controltiemposScadaNow, recolecMinutosFin.id_scada[0], dic, dbPost, actOfs)               
        calcPackagePerMinute(recolecMinutosFin, recolecMinutosCurso, dic)
    #PALETS
    pesos = dbMysqlCom.selectData("frf_envases","dataframe", "peso_neto_e", "unidades_e", ENVASE_E = ofs.model[0] ) 

    datosPalet = dbPost.selectMaxDatePallet(actOfs, turnoActual[0][1], fechaTurno)
    if len(datosPalet)==0 or datosPalet.fechamaxima[0] == None:
        dic["paqueteMinRealOfTurno"] = 0
    else:
        recolecMinutosFinpalet = dbPost.selectScadaDatePalet(actOfs, turnoActual[0][1], datosPalet.fechamaxima[0], fechaTurno) 
        recolecMinutosFinpaletIni = dbPost.selectScadaDateRunPalet(actOfs, turnoActual[0][1], datosPalet.fechamaxima[0], fechaTurno)        
        calcPalletPerTurn(datosPalet, recolecMinutosFinpalet, recolecMinutosFinpaletIni, ofs, dic, pesos )         
    calcoverweight(pesos, dic)
    dic["ofs"] = 1
    print(dic)
    #insertDataKpiPerMinuteSql(dic,actOfs, turnoActual[0][1], now )    
    return dic       
    
@app.route('/recolectarDatosScada', methods=['GET'])
def recolectarDatosScada():
    dic= {}
    ip = "'"+str(request.remote_addr)+"'"
    result = db.select('*', 'devices', 'ip', ip,"dataframe")
    idip = str(result.iloc[0][0])
    actOfs = db.select('*', 'activeof', 'deviceid', idip,"dataframe")    
    if (len(actOfs)==0):
        dic["ofs"] = 0
    else:
        dic =  recolectarDatosScadaFuncion(actOfs.ofid[0])        
    return dic

@app.route("/recolectarDatosKpi/<int:ofid>")
def recolectarDatosKpi(ofid):     
    datos = db.selectKpiSumByOf(ofid)    
    jsonResult = json.dumps(datos.to_dict('records'))   
    return jsonResult

@app.route('/recolectarDatosKpiOf', methods=['GET'])
def recolectarDatosKpiOf():     
    activeOf = db.selectKpiLinea()    
    jsonResult = json.dumps(activeOf.to_dict('records'))   
    return jsonResult

@app.route('/kpi', methods=['GET'])
def kpi():  
    return render_template("kpi_aofs.html", url_asig = getURLIp()) 

@app.route('/kpiOfs', methods=['GET'])
def kpiOfs():  
    return render_template("kpi_ofs.html", url_asig = getURLIp())     

@app.route('/recolectarDatos', methods=['GET'])
def recolectarDatos():         
    dic= {}
    ip = "'"+str(request.remote_addr)+"'"
    result = db.select('*', 'devices', 'ip', ip,"dataframe")
    idip = str(result.iloc[0][0])
    actOfs = db.select('*', 'activeof', 'deviceid', idip,"dataframe")
    if (len(actOfs)==0):
        dic["ofs"] = 0
        return dic
    ofs = db.selectOfsFin('*', 'ofs', 'id', actOfs.ofid[0], "dataframe")
    aWork = db.selectTimeWork(actOfs.ofid[0], "dataframe")    
    paquetes = dbLake.selectPaqueteMinuto('*', ofs.model[0], ofs.linea[0])
    dbMysqlCom = MysqlConnDB("Comer")
    dbMysqlCom.connectDB()
    pesos = dbMysqlCom.selectData("frf_envases","dataframe", "peso_neto_e", "unidades_e", ENVASE_E = ofs.model[0] )
    if pesos is None or len(pesos)==0:
        pesoNeto = 0
    else:
        pesoNeto = pesos.peso_neto_e[0] *1000  
    if len(pesos)==0 or pesos.unidades_e[0] is None or pesos.unidades_e[0] <=0 :
        unidades = 1         
    else:
        unidades= pesos.unidades_e[0]           
    pesadas = dbMetller.selectPesadas(actOfs.ofid[0], aWork.fecha_maxima[0], pesoNeto)
    if (len(pesadas)==0 ):
        pesadaPaquetes = 0
        pesadaMedio = 0
        pesadaPeso = 0
    else:
        if (pesadas.paquetes[0]==0):
            pesadaPaquetes = 0
            pesadaMedio = 0
            pesadaPeso = 0
        else:
            pesadaPaquetes = pesadas.paquetes[0]
            pesadaMedio = pesadas.peso_medio[0]
            pesadaPeso = pesadas.peso[0]
    dic["paquetes"] =float (ofs.iloc[0][18]* unidades * ofs.originalquantity[0])
    dic["ofs"] = 1
    dic["pesoPaquete"] = float(pesoNeto / unidades)
    dic["paqueteMinimoTeorico"] =  float(0 if len(paquetes)==0 else paquetes.media[0])
    dic["paquetesHechos"] =  float(pesadaPaquetes)
    dic["pesoMedioPaquete"] =  float(pesadaMedio)
    if pesoNeto == 0:
        dic["porPesoMedioPaquete"] = 0
    else:
        dic["porPesoMedioPaquete"] = float((pesadaPeso*100/(pesoNeto / unidades))-100)
    dic["tiempoMarchaOf"] =  float (0 if len(aWork)==0 else aWork.minutos_calculo[0] )
    dic["paqMinOf"] = float(pesoNeto / dic["tiempoMarchaOf"])
    dic["porRealizado"] = float(pesoNeto *100 / dic["paquetes"])
    if (dic["paqMinOf"] ==0):
        dic["tiempoRestante"] = 0
    else:
        dic["tiempoRestante"] = float(((dic["paquetes"]- pesoNeto /(dic["paqMinOf"])/60)))    
    jsonResult = json.dumps(dic)   
    return jsonResult
    
if __name__ == '__main__':
            
    app.run(host= datosIni["ip"]["host"], port=datosIni["ip"]["port"], debug= False)
    #app.run()
