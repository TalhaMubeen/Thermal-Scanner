import Logic
import time
import picamera
import datetime
import os
import io
import cv2
import socketserver
from threading import Condition
import threading
from http import server
import dlib
from PIL import Image as PILImage
import numpy
import heapq


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
						with videoRecorderInstance.output.condition:
							videoRecorderInstance.output.condition.wait()
							frame = videoRecorderInstance.output.frame
							imagecv = videoRecorderInstance.GetFaceBoundedFrame(frame)
							is_success, im_buf_arr = cv2.imencode(".jpg", imagecv)
							byte_im = im_buf_arr.tobytes()

							self.wfile.write(b'--FRAME\r\n')
							self.send_header('Content-Type', 'image/mjpeg')
							self.send_header('Content-Length', len(byte_im))
							self.end_headers()
							self.wfile.write(byte_im)
							self.wfile.write(b'\r\n')
				except Exception as e:
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
					<title>GateArm Light Monitor</title>
					</head>
					<body>
					<center><h1>#</h1></center>
					<center><img src="stream.mjpg" width="1024" height="1024"></center>
					</body>
					</html>
					""" 
			self.detector 	= dlib.get_frontal_face_detector()
			self.logger     = Logic.GetLogger()
			self.__config__     = configs['ThermalCam']
			self.MY_ID	= configs['ThermalCam']['MY_ID']
			self.lock = threading.Lock()
			self.stream         = io.BytesIO()
			self.resolution_width  = self.__config__['Recording']['Resolution_Width']
			self.resolution_height = self.__config__['Recording']['Resolution_Height']
			self.recordingTimeout  = self.__config__['Recording']['Recording_Timeout']
			self.framesPerSecond   = self.__config__['Recording']['FramePerSecond']
			self.rotation   = self.__config__['Recording']['Rotation']
			try:
				self.__picam__  = picamera.PiCamera()
				self.__picam__.rotation = self.rotation
				self.__picam__.resolution = (self.resolution_width , self.resolution_height)
				self.__picam__.framerate = self.framesPerSecond
			except :
				self.__picam__ = None
				self.logger.log(self.logger.ERROR, 'Failed to Init PI Camera | Camera not Detected or Already in use')

			self.VideoWriter       = None
			self.VideoCapture      = None

			self.default_images_dir = configs['ThermalCam']['DIAGNOSTICS']['IMAGE_LOG_PATH']
			self.default_videos_dir = configs['ThermalCam']['DIAGNOSTICS']['VIDEO_LOG_PATH']
			self.output = self.StreamingOutput()
			self.__StreamVideo__       = Logic.PeriodicTimer(1, self.StartStreamOverIP)
			self.__recordVideo__       = Logic.PeriodicTimer(1, self.StartRecording)
			self.is_recording           = False
			self.__is_streaming__       = False
			self.__last_recorded_file__ = ""
			self.OnFileRecordedCallback = None
			self.ThermalFrame = None
			Logic.GetMLXReader().RegisterThermalFrameCallback(self.OnThermalFrameCallback)
			#Setting Static Instance 
			if VideoRecorder.__instance__ is None:
				VideoRecorder.__instance__ = self
			self.logger.log(self.logger.INFO,'INIT SUCCESSFULLY ')
		except:
			self.logger.log(self.logger.ERROR, 'Failed to Init ')
			raise ValueError()
		pass

	def isRecording(self):
		"""
		function returns True if it's recording any video else False
		"""
		return self.is_recording

	def RegisterFileRecordedCallback(self, callback):
		self.OnFileRecordedCallback = callback

	def stop_recording(self):
		"""
		use this function to stop any ongoing video recording
		"""
		ret = self.is_recording
		if self.is_recording:
			self.is_recording = False   
			self.__picam__.stop_recording(splitter_port=1)
			self.logger.log(self.logger.INFO, 'Video Recording Stopped')
			self.__recordVideo__.stop()
		return ret

	def start_video_recording(self, duration = None):
		"""
		Starts recording video if there is no ongoing recording process going-on
		Records video for next 5-minutes
		"""
		if self.is_recording == False:     
			self.__recordVideo__.restart()
		else:
			self.logger.log(self.logger.ERROR, 'Already Recording a Video File')

	def StartRecording(self):
		if self.is_recording:
			self.logger.log(self.logger.INFO, 'Already Recording a Video')
		elif self.__picam__ == None:
			self.logger.log(self.logger.INFO, 'PI-CAMERA not detected')
		else:
			self.is_recording = True
			fileName = ""
			fileName = self.__get_file_name__(self.default_videos_dir,".h264")
			fileMP4 = fileName.replace('h264', 'mp4')
			self.__last_recorded_file__ = fileName

			dt = datetime.datetime.utcnow().strftime("%b-%d-%Y %H:%M:%S")
			self.logger.log(self.logger.INFO, 'Starting Video Recording, File : ' + fileName) 

			self.__picam__.start_recording(fileName, splitter_port=1)
			self.__picam__.wait_recording(timeout = (self.recordingTimeout*60), splitter_port=1)

			if self.is_recording: # do not stop if stopped by signal already i.e stop_recording is called by external thread
				self.__picam__.stop_recording(splitter_port=1)

			self.logger.log(self.logger.INFO, 'Video Recorded Successfully')

			#Safety check while Converting video from h264 to MP4 so that any other video recording can not be called from external thread
			self.is_recording = True 

			#converting h264 to MP4 with fps info header
			os.system('MP4Box -noprog -add ' + fileName + ' -fps '+ str(self.framesPerSecond)+' '+ fileMP4)

			if os.path.isfile(fileMP4):
				os.remove(fileName)
				self.__last_recorded_file__ = fileMP4
				if self.OnFileRecordedCallback != None:
					self.OnFileRecordedCallback(fileMP4, dt+ ' UTC')
				else:
					self.logger.log(self.logger.ERROR, 'On Video File Recorded Callback Not Registered')
			else:
				self.logger.log(self.logger.ERROR, 'Failed To FIND VIDEO FILE : ' + fileName)   
			self.is_recording = False

	def __get_file_name__(self, directory, extension):
		"""
		Get the filename having complete directory path with current date time
		"""
		currDate = datetime.datetime.utcnow().strftime("%Y-%m-%d")

		#checking if current date directory exists 
		if not os.path.exists(directory + currDate):
			os.makedirs(directory + currDate)
		if extension == '.jpg':
			file = directory + currDate + "/" +  "_IMG_"+str(int(datetime.datetime.utcnow().timestamp())) + extension

		else:
			file = directory + currDate + "/" +  "_VID_"+str(int(datetime.datetime.utcnow().timestamp())) + extension
		return file

	def get_last_recorded_file(self):
		"""
		This function returns the file name and path of last recording done using this module 
		"""
		return self.__last_recorded_file__

	def clear_last_record_name(self):
		"""
		Clears the stored last record file name
		"""
		self.__last_recorded_file__ = ""

	def capture_image(self):
		if self.__picam__ != None:
			filename = self.__get_file_name__(self.default_images_dir, ".jpg")
			self.__picam__.capture(filename, splitter_port=0)
			return filename
		else:
			self.logger.log(self.logger.ERROR, 'PI Camera is not initialized')

	def Process(self):
		if self.__StreamVideo__.is_running:
			pass
		else:
			self.__StreamVideo__.restart()
			self.__StreamVideo__.is_running = True

	def StopStream(self):
		if self.__is_streaming__ == False:
			pass
		else:
			self.__picam__.stop_recording(splitter_port=2)
			self.__is_streaming__ = False
			self.__StreamingServer__.shutdown()
			self.logger.log(self.logger.INFO,'Streaming Server Stopped Successfully')

	def OnThermalFrameCallback(self, thermalFrame):
		self.ThermalFrame = thermalFrame

	def GetFaceBoundedFrame(self, ioframe):
		image = PILImage.open(io.BytesIO(ioframe))
		imagearr = numpy.array(image) 
		imagearr = imagearr[:, :, ::-1].copy() #converting from RGB to BGR format

		gray = cv2.cvtColor(imagearr, cv2.COLOR_BGR2GRAY)
		gray = cv2.resize(gray, dsize=(320, 240), interpolation=cv2.INTER_AREA)

		# Use detector to find landmarks
		faces = self.detector(gray)

		for face in faces:
			with self.lock:
				therm = self.ThermalFrame.copy()
			
			x1 = face.left()   # left point
			y1 = face.top()    # top point
			x2 = face.right()  # right point
			y2 = face.bottom() # bottom point

			tx1 = int(x1 /10)
			ty1 = int(y1 /10)
			tx2 = int(x2 /10)
			ty2 = int(y2 /10)	

			meanTemp = 0
			dist = x2 - x1
			distCOF = int(dist /4)
			if len(therm) ==32:
				temp = therm[int(ty1):int(ty2), int(tx1):int(tx2)]
				meanTemp = numpy.max(temp)
				Fahrenheit = (meanTemp * 9/5) + 32
			x1 = x1*2 + 10
			y1 = y1*2 + 10
			x2 = x2*2 - 10
			y2 = y2*2 - 10
			cv2.putText(imagearr, ' TEMP - ' + str(Fahrenheit), ( x1  , y1 - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
			cv2.rectangle(img=imagearr, pt1=(x1, y1), pt2=(x2, y2), color=(0, 255, 0), thickness=2)

		return imagearr
	
	def StartStreamOverIP(self):
		if self.__picam__ != None:
			self.__picam__.start_recording(self.output, splitter_port=2, format = 'mjpeg')
			try:
				address = ('', 8000)
				self.__is_streaming__ == True
				self.PAGE = self.PAGE.replace("#",self.MY_ID )
				self.__StreamingServer__ = self.StreamingServer(address, self.StreamingHandler)
				self.logger.log(self.logger.INFO,'Streaming Server Started Successfully')
				self.__StreamingServer__.serve_forever()
			except:
				self.logger.log(self.logger.ERROR,'Failed To Start Streaming Server')
		else:
			pass