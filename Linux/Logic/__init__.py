# __init__.py
from .UDPClient import UDPClient
from .Diagnostics import LocalLogger
from .VideoRecorder import VideoRecorder
from .MLXReader import MLXReader
from .WIFIZMQClient import WIFIZMQClient

def GetUDPClient():
    return UDPClient.Instance()

def GetMLXReader():
    return MLXReader.Instance()

def GetVideoRecorder():
    return VideoRecorder.Instance()

def GetLogger():
    return LocalLogger.Instance()

def GetZMQClient():
    return WIFIZMQClient.Instance()
