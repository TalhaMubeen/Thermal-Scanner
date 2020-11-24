# import the necessary packages
from os import name
import threading

from numpy.lib.utils import source
import Logic
import datetime
import numpy as np
import imutils
import time
import cv2
import io
import os
import webbrowser
import sys
class FaceRecognizer(object):
    __instance__ = None

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)   

    def __init__(self, configs):
        try:
            print("Loading Models...")
            self.logger     = Logic.GetLogger()
            self.confidence = 0.5
            cwd = os.getcwd()
            self.__Image_Dir__  = cwd + configs['ThermalCam']['DIAGNOSTICS']['IMAGE_LOG_PATH']
            baseDirectory = "Logic\\face_detection_model\\"
            path = self.resource_path(baseDirectory)


            self.detector = cv2.dnn.readNetFromCaffe(path+"deploy.prototxt", path + "face_300x300.caffemodel")
            self.TempFrame = {}
            self.imageFrame = None
            self.ByteBuffer = io.BytesIO()
            self.IPCamStreamList = {}
            self.StreamWritter = Logic.GetStreamHandler().StreamWriter
            print("Models Loaded Successfully")
            print("Searching For Thermal Camera")
            if FaceRecognizer.__instance__ is None:
                FaceRecognizer.__instance__ = self
            self.logger.log(self.logger.INFO,'INIT SUCCESSFULLY ')
        except:
            print("Failed To Load Models")
            self.logger.log(self.logger.ERROR, 'Failed to Init ' )
            raise ValueError()
        pass

    def __get_image_dir_filePath__(self):
        currDate = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        if not os.path.exists(self.__Image_Dir__ + currDate):
            os.makedirs(self.__Image_Dir__ + currDate)

        datePath = self.__Image_Dir__ + currDate + "\\"
        return datePath

    @staticmethod
    def Instance():
        """ Static method to fetch the current instance.
        """
        return FaceRecognizer.__instance__

    def StartProcessingStreamSource(self, source):
        if source in self.IPCamStreamList:
            return
        else:
            th = threading.Thread(target=self.StreamReader, args=(source,))
            th.daemon = True
            th.start()
            self.IPCamStreamList[source] = th

    def SetTempratureFrame(self, source, tempFrame):
        if source not in self.IPCamStreamList:
            return
        frame = np.flipud(tempFrame.reshape((24, 32)))
        frame = cv2.flip(frame, 0)
        #FIXING ANY GARBAGE DATA
        frame[frame < 0] = 30
        frame[frame > 60] = 30
        self.TempFrame[source] = frame.copy()
    
    def StreamReader(self, ip_src):
        streamThread = threading.Thread(target=self.StartProcessingFeed, args=(ip_src,))
        try:
            print("Starting Thermal Camera Stream from source", ip_src)
            url = "http://"+ip_src +":8000/stream.mjpg"
            vs = cv2.VideoCapture(url)
            vs.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            print("Is Camera Stream Availiable?",vs.isOpened())
            time.sleep(3)
            streamThread.daemon = True
            streamThread.name = ip_src
            streamThread.start()
            self.logger.log(self.logger.INFO, 'Starting Stream For Camera IP ' + ip_src )
            count = 20
            while True:
                ret, frame = vs.read()
                if ret:
                    frame= frame[:380, :550]
                    frame= imutils.resize(frame, width=640)
                    self.imageFrame = frame
                else:
                    count = count -1
                    if count <= 0:
                        vs.release()
                        print("Releasing Resources for Thermal Camera ",streamThread.name)
                        del(self.IPCamStreamList[streamThread.name])
                        del(self.TempFrame[streamThread.name])
                        Logic.GetZMQClient().DisconnectPubSocket(streamThread.name)
                        streamThread.join()
                        self.logger.log(self.logger.ERROR, 'Stream For Camera IP ' + streamThread.name + ' Stopped' )
                        break
        except: 
            print("Releasing Resources for Thermal Camera ",streamThread.name)
            del(self.IPCamStreamList[streamThread.name])
            del(self.TempFrame[streamThread.name])   
            streamThread.join() 
            self.logger.log(self.logger.ERROR, 'Stream For Camera IP ' + streamThread.name + ' Stopped' ) 
            pass

    def StartProcessingFeed(self, source):
        frame = None
        mlxframe = None
        IPSource = source
        openBrowser = False
        try:
            while True:
                if self.TempFrame[IPSource] is not None:
                    mlxframe = self.TempFrame[IPSource].copy()
                # grab the frame from the threaded video stream
                #frame = self.imageFrame.copy()
                if self.imageFrame is None or self.imageFrame.shape[1] != 640 :
                    continue
                frame = self.imageFrame.copy()
                (h, w) = frame.shape[:2]

                # construct a blob from the image
                imageBlob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300),(104.0, 177.0, 123.0), swapRB=False, crop=False)

                # apply OpenCV's deep learning-based face detector to localize
                # faces in the input image
                self.detector.setInput(imageBlob)
                detections = self.detector.forward()

                #loop over the detections
                for i in range(0, detections.shape[2]):
                    # extract the confidence (i.e., probability) associated with
                    # the prediction
                    confidence = detections[0, 0, i, 2]

                    # filter out weak detections
                    if confidence > self.confidence:
                        # compute the (x, y)-coordinates of the bounding box for
                        # the face
                        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                        (startX, startY, endX, endY) = box.astype("int")
                        #Remapping image to MLX Frame
                        tempsx = int((startX)  / 20) 
                        tempsy = int((startY) / 20) 
                        tempex = int((endX)  / 20)
                        tempey = int((endY) / 20) 
                        maxTemp = 0
                        meanTemp = 0

                        if mlxframe is not None:
                            temp = mlxframe[tempsy:tempey, tempsx:tempex]
                            if temp.size == 0:
                                continue
                            maxTemp = np.max(temp)
                            maxTemp = maxTemp / 0.96
                            meanTemp = round(maxTemp, 1)
                            tempPercentage = ((meanTemp/37.6) * 100)
                            if tempPercentage < 98.5:
                                div = (1 - ((97.5 - tempPercentage)/100))
                                maxTemp = maxTemp / div
                                meanTemp = round(maxTemp, 1)
                        
                        # extract the face ROI
                        face = frame[startY:endY, startX:endX]
                        (fH, fW) = face.shape[:2]
                        
                        # ensure the face width and height are sufficiently large
                        if fW < 10 or fH < 10 or fW > 250 or fH > 250:
                            continue

                        if meanTemp < 37.6:
                            cv2.rectangle(frame, (startX, startY), (endX, endY),(0, 255, 0), 2)
                            y = startY - 10 if startY - 10 > 10 else startY + 10
                            cv2.putText(frame, "TEMP : " + str(meanTemp)+ "C", (startX, y),cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)
                        else:
                            cv2.rectangle(frame, (startX, startY), (endX, endY),(0, 0, 255), 2)
                            y = startY - 10 if startY - 10 > 10 else startY + 10
                            cv2.putText(frame, "TEMP : " + str(meanTemp) + "C", (startX, y),cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
                            path = self.__get_image_dir_filePath__()
                            timestr = time.strftime("%Y%m%d-%H%M%S")
                            cv2.imwrite(path+ timestr + ".jpeg", frame)
                    else:
                        pass
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    self.StreamWritter.write(buffer.tobytes())
                if openBrowser == False:
                    print("Opening Web Browser for Thermal Camera Stream")
                    webbrowser.open('http://localhost:8000')
                    
                    openBrowser = True
        except:
            pass