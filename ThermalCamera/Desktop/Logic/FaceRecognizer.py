
import threading
import Logic
import datetime
import numpy as np
import time
import cv2
import io
import os
import webbrowser
import sys
import winsound
from multiprocessing import Process
from PIL import Image

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
            # self.StreamThread = threading.Thread(target=self.get_concat_h_multi_blank)
            # self.StreamThread.daemon = True
            # self.StreamThread.start()
            self.BeepStarted = False
            self.im_list = {}
            self.sourcesList = []
            self.openBrowser = 0
            self.PauseStream = False
            self.detector = cv2.dnn.readNetFromCaffe(path+"deploy.prototxt", path + "face_300x300.caffemodel")
            self.TempFrame = {}
            self.imageFrame = {}
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
    
    def StartBeep(self):
        frequency = 2500  # Set Frequency To 2500 Hertz
        duration = 200  # Set Duration To 1000 ms == 2 second
        #winsound.Beep(frequency, duration) 
        winsound.Beep(frequency + 500, duration + 100 ) 
        winsound.Beep(frequency + 1000, duration + 200 )      
        self.BeepStarted = False

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

    def SetTempratureFrame(self, source, tempFrame):
        if source not in self.IPCamStreamList:
            return
        frame = np.flipud(tempFrame.reshape((24, 32)))
        frame = cv2.flip(frame, 0)
        #FIXING ANY GARBAGE DATA
        frame[frame < 0] = 30
        frame[frame > 60] = 30
        self.TempFrame[source] = frame.copy()

    def get_concat_h_blank(self, im1, im2, color=(0, 0, 0)):
        dst = Image.new('RGB', (im1.width + im2.width, max(im1.height, im2.height)), color)
        dst.paste(im1, (0, 0))
        dst.paste(im2, (im1.width, 0))
        return dst

    def get_concat_h_multi_blank(self):
        while True:
            try:
                byteArr = []
                if len(self.im_list) > 0 and self.PauseStream is False:
                    _im = self.im_list[self.sourcesList[0]].copy()
                    for index in range(len(self.sourcesList)):
                        if index == 0:
                            continue
                        im = self.im_list[self.sourcesList[index]].copy()
                        _im = self.get_concat_h_blank(_im, im)
                    byteIO = io.BytesIO()
                    im_np = np.asarray(_im)
                    ret, buffer = cv2.imencode('.jpg', im_np)
                    if ret:
                        self.StreamWritter.write(buffer.tobytes())
                        time.sleep(5/1000)
                else:
                    time.sleep(10/1000)
            except:
                pass

    def AddFrameFromSource(self, frame, source):
        self.imageFrame[source] = frame
        if source not in self.IPCamStreamList:
            self.sourcesList.append(source)
            th = threading.Thread(target=self.StartProcessingFeed, args=(source,))
            th.daemon = True
            th.start()
            self.IPCamStreamList[source] = th

    def ProcessFrame(self, frame, mlxframe, detections, source):
        (h, w) = frame.shape[:2]
        index = []
        #loop over data, where we have a possible face confidence
        data = np.where(detections[0, 0, 0:detections.shape[2], 2] > self.confidence)
        # loop over the detections
        for i in range(0, len(data[0])):
            # compute the (x, y)-coordinates of the bounding box for
            # the face
            box = detections[0, 0, data[0][i], 3:7] * np.array([w, h, w, h])
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
                    return
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
                return

            if meanTemp < 38.1:
                cv2.rectangle(frame, (startX, startY), (endX, endY),(0, 255, 0), 2)
                y = startY - 10 if startY - 10 > 10 else startY + 10
                cv2.putText(frame, "TEMP : " + str(meanTemp)+ "C", (startX, y),cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)
            else:
                cv2.rectangle(frame, (startX, startY), (endX, endY),(0, 0, 255), 2)
                y = startY - 10 if startY - 10 > 10 else startY + 10
                cv2.putText(frame, "TEMP : " + str(meanTemp) + "C", (startX, y),cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
                path = self.__get_image_dir_filePath__()
                timestr = time.strftime("%Y%m%d-%H%M%S")

                if self.BeepStarted is False:
                    self.BeepStarted = True
                    beepThread = threading.Timer(0.1, self.StartBeep)
                    beepThread.daemon = True
                    beepThread.start()

                cv2.imwrite(path+ timestr + ".jpeg", frame)

        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            self.StreamWritter.write(buffer.tobytes())
            # im_pil = Image.fromarray(frame)
            # self.im_list[source] = im_pil

    def StartProcessingFeed(self, source):
        frame = None
        mlxframe = None
        IPSource = source
        self.openBrowser = False
        try:
            while True:
                if IPSource in self.TempFrame:
                    mlxframe = self.TempFrame[IPSource].copy()
                if len(self.imageFrame) == 0:
                    time.sleep(10/1000)
                    continue
                if source not in self.imageFrame:
                    time.sleep(10/1000)
                    continue
                if self.imageFrame[source].shape[1] != 640 :
                    time.sleep(10/1000)
                    continue
                frame = self.imageFrame[source].copy()
                (h, w) = frame.shape[:2]

                # construct a blob from the image
                imageBlob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300),(104.0, 177.0, 123.0), swapRB=False, crop=False)
                self.detector.setInput(imageBlob)
                detections = self.detector.forward()

                #loop over the detections
                th = threading.Thread(target=self.ProcessFrame, args=(frame, mlxframe, detections, source,))
                th.daemon = True
                th.start()

                if self.openBrowser == False:
                    print("Opening Web Browser for Thermal Camera Stream")
                    webbrowser.open('http://localhost:8000')                  
                    self.openBrowser = True
                time.sleep(20/1000)
        except:
            pass