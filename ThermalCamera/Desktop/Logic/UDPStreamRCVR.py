# from time import sleep
# import Logic
# import cv2
# import numpy as np
# import socket
# import struct
# import threading
# import time

# MAX_DGRAM = 2**17

# class UDPStreamRCVR(object):
#     __instance__ = None

#     def whoami(self):
#         """
#         returns the class name as string
#         """
#         return type(self).__name__ 

#     def __init__(self):
#         try:
#             self.logger     = Logic.GetLogger()
#             threading.Thread(target=self.main).start()
#             if UDPStreamRCVR.__instance__ is None:
#                 UDPStreamRCVR.__instance__ = self
#             self.logger.log(self.logger.INFO,'INIT SUCCESSFULLY ')
#         except:
#             print("Failed To Load Models")
#             self.logger.log(self.logger.ERROR, 'Failed to Init ' )
#             raise ValueError()
#         pass

#     def dump_buffer(self,s):
#         """ Emptying buffer frame """
#         while True:
#             seg, addr = s.recvfrom(MAX_DGRAM)
#             print(seg[0])
#             if struct.unpack("B", seg[0:1])[0] == 1:
#                 print("finish emptying buffer")
#                 break

#     def main(self):
#         """ Getting image udp frame &
#         concate before decode and output image """
        
#         data_udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
#         data_udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#         data_udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         data_udp_server.bind(('', 12345))
#         # Set up socket

#         dat = b''
#         self.dump_buffer(data_udp_server)

#         while True:
#             seg, addr = data_udp_server.recvfrom(MAX_DGRAM)
#             if struct.unpack("B", seg[0:1])[0] > 1:
#                 dat += seg[1:]
#             else:
#                 dat += seg[1:]
#                 if dat.startswith(b'\xff\xd8'):
#                     img = cv2.imdecode(np.fromstring(dat, dtype=np.uint8), 1)
#                     Logic.GetFaceRecognizer().AddFrameFromSource(img, addr[0])
#                 else:
#                     time.sleep(10/1000)
#                 dat = b''

