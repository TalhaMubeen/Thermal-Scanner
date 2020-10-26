# __init__.py
from .UDPClient import UDPClient
from .Diagnostics import LocalLogger
from .RepeatedTimer import PeriodicTimer
from .VideoRecorder import VideoRecorder
from .WIFIZMQClient import WIFIZMQClient
from .MLXReader import MLXReader
#from .ZMQDataProcessor import ZMQDataProcessor

def GetUDPClient():
    return UDPClient.Instance()

def GetMLXReader():
    return MLXReader.Instance()

def GetZMQClient():
    return WIFIZMQClient.Instance()

def GetVideoRecorder():
    return VideoRecorder.Instance()

#def GeZMQDataProcessor():
#    return ZMQDataProcessor.Instance()

def GetVideoRecordingProcessor():
    return VideoRecordingProcessor.Instance()

def GetLogger():
    return LocalLogger.Instance()
