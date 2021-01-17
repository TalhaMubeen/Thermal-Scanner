print("Loading Logic Modules ...")
from .Diagnostics import LocalLogger
from .UDPClientProcessor import UDPClientProcessor
from .FaceRecognizer import FaceRecognizer
from .StreamHandler import StreamHandler
from .WIFIZMQClient import WIFIZMQClient
print("Logic Loaded Successfully ...")
def GetLogger():
    return LocalLogger.Instance()

def GetUDPClientProcessor():
    return UDPClientProcessor.Instance()

def GetFaceRecognizer():
    return FaceRecognizer.Instance()

def GetStreamHandler():
    return StreamHandler.Instance()

def GetZMQClient():
    return WIFIZMQClient.Instance()