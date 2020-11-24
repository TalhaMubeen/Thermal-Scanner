# __init__.py
from .UDPClient import UDPClient
from .Diagnostics import LocalLogger
from .RepeatedTimer import PeriodicTimer
from .VideoRecorder import VideoRecorder
from .MLXReader import MLXReader

def GetUDPClient():
    return UDPClient.Instance()

def GetMLXReader():
    return MLXReader.Instance()

def GetVideoRecorder():
    return VideoRecorder.Instance()

def GetVideoRecordingProcessor():
    return VideoRecordingProcessor.Instance()

def GetLogger():
    return LocalLogger.Instance()
