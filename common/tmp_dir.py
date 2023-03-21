import os
import pathlib

from conf.config import get_conf


class TmpDir(object):
    """A temporary directory that is deleted when the object is destroyed.
    """

    tmpFilePath = pathlib.Path('./tmp/')

    def __init__(self):
        pathExists = os.path.exists(self.tmpFilePath)
        if not pathExists and get_conf('speech_recognition') == True:
            os.makedirs(self.tmpFilePath)

    def path(self):
        return str(self.tmpFilePath) + '/'
