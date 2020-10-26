import Logic
import board
import busio
import numpy as np
import adafruit_mlx90640
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
        self.OnHeatMapCallback = None
        self.RefreshRate = adafruit_mlx90640.RefreshRate.REFRESH_8_HZ
        self.mlx_interp_value = 10
        self.mlx_shape = (32,24) # mlx90640 shape
        self.mlx_interp_shape = (self.mlx_shape[0]*self.mlx_interp_value, self.mlx_shape[1]*self.mlx_interp_value) # new shape
        if MLXReader.__instance__ is None:
            MLXReader.__instance__ = self

    def RegisterThermalFrameCallback(self, func):
        self.OnHeatMapCallback = func
        threading.Thread(target=self.run).start()

    def run(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        mlx = adafruit_mlx90640.MLX90640(i2c)
        mlx.refresh_rate = self.RefreshRate
        frame = [0] * 768

        while True:
            try:
                mlx.getFrame(frame)

                amb = [0]*834
                mlx._GetFrameData(amb)
                amb = mlx._GetTa(amb) - 8.0  # this is ambient temp in Centigrade
                amb = round(amb,1) # ambient temp in C, rounded to 1 decimal
                


            except ValueError:
                continue #Frame not ready yet!

            data_array = np.fliplr(np.reshape(frame,self.mlx_shape)) # reshape, flip data
            data_array[data_array < 0] = 25
            #data_array = ndimage.zoom(data_array,self.mlx_interp_value) # interpolate
            if self.OnHeatMapCallback is not None:
                self.OnHeatMapCallback(data_array)
            time.sleep(100/1000)