import Logic
import json
import time
import inspect

class TermalCamera(object):

	def whoami(self):
		"""
		returns the class name as string
		"""
		return type(self).__name__

	def LoadConfigurations(self):
		"""Returns configurations json object if loaded correctly else None"""
		try:
			with open("/home/RADA/DEV/Logic/Configurations.json")as config_file:
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
			self.Start()
			self.logger     			= Logic.GetLogger()
			self.logger.log(self.logger.INFO,'INIT SUCCESSFULLY ' )

		except:
			self.logger.log(self.logger.ERROR, 'Failed to Init ' )
		pass

	def Init(self,config):
		Logic.LocalLogger("Diagnostics",config)
		MY_ID = config['ThermalCam']['MY_ID']
		Logic.WIFIZMQClient()
		Logic.UDPClient(config)
		Logic.UDPStreamer()
		#Logic.VideoRecorder(config)
		Logic.MLXReader()
	
	def Start(self):
		pass
		#self.ObjectsToProcess.append(Logic.GetVideoRecorder())

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

	# def Process(self):
	# 	for obj in self.ObjectsToProcess:
	# 		obj.Process()

if __name__ == "__main__":
	try:
		termalCam = TermalCamera()	
		termalCam.EXECUTE()
	except:
		exit("ERROR EXECUTING")
