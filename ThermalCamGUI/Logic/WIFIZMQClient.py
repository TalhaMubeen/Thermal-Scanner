from enum import Flag
import Logic
import time
import zmq
from netifaces import interfaces, ifaddresses, AF_INET
import json
import numpy as np
import winreg as wr
import threading
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

	def get_connection_name_from_guid(self, iface_guids):
		#iface_names = ['(unknown)' for i in range(len(iface_guids))]
		iface_names = '(unknown)'# for i in range(len(iface_guids))]
		reg = wr.ConnectRegistry(None, wr.HKEY_LOCAL_MACHINE)
		reg_key = wr.OpenKey(reg, r'SYSTEM\CurrentControlSet\Control\Network\{4d36e972-e325-11ce-bfc1-08002be10318}')
		#for i in range(len(iface_guids)):
		try:
			reg_subkey = wr.OpenKey(reg_key, iface_guids + r'\Connection')
			iface_names = wr.QueryValueEx(reg_subkey, 'Name')[0]
		except FileNotFoundError:
			pass
		return iface_names

	def GetMYIPAddress(self):
		my_ip = {}
		addresses = '0'
		#Ethernet
		for ifaceName in interfaces():
			x = self.get_connection_name_from_guid(ifaceName)
			if "Ethernet" not in (x):
				continue
			addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
			my_ip['eth'] = addresses

		addresses = '0'
		#Wi-Fi
		for ifaceName in interfaces():
			x = self.get_connection_name_from_guid(ifaceName)
			if "Wi-Fi" not in (x):
				continue
			addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
			my_ip['wifi'] = addresses

		return my_ip

	def __init__(self, configs):
		try:
			self.IPAddresses = self.GetMYIPAddress()
			self.logger = Logic.GetLogger()
			self.__app_ip_address__ = ""
			self.__sub__ = None
			self.__pub__ = None
			self.__message__ = None
			self.__zmq_ctx__ = None
			self.IPCamStreamList = []
			#Binding Subscriber to generic socket
			self.__ConnectSubscriber__()
			self.OnDataRcvCallback = None
			th = threading.Thread(target=self.Process)
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

	def __ConnectSubscriber__(self):
		"""
		This Subscribes to all topics
		"""
		context = zmq.Context()
		self.__sub__ = context.socket(zmq.SUB)
		self.__sub__.setsockopt(zmq.SUBSCRIBE, b'')
		self.__sub__.bind("tcp://*:6666")
		time.sleep(2)

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

		pub_ip = "tcp://"+ app_ip +":6669"
		if self.__pub__ != None:
			#New IP ADDRESS is different from the prev EIP IP ADDRESS
			self.__pub__.disconnect(pub_ip)
			self.__pub__.close()
			self.__pub__ = None
			self.__app_ip_address__ = ""

		if self.__pub__ == None:
			#Connect to the given IP ADDRESS
			self.__app_ip_address__ = app_ip
			context = zmq.Context()
			self.__pub__ = context.socket(zmq.PUB)
			self.__pub__.connect(pub_ip)
			time.sleep(2)

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
		Logic.GetFaceRecognizer().StartProcessingStreamSource(ip_addr)
		Logic.GetFaceRecognizer().SetTempratureFrame(ip_addr, mlxFrame)

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
				