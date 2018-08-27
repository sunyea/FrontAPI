from configparser import ConfigParser
import os

class CConfig(object):
    def __init__(self, file='Config.ini'):
        self._file = os.path.join(os.path.abspath('.'), file)
        self._conf = ConfigParser()
        self._conf.read(self._file)

    def getServer(self, name):
        return self._conf.get('server', name)

    def getKafka(self, name):
        return self._conf.get('kafka', name)