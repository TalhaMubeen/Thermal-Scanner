import Logic
import io
import socketserver
from threading import Condition
import threading
from http import server
import webbrowser

class StreamHandler(object):

    class StreamingOutput(object):
        def __init__(self):
            self.frame = None
            self.buffer = io.BytesIO()
            self.condition = Condition()

        def write(self, buf):
            if buf.startswith(b'\xff\xd8'):
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
                content = Logic.GetStreamHandler().PAGE.encode('utf-8')
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
                    streamer = Logic.GetStreamHandler()
                    while True:
                        try:
                            with streamer.StreamWriter.condition:
                                streamer.StreamWriter.condition.wait()
                                frame = streamer.StreamWriter.frame
 
                                self.wfile.write(b'--FRAME\r\n')
                                self.send_header('Content-Type', 'image/jpeg')
                                self.send_header('Content-Length', len(frame))
                                self.end_headers()
                                self.wfile.write(frame)
                                self.wfile.write(b'\r\n')
                        except:
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
        return StreamHandler.__instance__

    def __init__(self, configs):
        try:
            self.PAGE="""\
                    <html>
                    <head>
                    <title>Thermal Camera</title>
                    </head>
                    <body>
                    <center><h1>Thermal Camera</h1></center>
                    <center><img src="stream.mjpg" width="50%"></center>
                    </body>
                    </html>
                    """ 
            self.StreamWriter = self.StreamingOutput()
            self.logger     = Logic.GetLogger()
            self.__config__ = configs['ThermalCam']
            self.MY_ID	= configs['ThermalCam']['MY_ID']

            threading.Thread(target=self.StartStreamOverIP).start()
            
            if StreamHandler.__instance__ is None:
                StreamHandler.__instance__ = self
            self.logger.log(self.logger.INFO,'INIT SUCCESSFULLY ')
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ' )
            raise ValueError()
        pass


    def StartStreamOverIP(self):
        while True:
            try:
                address = ('', 8000)
                self.__StreamingServer__ = self.StreamingServer(address, self.StreamingHandler)
                self.logger.log(self.logger.INFO,'Streaming Server Started Successfully')
                self.__StreamingServer__.serve_forever()
            except:
                self.logger.log(self.logger.ERROR,'Failed To Start Streaming Server')