# import os
# import math
# import time
# import numpy as np
# from PIL import Image
# import imutils
# import cv2
# from scipy import ndimage

# mlx_shape = (32,24) # mlx90640 shape
# mlx_interp_val = 20 # interpolate # on each dimension
# mlx_interp_shape = (mlx_shape[0]*mlx_interp_val,
#                     mlx_shape[1]*mlx_interp_val) # new shape

# #some utility functions
# def constrain(val, min_val, max_val):
#     maxval = max(min_val, val)
#     return min(max_val,maxval )

# def map_value(x, in_min, in_max, out_min, out_max):
#     return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# def gaussian(x, a, b, c, d=0):
#     return a * math.exp(-(x - b)**2 / (2 * c**2)) + d

# def gradient(x, width, cmap, spread=1):
#     width = float(width)
#     r = sum([gaussian(x, p[1][0], p[0] * width, width/(spread*len(cmap))) for p in cmap])
#     g = sum([gaussian(x, p[1][1], p[0] * width, width/(spread*len(cmap))) for p in cmap])
#     b = sum([gaussian(x, p[1][2], p[0] * width, width/(spread*len(cmap))) for p in cmap])
#     r = int(constrain(r*255, 0, 255))
#     g = int(constrain(g*255, 0, 255))
#     b = int(constrain(b*255, 0, 255))
#     return r, g, b

# class MLXThread(object):
#     #low range of the sensor (this will be black on the screen)
#     MINTEMP = 20.
#     #high range of the sensor (this will be white on the screen)
#     MAXTEMP = 50.
#     #how many color values we can have
#     COLORDEPTH = 1000
#     heatmap = (
#         (0.0, (0, 0, 0)),
#         (0.20, (0, 0, .5)),
#         (0.40, (0, .5, 0)),
#         (0.60, (.5, 0, 0)),
#         (0.80, (.75, .75, 0)),
#         (0.90, (1.0, .75, 0)),
#         (1.00, (1.0, 1.0, 1.0)),
#     )
#     changeHeatmap = None
#     #changeHeatmap = pyqtSignal(np.ndarray)

#     def run(self, frame):
#         # data = [0] * 768
#         # count = 0
#         # for h in range(24):
#         #     for w in range(32):
#         #         data[count] = frame[h*32 + w]
#         #         count = count +1
#         # data  = np.array(data)
#         # frame = data
#         # img = Image.fromarray(data.reshape(32,24), 'L')
#         # img = img.resize((640, 480), Image.BILINEAR)
#         # opencvImage = cv2.cvtColor(np.array(img), cv2.COLOR_GRAY2BGR)
#         # cv2.imshow("Thermal1", opencvImage)
#         # cv2.waitKey(1)

#         colormap = [0] * self.COLORDEPTH
#         for i in range(self.COLORDEPTH):
#             colormap[i] = gradient(i, self.COLORDEPTH, self.heatmap)

#         pixels = [0] * 768
#         for i, pixel in enumerate(frame):
#             coloridx = map_value(pixel, self.MINTEMP, self.MAXTEMP, 160, self.COLORDEPTH - 1)
#             coloridx = int(constrain(coloridx, 160, self.COLORDEPTH-1))
#             pixels[i] = colormap[coloridx]
#         #data_array = ndimage.zoom(frame,mlx_interp_val) # interpolate
#         #data_array = np.resize(pixels,(32,24))
#         #data_array = imutils.resize(pixels, width=32)
#         #img = np.resize(data_array, (640, 480), Image.BILINEAR)
#         img = Image.new('RGB', (32,24))
#         img.putdata(pixels)
#         img = img.resize((640, 480), Image.BILINEAR)
#         opencvImage = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
#         cv2.imshow("Thermal", opencvImage)
#         cv2.waitKey(1)
#         return opencvImage

