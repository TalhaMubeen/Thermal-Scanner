import socket
import threading
import Logic
import json
import numpy as np
from datetime import datetime

class UDPClientProcessor(object):
    __instance__ = None
    """
    UDP Packets Processor
    """

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    def __init__(self, configs):
        try:
            self.logger     = Logic.GetLogger()
            self.Data_Port = 4000 
            self.data_udp_server = None            
            self.StartClient()
            self.clientStreams = []

            th2 = threading.Thread(target=self.DataProcess)
            th2.daemon = True
            th2.start()

            if UDPClientProcessor.__instance__ is None:
                UDPClientProcessor.__instance__ = self
            self.logger.log(self.logger.INFO,'INIT SUCCESSFULLY ')
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ' )
            raise ValueError()
        pass

    def StartClient(self):
        self.data_udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.data_udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.data_udp_server.bind(('', self.Data_Port))

    @staticmethod
    def Instance():
        """ Static method to fetch the current instance.
        """
        return UDPClientProcessor.__instance__

    def DataProcess(self):
        while True:
            try:
                if self.data_udp_server is not None:
                    data, addr = self.data_udp_server.recvfrom(1024)
                    Logic.GetZMQClient().ConnectPubSocket(addr[0])
            except:
                    pass
