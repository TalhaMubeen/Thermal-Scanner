import Logic
import time
import zmq
import threading
import json
import subprocess as sp
from ast import literal_eval

TOTAL_DOTS_IN_IPADDRESS  = 3

class WIFIZMQClient(object):
	"""
	This class is responsible to eastablish zmq communication 
	"""

	def whoami(self):
		"""
		returns the class name as string
		"""
		return type(self).__name__

	__instance__ = None
	@staticmethod
	def Instance():
		""" 
		Static method to fetch the current instance.
		"""
		return WIFIZMQClient.__instance__

	def __init__(self):
		try:
			self.logger = Logic.GetLogger()
			self.__app_ip_address__ = ""
			self.__sub__ = None
			self.__pub__ = None
			self.__message__ = None
			self.__zmq_ctx__ = None
			self.sendData = False
			context = zmq.Context()
			self.__pub__ = context.socket(zmq.PUB)
			self.__pub__.bind("tcp://*:6060")

			self.__pubImg__ = None
			self.__pubImg__ = context.socket(zmq.PUB)
			self.__pubImg__.bind("tcp://*:7070")

			time.sleep(2)
			self.sendData = True
			#Binding Subscriber to generic socket
			self.__ConnectSubscriber__()
			self.OnDataRcvCallback = None
			#th = threading.Thread(target=self.Process)
			#th.daemon = True
			#th.start()
			#Setting Static Object
			if WIFIZMQClient.__instance__ is None:
				WIFIZMQClient.__instance__ = self
			self.logger.log(self.logger.INFO,'INIT SUCCESSFULLY ')
		except:
			self.logger.log(self.logger.ERROR, 'Failed to Init ' )
			raise ValueError()
		pass

	def SetZMQDataRcvCallback(self, callback):
		self.OnDataRcvCallback = callback

	def __ConnectSubscriber__(self):
		"""
		This Subscribes to all topics
		"""
		context = zmq.Context()
		self.__sub__ = context.socket(zmq.SUB)
		self.__sub__.setsockopt(zmq.SUBSCRIBE, b'')
		self.__sub__.bind("tcp://*:5050")
		time.sleep(2)

	# def __ConnectPubSocket__(self, app_ip):
	# 	pub_ip = "tcp://"+ app_ip +":6666"
	# 	if self.__pub__ != None:
	# 		#New IP ADDRESS is different from the prev EIP IP ADDRESS
	# 		self.__pub__.disconnect(pub_ip)
	# 		self.__pub__.close()
	# 		self.__pub__ = None
	# 		self.__app_ip_address__ = ""
	# 		self.sendData = False
	# 	if self.__pub__ == None:
	# 		#Connect to the given IP ADDRESS
	# 		self.__app_ip_address__ = app_ip
	# 		context = zmq.Context()
	# 		self.__pub__ = context.socket(zmq.PUB)
	# 		self.__pub__.bind("tcp://*:6666")
	# 		time.sleep(2)
	# 		self.sendData = True

	def GetSystemCmdOutput(self, cmd):
		ret = sp.check_output(cmd, shell=True, universal_newlines=True)
		ret = ret.replace('\n', '')
		return ret

	def SendImageData(self, image):
		if self.__pubImg__ == None and self.sendData is False:
			return	

		WLanIPAddress = self.GetSystemCmdOutput("ifconfig wlan0 | awk '$1 == \"inet\" {print $2}'")
		EthIPAddress = self.GetSystemCmdOutput("ifconfig eth0 | awk '$1 == \"inet\" {print $2}'")
		IPAddress = ""
		sendMessage = False

		if EthIPAddress.count(".") == TOTAL_DOTS_IN_IPADDRESS:
			IPAddress = EthIPAddress
			sendMessage = True

		elif WLanIPAddress.count(".") == TOTAL_DOTS_IN_IPADDRESS:
			IPAddress = WLanIPAddress
			sendMessage = True

		if sendMessage is True:
			try:	
				datastr = json.dumps({"image": image, "IP":IPAddress})
				self.__pubImg__.send_string(datastr)
			except:
				pass

	def SendMessage(self, data):
		if self.__pub__ == None and self.sendData is False:
			return

		WLanIPAddress = self.GetSystemCmdOutput("ifconfig wlan0 | awk '$1 == \"inet\" {print $2}'")
		EthIPAddress = self.GetSystemCmdOutput("ifconfig eth0 | awk '$1 == \"inet\" {print $2}'")
		IPAddress = ""
		sendMessage = False

		if EthIPAddress.count(".") == TOTAL_DOTS_IN_IPADDRESS:
			IPAddress = EthIPAddress
			sendMessage = True

		elif WLanIPAddress.count(".") == TOTAL_DOTS_IN_IPADDRESS:
			IPAddress = WLanIPAddress
			sendMessage = True

		if sendMessage == True:
			datastr = json.dumps({"data": data, "IP":IPAddress})
			try:
				self.__pub__.send_string(datastr)
			except:
				pass

	# # def ProcessRcvdData(self, str_data):
	# 	#str_data = data.decode("utf-8") 
	# 	if str_data.count('@') > 0: # we recieved EIP IP Address
	# 		app_ip_address = str_data.replace('@', '')
	# 		Logic.GetUDPClient().SetAPPIPAddress(app_ip_address)

	# 		if self.__app_ip_address__ != app_ip_address:
	# 			#Eastablishing Publish Socket using EIP IP ADDRESS
	# 			self.__ConnectPubSocket__(app_ip_address)

	# 		else:
	# 			# do nothing we have already eastblished socket with current EIP IP ADDRESS
	# 			pass
	# 	else:
	# 		pass
	# 		#self.OnDataRcvCallback(data)

	def Process(self):
		while True:
			if self.__sub__ == None:
				return
			try:
				raw_msg = self.__sub__.recv_string(flags=zmq.NOBLOCK)
				if len(raw_msg) > 0:
					#raw_msg = raw_msg.replace('\n', '')
					self.ProcessRcvdData(raw_msg)
				else:
					pass
			except zmq.ZMQError as e:
				if e.errno == zmq.EAGAIN:
					pass
				else:
					self.logger.log(self.logger.ERROR, "ZMQ Socket ERROR")
			time.sleep(10/1000)
				