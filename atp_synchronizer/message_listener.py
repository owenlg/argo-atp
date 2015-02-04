import logging
import thread
import time

#LOG = logging.getLogger(__name__)

class NullListener:
    def __init__(self):
        pass
        
# Sending     
    def on_connecting(self, host_and_port):
        pass
    def on_send(self, headers, body):
        pass
    def on_disconnected(self, headers, body):
        pass
    
# Receiving
    def on_connected(self, headers, body):
        pass
    def on_receipt(self, headers, body):
        pass
    def on_error(self, headers, body):
        pass
    def on_message(self, headers, body):
        pass
    
class WaitForConnectListener(NullListener):
    """Simple listener which will wait until the connection receives a CONNECTED message"""

    def __init__(self, configuration):
        self.state= 'DISCONNECTED'
        self.__lock = thread.allocate_lock()
        self.body = None
        self.__logger = configuration.logger
        self.messages = []
        
    def on_connecting(self, host_and_port):
        self.__lock.acquire()
        self.__logger.info("Connecting to %s:%s"%host_and_port)
        self.state = 'CONNECTING'
        self.__lock.release()
        
    def on_connected(self, conn_headers, body):
        self.__lock.acquire()
        try:
            self.__logger.info("Connected : %s"%conn_headers)
            self.state = 'CONNECTED'
        finally:
            self.__lock.release()

    def on_disconnected(self, headers, body):
        self.__lock.acquire()
        try:
            self.__logger.info("Connection lost...")
            self.state = 'DISCONNECTED'
            self.body = body
        finally:
            self.__lock.release()

    def on_error(self, headers, body):
        self.__lock.acquire()
        try:
            self.__logger.info("Error : %s"%body)
            self.state = 'ERROR'
            self.body = body
        finally:
            self.__lock.release()

    def is_connected(self):
        self.__lock.acquire()
        try:
            return self.state == 'CONNECTED'
        finally:
            self.__lock.release()
    
    def is_error(self):
        self.__lock.acquire()
        try:
            return self.state == 'ERROR'
        finally:
            self.__lock.release()
            
    def on_message(self, headers, body):
        #print ''.join(body)
        self.__lock.acquire()
        if body !=None and self.state== 'CONNECTED':
            self.messages.append(body)
        self.__lock.release()
            
    
