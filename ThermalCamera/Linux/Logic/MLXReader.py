import Logic
import board
import busio
import numpy as np
import mlx.mlx90640 as mlx
from scipy import ndimage
import threading
import time


class MLXReader(object):
    __instance__ = None

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    @staticmethod
    def Instance():
        """ Static method to fetch the current instance.
        """
        return MLXReader.__instance__  

    def __init__(self):
        self.mlxDev = mlx.Mlx9064x(hw='I2C-1', frame_rate=32)
        self.mlxDev.set_m_fEmissivity(0.965)
        self.mlxDev.init()
        th = threading.Thread(target=self.run)
        th.daemon = True
        th.start()
        if MLXReader.__instance__ is None:
            MLXReader.__instance__ = self

    def run(self):
        frame = [0] * 768
        while True:
            try:
                frame = self.mlxDev.read_frame()  
                f = self.mlxDev.do_compensation(frame) 
                Logic.GetZMQClient().SendMessage(f)
                #Logic.GetUDPClient().SendMessage(f)
            except:
                continue #Frame not ready yet!
            time.sleep(1/30)