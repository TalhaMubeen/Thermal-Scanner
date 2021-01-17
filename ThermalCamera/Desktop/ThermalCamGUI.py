print("Starting Thermal Camera Logic")
import Logic
import json
import time
import inspect
import sys
import os

class ThermalCamGUI(object):
    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path) 

    def LoadConfigurations(self):
        """Returns configurations json object if loaded correctly else None"""
        try:
            path = self.resource_path('Logic\\')
            with open(path + "Configurations.json")as config_file:
                data = json.load(config_file)
                return data
        except:
            return {}
        pass

    def __init__(self):
        try:
            self.ObjectsToProcess 		= []
            self.configs                = {}
            self.configs                = self.LoadConfigurations()
            self.Init(config=self.configs)
            self.logger     			= Logic.GetLogger()
            self.logger.log(self.logger.INFO,'INIT SUCCESSFULLY ' )

        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ' )
        pass

    def Init(self,config):
        _Diagnostics = Logic.LocalLogger("Diagnostics",config)

       # MY_ID = config['ThermalCam']['MY_ID']
        Logic.StreamHandler(config)
        Logic.FaceRecognizer(config)
        Logic.UDPClientProcessor(config)
        Logic.WIFIZMQClient(configs=config)

    def EXECUTE(self):
        try:
            while True:
                #self.Process()
                time.sleep(10)
        except:
            stack = inspect.stack()
            the_class = stack[1][0].f_locals["self"].__class__.__name__
            the_method = stack[1][0].f_code.co_name
            self.logger.log(self.logger.ERROR, "Terminating App | Class = " + the_class + " FUNC = "+ the_method )

    def Process(self):
        for obj in self.ObjectsToProcess:
            obj.Process()

if __name__ == "__main__":
    try:
        print("Processing Logic")
        termalCam = ThermalCamGUI()
        termalCam.EXECUTE()
    except:
        time.sleep(100000)
        print("Error Occured")
        exit("ERROR EXECUTING")
