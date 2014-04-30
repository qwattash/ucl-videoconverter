"""
@author: qwattash - Alfredo Mazzinghi
@license GPLv2
"""

from django.shortcuts import render, render_to_response
from django.http import HttpResponse, Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.template import RequestContext, loader
from django.conf import settings

##devel
#from django.views.static import serve
##

import hashlib
import random

from sfmmanager.models import *
from sfmmanager.forms import *
from sfmmanager.storage_utils import *
from sfmmanager.task_manager import *

#reserved values for output code fields
REQ_AUTH = "auth"
REQ_DEAUTH = "deauth"
REQ_DEL = "delete"
REQ_STATUS = "status"
REQ_JOB = "job"
REQ_REG = "register"
REQ_DOWNLOAD = "download"
REQ_RERUN = "rerun"
REQ_CONF = "config"
RES_SUCCESS = "success"
RES_FAILURE = "failure"

#status codes
STATUS = {'1': 'reconstructed',
          '2': 'pending',
          '3': 'error',
          '4': 'forbidden',
          '5': 'unknown',
          '6': 'extracting_frames',
          '7': 'working',
          '8': 'converting_output'}

"""
Handle generic requests 
"""
def index(request):
    #allow only specific resources to be accessed
    raise Http404

"""
Generic response building functions
"""
def buildResponseMessage(request, request_code, response_code, msg):
    template = loader.get_template('sfmmanager/response.xml')
    uname = ''
    if request.user.is_authenticated():
        uname = request.user.username
    context = RequestContext(request, {
                        'uname': uname,
                        'req': request_code,
                        'req_params': '',
                        'code': response_code,
                        'payload': [msg]
                })
    return HttpResponse(template.render(context))

def buildResponseList(request, request_code, response_code, payload_list):
    template = loader.get_template('sfmmanager/response.xml')
    uname = ''
    if request.user.is_authenticated():
        uname = request.user.username
    context = RequestContext(request, {
                        'uname': uname,
                        'req': request_code,
                        'req_params': '',
                        'code': response_code,
                        'list_payload': payload_list
                })
    return HttpResponse(template.render(context))

"""
authenticate an user, begin a new session and return a status
Message Format
<get>
<param type='string'>uname</param>
<param type='string'>password</param>
</get>
"""
def auth(request):
    uname = request.GET.get("uname", None)
    pwd = request.GET.get("password", None)
    if uname == None or pwd == None:
        #invalid parameter passed, return error
        return buildResponseMessage(request, REQ_AUTH, RES_FAILURE, "Invalid request format")
    else:
        #extract user row from database
        user = authenticate(username=uname, password=pwd)
        if user != None:
            #passwod and user correct
            if user.is_active:
                #valid account
                login(request, user)
                return buildResponseMessage(request, REQ_AUTH, RES_SUCCESS, "authentication succeded")    
            else:
                #account disabled
                return buildResponseMessage(request, REQ_AUTH, RES_FAILURE, "Account banned")
        else:
            #invalid username or password
            return buildResponseMessage(request, REQ_AUTH, RES_FAILURE, "Invalid username or password")


"""
create new user account using the django authentication module
the request should include the following fields in a GET request
uname: username
password: the password that wants to use
<get>
<param type='string'>uname</param>
<param type='string'>password</param>
<param type='string'>email</param>
</get>
"""
def register(request):
    #first of all check that an user with the same name does not exist
    name = request.GET.get('uname', None)
    try:
        user = User.objects.get(username=name)
        #if the user does not exist an exception is raised
        #if the user exists go on
        return buildResponseMessage(request, REQ_REG, RES_FAILURE, "Account with same name already exists")
    except User.DoesNotExist:
        #register new user
        pwd = request.GET.get('password', None)
        email = request.GET.get('email', None)
        if (name and pwd):
            User.objects.create_user(name, email, pwd)
            user = authenticate(username=name, password=pwd)
            login(request, user)
            return buildResponseMessage(request, REQ_REG, RES_SUCCESS, "Registered")
        else:
            #missing some param, error
            return buildResponseMessage(request, REQ_REG, RES_FAILURE, "Missing parameter")

"""
get user status, current queued jobs, working jobs
authentication status etc.
"""
def status(request):
    #session handling makes user available directly in request
    if request.user.is_authenticated():
        jobs = Video.objects.filter(uid=request.user)
        payload = []
        for job in jobs:
            payload.append((STATUS[str(job.status)], job.vname))
        return buildResponseList(request, REQ_STATUS, RES_SUCCESS, payload)
    else:
        return buildResponseMessage(request, REQ_STATUS, RES_FAILURE, "Unauthenticated")

"""
Log out user
"""
def unauth(request):
    if request.user.is_authenticated():
        logout(request)
        return buildResponseMessage(request, REQ_DEAUTH, RES_SUCCESS, "Deauthenticated")
    else:
        return buildResponseMessage(request, REQ_DEAUTH, RES_FAILURE, "Not authenticated")

"""
upload video content
the video must be sent as multipart/form-data with name target
such as
<form action="url" method="POST" encoding="multipart/form-data">
<input type="file" name="target"/>
</form>
""" 
def upload(request):
    if request.user.is_authenticated():
        #check if the user has reached the maximum video count
        #that is allowed to store
        user_videos = Video.objects.filter(uid=request.user)
        #the user_max_files constant is defined in the model
        if len(user_videos) >= USER_MAX_FILES:
            return buildResponseMessage(request, REQ_JOB, RES_FAILURE, "Maximum video upload limit reached")
        elif request.method == "POST":
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                video = Video()
                video.data = request.FILES['target']
                video.uid = request.user
                video.vname = request.FILES['target'].name
                temp_hash = hashlib.md5()
                for chunk in request.FILES['target'].chunks():
                    temp_hash.update(chunk)
                video.vhash = temp_hash.hexdigest()
                #check if video has already been uploaded
                existingData = Video.objects.filter(uid=request.user, 
                                                    vhash=temp_hash.hexdigest())
                existingName = Video.objects.filter(uid=request.user,
                                                    vname=video.vname)
                existing = existingName or existingData
                code = RES_FAILURE
                msg = ''
                if len(existing) > 1:
                    #error
                    msg = 'Unrecoverable Error'
                elif len(existing) == 1:
                    #already existing entry
                    msg = 'Job already exists'
                else:
                    #set response args
                    code = RES_SUCCESS
                    msg = 'Job submitted'
                    #save new entry
                    video.save()
                    resource = ResourceData(video.data.url)
                    #submit task chain to celery worker
                    manager = TaskManager(video.id)
                    manager.run()
                return buildResponseMessage(request, REQ_JOB, code, msg)
            else:
                #form not valid
                return buildResponseMessage(request, REQ_JOB, RES_FAILURE, "Invalid form format")
        else:
            #non POST request
            return buildResponseMessage(request, REQ_JOB, RES_FAILURE, "Invalid request")
    else:
        return buildResponseMessage(request, REQ_JOB, RES_FAILURE, "Unauthenticated")

"""
serve requested file, se apache mod_xsendfile for production use
https://docs.djangoproject.com/en/1.2/howto/static-files/
https://github.com/johnsensible/django-sendfile/tree/master/examples/protected_downloads
"""
def getfile(request):
    if request.user.is_authenticated():
        rname = request.GET.get('name', None)
        try:
            video = Video.objects.filter(vname=rname)[0]
        except IndexError:
            video = None
        if rname and video:
            resource = ResourceData(video.data.url)
            path = resource.getFinalOutputFile()
            if path != None and (str(video.status) == str(Video.STATUS_RECONSTRUCTED)):
                #set http headers required for the download process
                response = HttpResponse(content_type='application/force-download')
                response['Content-Disposition'] = 'attachment; filename=%s.obj' % video.vname
                #make use of the apache mod_xsendfile module
                response['X-Sendfile'] = unicode(path).encode('utf-8')
                return response
            else:
                return buildResponseMessage(request, REQ_DOWNLOAD, RES_FAILURE, "Output not ready or error occurred")
        else:
            return buildResponseMessage(request, REQ_DOWNLOAD, RES_FAILURE, "Resource not existing")
    else:
        return buildResponseMessage(request, REQ_DOWNLOAD, RES_FAILURE, "Unauthenticated")

"""
Retreive specified log file for given video if exists
<get>
<param type='string' name='type'>log type</param>
<param type='string' name='name'>video name</param>
</get>
"""
def getlog(request):
    #check if user is authenticated
    if request.user.is_authenticated():
        rname = request.GET.get('name', None)
        rtype = request.GET.get('type', None)
        try:
            video = Video.objects.filter(vname=rname)[0]
        except IndexError:
            video = None
        if rname and video:
            resource = ResourceData(video.data.url)
            logname, path = resource.getLogPath(rtype)
            if logname != None and path != None:
                #set http headers required for the download process
                response = HttpResponse(content_type='application/force-download')
                response['Content-Disposition'] = 'attachment; filename=%s' % logname
                #make use of the apache mod_xsendfile module
                response['X-Sendfile'] = unicode(path).encode('utf-8')
                return response
            else:
                return buildResponseMessage(request, REQ_DOWNLOAD, RES_FAILURE, "Unexisting log file")
        else:
            return buildResponseMessage(request, REQ_DOWNLOAD, RES_FAILURE, "Resource not existing or not yet ready")
    else:
        return buildResponseMessage(request, REQ_DOWNLOAD, RES_FAILURE, "Unauthenticated")

"""
remove a video and video data associated on the server
<get>
<param type='string'>video name</param>
</get>
"""
def delete(request):
    #check if user is authenticated
    if request.user.is_authenticated():
        rname = request.GET.get('name', None)
        if rname:
            video_objects = Video.objects.filter(vname=rname)
            if (len(video_objects) > 0):
                video = video_objects[0]
                resource = ResourceData(video.data.url)
                #delete video and data
                resource.removeProcessingData()
                params = Parameter.objects.filter(vid=video)
                params.delete()
                video_objects.delete()
                return buildResponseMessage(request, REQ_DEL, RES_SUCCESS, "Deleted")
            else:
                return buildResponseMessage(request, REQ_DEL, RES_FAILURE, "Unexisting video")
        else:
            return buildResponseMessage(request, REQ_DEL, RES_FAILURE, "No name given")
    else:
        return buildResponseMessage(request, REQ_DEL, RES_FAILURE, "Unauthenticated")

"""
rerun the computation for a video that has failed or with new parameters
<get>
<param name='name'>name of the video to rerun</param>
</get>
"""
def rerun(request):
    if request.user.is_authenticated():
        name = request.GET.get('name', None);
        if name:
            videos = Video.objects.filter(vname=name)
            if (len(videos) > 0):
                video = videos[0]
                manager = TaskManager(video.id)
                manager.run()
                return buildResponseMessage(request, REQ_RERUN, RES_SUCCESS, "Rerunning")
            else:
                return buildResponseMessage(request, REQ_RERUN, RES_FAILURE, "Unexisting video")
        else:
            return buildResponseMessage(request, REQ_RERUN, RES_FAILURE, "No name given")
    else:
        return buildResponseMessage(request, REQ_RERUN, RES_FAILURE, "Unauthenticated")

"""
Handle configuration of the video recontruction parameters
<get>
<param name='name'>name of the video to configure</param>
<param name='cmd'>configuration command</param>
<param name='pname'>parameter to modify</param>
<param name='arg'>additional command argument</param> 
</get>
"""
def config(request):
    #check if user is authenticated
    if request.user.is_authenticated():
        # video name
        rname = request.GET.get('name', None)
        # command
        cmd = request.GET.get('cmd', None)
        # param name
        pname = request.GET.get('pname', None)
        # optional argument of the command
        arg = request.GET.get('arg', None)
        if rname and cmd and pname:
            video_objects = Video.objects.filter(vname=rname)
            if (len(video_objects) > 0):
                video = video_objects[0]
                ## check for parameter structure validity
                params = Parameter.objects.filter(vid=video, name=pname)
                if len(params) != 1: 
                    if Parameter.DEFAULTS.get(pname, None):
                        """
                        # there should be only one parameter with name pname for each video
                        # the parameter name should be legit
                        # if one of these does not hold there is an error in the database
                        # recover error, delete all but one parameters with name pname
                        """
                        params.delete()
                        p = Parameter(vid=video, name=pname)
                        p.reset()
                    else:
                        # the parameter given does not exist
                        return buildResponseMessage(request, REQ_CONF, RES_FAILURE, "Invalid parameter")
                # get parameter with name pname for this video
                param = params[0]
                ## now check the commands and perform action for each command
                if cmd == 'set':
                    if param.validate(arg):
                        param.value = arg
                        param.save()
                    else:
                        # the parameter is invalid
                        return buildResponseMessage(request, REQ_CONF, RES_FAILURE, "Illegal parameter value")
                elif cmd == 'reset':
                    param.reset()
                elif cmd == 'get':
                    # the get command is implicitly defined since the response to any command is the
                    # response to a get, this is used to filter valid commands only
                    pass
                else:
                    # command do not exist
                    return buildResponseMessage(request, REQ_CONF, RES_FAILURE, "Invalid command")
                # notify the success of the operation
                return buildResponseMessage(request, REQ_CONF, RES_SUCCESS, 
                                            "Config {0}: {1} = {2}".format(cmd, pname, param.value))
            else:
                return buildResponseMessage(request, REQ_CONF, RES_FAILURE, "Unexisting video")
        else:
            return buildResponseMessage(request, REQ_CONF, RES_FAILURE, "Missing name of video or command")
    else:
        return buildResponseMessage(request, REQ_CONF, RES_FAILURE, "Unauthenticated")

#@####################################################################
# Testing- STUFF
def test(request):
    form = UploadFileForm()
    return render_to_response('sfmmanager/test.html', {'form': form})

def debug(request):
    vds = Video.objects.all()
    r = ""
    for v in vds:
        #pp = ParamNumFPS(vid=v)
        #pp.save()
        params = Parameter.objects.filter(vid=v)
        #params.delete()
        r += "<ul><h3>%s</h3>" % (v.vname,)
        for p in params:
            r += "<li>%s: %s</li>" % (p.name, p.value)
        r += "</ul>"
    return HttpResponse('<p>Debug</p>' + r)
