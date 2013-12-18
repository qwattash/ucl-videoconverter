#!/usr/bin/python

"""
storeage access helpers used to hide the filesystem organization
to processing functions and provide simple access
@author qwattash (Alfredo Mazzinghi)
@license MIT
"""
from django.conf import settings

import os
import shlex
import shutil

"""
Data storage directory hierarchy
<directory name="data_root" desc="top data directory">
  <directory name="user_id#1" desc="top user data directory">
    <file name="md5(resource_file).ext" desc="user uploaded resource">
    <directory name="md5(resource_file)_data" desc="processing data for file resource_file">
    </directory>
  </directory>
  <directory name="user_id#2">
  </directory>
</directory>
"""

class ResourceData(object):

    def __init__(self, resource_name):
        self._name = resource_name
        root, ext = os.path.splitext(self._name)
        data_dir = root + "_data"
        self._root_data = data_dir

    def removeProcessingData(self):
        """
        remove all processingdata and directories related to
        given resource (usually resource is a video path).
        the storage format assumed is explained above
        """
        #check for destination dir
        if os.path.isdir(self._root_data):
            shutil.rmtree(self._root_data)
        os.mkdir(self._root_data)

    def getLogFile(self, log_name):
        """
        create log file for given log_name
        return file handle for the log file
        """
        log_dir = os.path.join(self._root_data, 'log')
        if not os.path.isdir(log_dir):
            os.mkdir(log_dir)
        log_full_name = os.path.join(log_dir, log_name + '.log')
        log_fd = os.open(log_full_name, os.O_RDWR | os.O_CREAT)
        hlog = os.fdopen(log_fd, "rw+")
        return hlog

    def joinPath(self, path):
        return os.path.join(self._root_data, path)

    def getOutputFiles(self):
        output = []
        for f in os.listdir(self._root_data):
            if not os.path.isdir(f):
                root, ext = os.path.splitext(f)
                if ext == ".ply":
                   output.append(f)
        return output
    
    def getURLOutputPath(self):
        #full = self.getOutputPath()
        full = os.path.join(self._root_data, "result.obj")
        #make it relative to STATIC_URL
        return os.path.relpath(full, os.path.commonprefix([full, settings.MEDIA_ROOT]))

    def getOutputPath(self):
        output = self.getOutputFiles()
        #get file with the biggest point cloud
        vertexnum = [] #vertex num for each file in output
        max_idx = 0
        for idx in range(0, len(output)):
            name = output[idx]
            try:
                fd = open(self.joinPath(name), 'r')
                hdr = PlyHeader(fd)
                fd.close()
                vertexnum.append(hdr.elements["vertex"].number)
                if vertexnum[idx] > vertexnum[max_idx]:
                    max_idx = idx
            except IOError as e:
                #error opening file
                raise e
            except Exception as e:
                #error in PlyHeader
                raise e
        ##
        return os.path.join(self._root_data, output[max_idx])

class PlyHeader(object):

    PLY_SIGNATURE = "ply"
    PLY_TYPES = {}
    
    class _Element(object):
        
        def __init__(self, number):
            self.number = int(number)
            self.properties = {}

    class _Property(object):
        
        def __init__(self, tp):
            self.type = tp
    
    """
    data must be a file-like object to be parsed
    """
    def __init__(self, data):
        signature = data.readline().rstrip()
        if signature != PlyHeader.PLY_SIGNATURE:
            raise Exception("invalid PLY")
        #instance variables
        #for each element store the name and a tuple (num_of_elements, prototype)
        self.elements = {}
        #store format string defined by the header (bin, endianness, ascii)
        self.format = ""
        #parse header line by line
        line = data.readline().rstrip()
        #element currently parsed
        current_element = None
        while line != "":
            #parse fromat
            tokens = line.split(" ") 
            if tokens[0] == "format":
                self.format = tokens[1]
            elif tokens[0] == "element":
                current_element = tokens[1]
                self.elements[tokens[1]] = PlyHeader._Element(tokens[2]) 
                #(num_elements, {properties})
            elif tokens[0] == "property":
                self.elements[current_element].properties[tokens[2]] = PlyHeader._Property(tokens[1])
            elif tokens[0] == "end_header":
                break
            else:
                raise Exception("unrecognized token")
            line = data.readline().rstrip()
