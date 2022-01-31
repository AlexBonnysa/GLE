import os
import errno
import filecmp
import glob


class DirectoryUtils:
    def __init__(self) -> None:
        pass
    
    def createDirectory(self, path):
        try:
            os.mkdir(path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
    def checkIfFileIstheSame(self, file1, file2):
        return filecmp.cmp(file1, file2, shallow=False)        

    def listFilesInDirectory(self, path) ->list:
        try:
            return glob.glob(path+"/*.jpg")
        except Exception as e:
            return []

    def checkIfFileNameExist(self, pathFileName):
        return os.path.exists(pathFileName)
        

    def deleteFilesInDirectory(self, path):
        files = glob.glob(path+'/*')
        for f in files:
            os.remove(f)
