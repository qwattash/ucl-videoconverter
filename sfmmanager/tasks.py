#!/usr/bin/python

"""
celery tasks for this django application
@author qwattash (Alfredo Mazzinghi)
@license MIT
"""

from __future__ import absolute_import

from celery import shared_task, task

from sfmmanager.models import *
from sfmmanager.storage_utils import *

import os
import subprocess
import shlex

"""
extract frames from the video using ffmpeg
@todo
add tunable parametes for
i) number of frames in output changing -r arg
"""
@shared_task
def extractFrames(vid):
    #get video instance
    video = Video.objects.get(pk=vid)
    params = Parameter.objects.get(vid=video)
    #update status to working
    video.status = Video.STATUS_EXTRACT_FRAMES
    video.save()
    try:
        resource = ResourceData(video.data.url)
        resource.removeProcessingData()
        #create logfile
        log = resource.getLogFile("ffmpeg")
        output_path = resource.joinPath("frame%d.jpg")
        # if a parameter is not existing, filter().value will throw an exception since None.value
        # is not permitted; this will in turn cause the error state to be captured
        num_extract_fps = params.filter(name=Param.PARAM_NUM_FRAMES).value
        command = "ffmpeg -i %s -r %d %s" % (video.data.url, num_extract_fps, output_path)
        args = shlex.split(command)
        print args
        extractor = subprocess.Popen(args,
                                     stdout=log, 
                                     stderr=log, 
                                     stdin=None)
        extractor.wait()
        log.close()
        if extractor.returncode != 0:
            raise Exception('ffmpeg terminated incorrectly') 
    except Exception as e:
        video.status = Video.STATUS_ERROR
        video.save()
    return vid

"""
process frames, call visualSFM to do the job
@todo 
add tunable parameters for
i) vsfm config file
ii) vsfm reconstruction type (sfm, sfm+cmvs, sfm+pmvs)
"""
@shared_task
def processFrames(vid):
    #get video model
    video = Video.objects.get(pk=vid)
    #check for errors
    if video.status == Video.STATUS_ERROR:
        return vid
    #update status
    video.status = Video.STATUS_WORKING
    video.save()
    try:
        resource = ResourceData(video.data.url)
        #get log file for vsfm
        log = resource.getLogFile("vsfm")
        output_path = resource.joinPath("vsfm.nvm")
        input_path = resource.joinPath("")
        command = "vsfm sfm+pmvs %s %s" % (input_path, output_path)
        args = shlex.split(command)
        print args
        vsfm = subprocess.Popen(args,
                                stdin=None,
                                stdout=log,
                                stderr=log)
        vsfm.wait()
        log.close()
        if vsfm.returncode != 0:
            raise Exception('vsfm terminated incorrectly')
    except:
        video.status = Video.STATUS_ERROR
        video.save()
    return vid

"""
process output from processFrame
convert nvm or ply into some unity format
http://www.cs.princeton.edu/~min/meshconv/
"""
@shared_task
def processOutput(vid):
    #merge all ply files in a single ply
    video = Video.objects.get(pk=vid)
    #check for errors
    if video.status == Video.STATUS_ERROR:
        return vid
    #update status
    video.status = Video.STATUS_CONVERTING_OUTPUT
    video.save()
    resource = ResourceData(video.data.url)
    plyoutput = resource.getVsfmOutput()
    if not plyoutput:
        video.status = Video.STATUS_ERROR
        video.save()
        return vid
    objoutput = resource.joinPath("result.obj")
    try:
        #get log file for vsfm
        log = resource.getLogFile("meshlab")
        command = "meshlabserver -i %s -o %s -om vc vn" % (plyoutput, objoutput)
        args = shlex.split(command)
        print args
        meshlab = subprocess.Popen(args,
                                stdin=None,
                                stdout=log,
                                stderr=log)
        meshlab.wait()
        log.close()
        if meshlab.returncode != 0:
            raise Exception('meshlabserver terminated incorrectly')
        video.status = Video.STATUS_RECONSTRUCTED
        video.save()
    except:
        video.status = Video.STATUS_ERROR
        video.save()
    return vid

@shared_task
def deleteProcessingData(vid):
    #get video instance
    video = Video.objects.get(pk=vid)
    #remove direcotry data
    resource = ResourceData(video.data.url)
    resource.removeProcessingData()
    video.status = Video.STATUS_PENDING
    video.save()
    return vid

@shared_task
def debugTask(vid):
    print "DISPLAY = %s" % os.getenv('DISPLAY', None)
    return True
