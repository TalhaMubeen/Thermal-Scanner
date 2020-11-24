import Logic
import time
import picamera
import datetime
import os
import io
import socketserver
from threading import Condition
import threading
from http import server
from PIL import Image as PILImage
import numpy

class VideoRecorder(object):
    class StreamingOutput(object):
        def __init__(self):
            self.frame = None
            self.buffer = io.BytesIO()
            self.condition = Condition()

        def write(self, buf):
            if buf.startswith(b'\xff\xd8'):
                # New frame, copy the existing buffer's content and notify all
                # clients it's available
                self.buffer.truncate()
                with self.condition:
                    self.frame = self.buffer.getvalue()
                    self.condition.notify_all()
                self.buffer.seek(0)
            return self.buffer.write(buf)

    class StreamingHandler(server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(301)
                self.send_header('Location', '/index.html')
                self.end_headers()
            elif self.path == '/index.html':
                content = Logic.GetVideoRecorder().PAGE.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', len(content))
                self.end_headers()
                self.wfile.write(content)
            elif self.path == '/stream.mjpg':
                self.send_response(200)
                self.send_header('Age', 0)
                self.send_header('Cache-Control', 'no-cache, private')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
                self.end_headers()
                try:
                    videoRecorderInstance = Logic.GetVideoRecorder()
                    while True:
                        try:
                            with videoRecorderInstance.output.condition:
                                videoRecorderInstance.output.condition.wait()
                                frame = videoRecorderInstance.output.frame
                                
                                self.wfile.write(b'--FRAME\r\n')
                                self.send_header('Content-Type', 'image/jpeg')
                                self.send_header('Content-Length', len(frame))
                                self.end_headers()
                                self.wfile.write(frame)
                                self.wfile.write(b'\r\n')
                        except:
                            self.wfile.write(b'--FRAME\r\n')
                            self.send_header('Content-Type', 'image/jpeg')
                            self.send_header('Content-Length', len(frame))
                            self.end_headers()
                            self.wfile.write(frame)
                            self.wfile.write(b'\r\n')
                            pass
                except:
                    pass
            else:
                self.send_error(404)
                self.end_headers()

    class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
        allow_reuse_address = True
        daemon_threads = True

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    __instance__ = None
    @staticmethod
    def Instance():
        """ Static method to fetch the current instance.
        """
        return VideoRecorder.__instance__

    def __init__(self, configs):
        try:
            self.PAGE="""\
                    <html>
                    <head>
                    <title>Thermal Camera</title>
                    </head>
                    <body>
                    <center><h1>#</h1></center>
                    <center><img src="stream.mjpg" width="640" height="480"></center>
                    </body>
                    </html>
                    """ 

            self.logger     = Logic.GetLogger()
            self.__config__     = configs['ThermalCam']
            self.MY_ID	= configs['ThermalCam']['MY_ID']
            self.resolution_width  = self.__config__['Recording']['Resolution_Width']
            self.resolution_height = self.__config__['Recording']['Resolution_Height']
            self.recordingTimeout  = self.__config__['Recording']['Recording_Timeout']
            self.framesPerSecond   = self.__config__['Recording']['FramePerSecond']
            self.rotation   	   = self.__config__['Recording']['Rotation']
            self.__StreamingServer__ = None
            try:
                self.__picam__  = picamera.PiCamera()
                self.__picam__.rotation = self.rotation
                self.__picam__.resolution = (self.resolution_width , self.resolution_height)
                #self.__picam__.framerate  = self.framesPerSecond
                self.__picam__.hflip 	  = True
            except :
                self.__picam__ = None
                self.logger.log(self.logger.ERROR, 'Failed to Init PI Camera | Camera not Detected or Already in use')

            self.default_images_dir = configs['ThermalCam']['DIAGNOSTICS']['IMAGE_LOG_PATH']
            self.default_videos_dir = configs['ThermalCam']['DIAGNOSTICS']['VIDEO_LOG_PATH']
            self.output = self.StreamingOutput()
            self.__StreamVideo__ = threading.Thread(target=self.StartStreamOverIP)
            self.__StreamVideo__.start()
            if VideoRecorder.__instance__ is None:
                VideoRecorder.__instance__ = self
            self.logger.log(self.logger.INFO,'INIT SUCCESSFULLY ')
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ')
            raise ValueError()
        pass

    def Process(self):
        return
        # if self.__StreamVideo__.is_running:
        #     pass
        # else:
        #     self.__StreamVideo__.restart()
        #     self.__StreamVideo__.is_running = True

    def StopStream(self):
        try:
            if self.__is_streaming__ == False:
                pass
            else:
                self.__picam__.stop_recording(splitter_port=2)
                self.__is_streaming__ = False
                self.__StreamingServer__.shutdown()
                self.__StreamingServer__ = None
                self.logger.log(self.logger.INFO,'Streaming Server Stopped Successfully')
        except:
            pass

    def StartStreamOverIP(self):
        while True:
            if self.__picam__ != None:
                self.__picam__.start_recording(self.output, splitter_port=2, format = 'mjpeg')
                try:
                    address = ('', 8000)
                    self.PAGE = self.PAGE.replace("#",self.MY_ID )
                    self.__StreamingServer__ = self.StreamingServer(address, self.StreamingHandler)
                    self.logger.log(self.logger.INFO,'Streaming Server Started Successfully')
                    self.__StreamVideo__.is_running = True
                    self.__StreamingServer__.serve_forever()
                except:
                    self.StopStream()
                    self.__StreamVideo__.is_running = False
                    self.logger.log(self.logger.ERROR,'Failed To Start Streaming Server')