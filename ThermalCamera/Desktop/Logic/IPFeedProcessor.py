import Logic
import cv2

class IPFeedProcessor(object):
    __instance__ = None
    """
    UDP Packets Processor
    """

    def whoami(self):
        """
        returns the class name as string
        """
        return type(self).__name__

    def __init__(self, configs):
        try:
            self.logger     = Logic.GetLogger()

            if IPFeedProcessor.__instance__ is None:
                IPFeedProcessor.__instance__ = self
            
            self.logger.log(self.logger.INFO,'INIT SUCCESSFULLY ')
        except:
            self.logger.log(self.logger.ERROR, 'Failed to Init ' )
            raise ValueError()
        pass

    @staticmethod
    def Instance():
        """ Static method to fetch the current instance.
        """
        return IPFeedProcessor.__instance__

    def StartCameraFeedReading(self, IPAddress):
        
        cv2.VideoCapture("http://"+str(IPAddress)+ ":8000/stream.mjpg")