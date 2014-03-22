from django.conf import settings

from sfmmanager.models import *
from sfmmanager.storage_utils import ResourceData

import shutil
import os
import re

"""
configuration file class
represent the config file as a dictionary and makes modification easy
save and load are supported by this class
"""
class Config(dict):
    
    """
    srcpath is the path to the config file to read
    dstpath is the path of the config file to write
    """
    def __init__(self, srcpath, dstpath):
        self.src = srcpath
        self.dst = dstpath
        
    """
    load configuration from src
    """
    def load(self):
        conf = open(self.src, "r")
        conf.seek(0)
        while True:
            line = conf.readline()
            if not line:
                break
            # parse line
            # if is comment skip it
            if line[0] != "#" and line != "\n":
                # get key value pair in the skeleton
                match = re.search('([A-Za-z0-9_-]+)[ \t]+([\.0-9A-Za-z "\'-]*)', line.rstrip())
                self[match.group(1)] = match.group(2)
        conf.close()
    
    def save(self):
        conf = open(self.dst, "w+")
        conf.seek(0)
        for key,value in self.items():
            conf.write("{0} {1}\n".format(key, value))
"""
Handles the generation of configuration files for our third party programs
based on a template config file and the parameters stored in the database
"""
class ConfigFactory(object):

    # path to the template conf files relative to MEDIA_ROOT
    SKELETON_PATH = "conf/"
    # vsfm conf path
    # this may become an entry in django settings
    VSFM_CONF_PATH = "/home/azureuser/workspace/vsfm/vsfm/bin/nv.ini"

    def __init__(self, video):
        res = ResourceData(video.data.url)
        self.video = video
        self.temp_path = res.joinPath("conf")
        if not os.path.exists(self.temp_path):
            os.makedirs(self.temp_path)
        self.skel_path = os.path.join(settings.MEDIA_ROOT, ConfigFactory.SKELETON_PATH)

    """
    build visualSFM config file for given video
    """
    def buildVsfmConf(self):
        conf_file = os.path.join(self.temp_path, "nv.ini")
        skel_file = os.path.join(self.skel_path, "vsfm.skel")
        # read skeleton conf
        conf = Config(skel_file, conf_file)
        conf.load()
        # get video parameters
        params = Parameter.objects.filter(vid=self.video)
        # now for each parameter find the location in the file to be modified
        # and apply the parameter
        for p in params:
            if conf.has_key(p.name):
                conf[p.name] = p.value
        # save conf file
        conf.save()
        return conf_file

    def deployVsfmConf(self, path):
        # remove current ini
        if os.path.exists(ConfigFactory.VSFM_CONF_PATH):
            os.remove(ConfigFactory.VSFM_CONF_PATH)
        shutil.copy(path, ConfigFactory.VSFM_CONF_PATH)
