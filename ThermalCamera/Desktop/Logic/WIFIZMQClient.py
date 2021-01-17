
import Logic
import time
import zmq
import json
import numpy as np
import threading
import cv2
import base64

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

	def __init__(self, configs):
		try:
			self.logger = Logic.GetLogger()
			self.__app_ip_address__ = ""
			self.__sub__ = {}
			self.__imgSub__ = {}
			self.__pub__ = None
			self.__message__ = None
			self.__zmq_ctx__ = None
			self.IPList = []
			self.OnDataRcvCallback = None
			th = threading.Thread(target=self.Process)
			th.start()
			th = threading.Thread(target=self.ProcessImages)
			th.start()
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

	def ConnectSubscriber(self, IP):
		"""
		This Subscribes to all topics
		"""
		if IP in self.IPList:
			return

		context = zmq.Context()
		self.__sub__[IP] = context.socket(zmq.SUB)
		self.__sub__[IP].setsockopt(zmq.SUBSCRIBE, b'')
		self.__sub__[IP].connect("tcp://"+IP+":6060")
		
		self.__imgSub__[IP] = context.socket(zmq.SUB)
		self.__imgSub__[IP].setsockopt(zmq.SUBSCRIBE, b'')
		self.__imgSub__[IP].connect("tcp://"+IP+":7070")
		time.sleep(2)
		self.IPList.append(IP)


	def ConnectPubSocket(self, app_ip):
		if app_ip in self.IPCamStreamList:
			IPAddr = 0
			if 'eth' in self.IPAddresses and self.IPAddresses['eth'][0] != 0:
				IPAddr = self.IPAddresses['eth'][0]
			elif 'wifi' in self.IPAddresses and self.IPAddresses['wifi'][0] != 0:
				IPAddr = self.IPAddresses['wifi'][0]
			else:
				print("No Ethernet or WIFI Connection Found")
				exit()
			self.SendMessage("@" + IPAddr)
			return

		self.IPCamStreamList.append(app_ip)
		print("Node Discovery Packet Recieved from ", app_ip)

		pub_ip = "tcp://"+ app_ip +":5050"
		if self.__pub__ != None:
			#New IP ADDRESS is different from the prev EIP IP ADDRESS
			self.__pub__.disconnect(pub_ip)
			self.__pub__.close()
			self.__pub__ = None
			self.__app_ip_address__ = ""

		if self.__pub__ == None:
			try:
			#Connect to the given IP ADDRESS
				self.__app_ip_address__ = app_ip
				context = zmq.Context()
				self.__pub__ = context.socket(zmq.PUB)
				self.__pub__.connect(pub_ip)
				time.sleep(2)
			except:
				print('ZMQ LIB Import Error')

	def DisconnectPubSocket(self, address):
		pub_ip = "tcp://"+ address +":6669"
		if self.__pub__ != None:
			#New IP ADDRESS is different from the prev EIP IP ADDRESS
			self.__pub__.disconnect(pub_ip)
			self.__pub__.close()
			self.__pub__ = None
			self.__app_ip_address__ = ""
			
	def SendMessage(self, data):
		if self.__pub__ == None:
			return
		self.__pub__.send_string(data)

	def ProcessRcvdData(self, data):
		json_load = json.loads(data)
		mlxFrame = np.asarray(json_load['data'])
		ip_addr = json_load['IP']
		#Logic.GetFaceRecognizer().StartProcessingStreamSource(ip_addr)
		Logic.GetFaceRecognizer().SetTempratureFrame(ip_addr, mlxFrame)

	def ProcessImages(self):
		while True:
			if self.__sub__ == None:
				return
			dic = self.__imgSub__.copy()	
			for socket in dic:
				try:
					raw_msg = dic[socket].recv(flags=zmq.NOBLOCK, copy=True)
					if len(raw_msg) > 0:
						json_load = json.loads(raw_msg)
						image = np.asarray(json_load['image'])
						jpg_original = base64.b64decode(image)
						jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
						img = cv2.imdecode(jpg_as_np, flags=1)
						Logic.GetFaceRecognizer().AddFrameFromSource(img, socket)
					else:
						pass
				except zmq.ZMQError as e:
					if e.errno == zmq.EAGAIN:
						pass
					else:
						self.logger.log(self.logger.ERROR, "ZMQ Socket ERROR")
				time.sleep(10/1000)

	def Process(self):
		while True:
			if self.__sub__ == None:
				return
			dic = self.__sub__.copy()
			for socket in dic:
				try:
					raw_msg = dic[socket].recv(flags=zmq.NOBLOCK, copy=True)
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
				time.sleep(20/1000)
				