from typing import Any
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from config.loadData import readJson
from pdf2image import convert_from_path
class ImageConverterPdf:
    def __init__(self) -> Any:
        self.datosIni = readJson()
        
    def TransformImage(self, path, filename, linea):        
        poppler_path = r"C:\po\poppler\bin" 
        images = convert_from_path(path+filename,poppler_path=poppler_path)
        for i in range(len(images)):        
            images[i].save(path+'IMG'+ linea +"_"+ str(i)+'.jpg', 'JPEG')