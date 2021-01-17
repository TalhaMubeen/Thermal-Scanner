import Logic
import cv2
import numpy as np
import socket
import struct
import math
import threading
import time
import base64

class UDPStreamer(object):

    __instance__ = None

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__ 

    def __init__(self):
        try:
            self.logger     = Logic.GetLogger()
            threading.Thread(target=self.main).start()
            if UDPStreamer.__instance__ is None:
                UDPStreamer.__instance__ = self
            self.logger.log(self.logger.INFO,'INIT SUCCESSFULLY ')
        except:
            print("Failed To Load Models")
            self.logger.log(self.logger.ERROR, 'Failed to Init ' )
            raise ValueError()
        pass
    @staticmethod
    def Instance():
        """ Static method to fetch the current instance.
        """
        return UDPStreamer.__instance__

    def main(self):
        """ Top level main function """
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
        cap.set(cv2.CAP_PROP_FPS, 40)
        while (cap.isOpened()):
            ret, frame = cap.read()
            if ret:
                string = base64.b64encode(cv2.imencode('.jpg', frame)[1]).decode()
                Logic.GetZMQClient().SendImageData(string)

            #time.sleep(40/1000)
        cap.release()

