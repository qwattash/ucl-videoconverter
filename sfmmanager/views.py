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
from django.views.static import serve
##

import hashlib
import random

from sfmmanager.models import *
from sfmmanager.forms import *
from sfmmanager.storage_utils import *

#reserved values for output code fields
REQ_AUTH = "auth"
REQ_DEAUTH = "deauth"
REQ_DEL = "delete"
REQ_STATUS = "status"
REQ_JOB = "job"
REQ_REG = "register"
REQ_DOWNLOAD = "download"
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
    template = loader.get_template('sfmmanager/response.xml')
    if uname == None or pwd == None:
        #invalid parameter passed, return error
        context = RequestContext(request, {
                'uname': '',
                'req': REQ_AUTH,
                'req_params': '',
                'code': RES_FAILURE,
                'payload': ["invalid request format"]
                })
    else:
        #extract user row from database
        user = authenticate(username=uname, password=pwd)
        if user != None:
            #passwod and user correct
            if user.is_active:
                #valid account
                context = RequestContext(request, {
                        'uname': uname,
                        'req': REQ_AUTH,
                        'req_params': '',
                        'code': RES_SUCCESS,
                        'payload': ["authentication succeded"]
                })
                login(request, user)
            else:
                #account disabled
                context = RequestContext(request, {
                        'uname': uname,
                        'req': REQ_AUTH,
                        'req_params': '',
                        'code': RES_FAILURE,
                        'payload': ["account banned"]
                })
        else:
            #invalid username or password
            context = RequestContext(request, {
                'uname': uname,
                'req': REQ_AUTH,
                'req_params': '',
                'code': RES_FAILURE,
                'payload': ["invalid username or password"]
                })
    return HttpResponse(template.render(context))

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
    template = loader.get_template('sfmmanager/response.xml')
    try:
        user = User.objects.get(username=name)
        #if the user does not exist an exception is raised
        #already exixting
        context = RequestContext(request, {
                'uname': name,
                'req': REQ_REG,
                'req_params': '',
                'code': RES_FAILURE,
                'payload': ["Account with same name already exists"]
                })
    except User.DoesNotExist:
        #register new user
        pwd = request.GET.get('password', None)
        email = request.GET.get('email', None)
        if (name and pwd and email):
            user = User.objects.create_user(name, email, pwd)
            context = RequestContext(request, {
                'uname': name,
                'req': REQ_REG,
                'req_params': '',
                'code': RES_SUCCESS,
                'payload': ["registered"]
                })
        else:
            #missing some param, error
            context = RequestContext(request, {
                'uname': name,
                'req': REQ_REG,
                'req_params': '',
                'code': RES_FAILURE,
                'payload': ["missing parameter"]
                })

    return HttpResponse(template.render(context))

"""
get user status, current queued jobs, working jobs
authentication status etc.
"""
def status(request):
    #session handling makes user available directly in request
    template = loader.get_template('sfmmanager/response.xml')
    if request.user.is_authenticated():
        jobs = Video.objects.filter(uid=request.user)
        payload = []
        for job in jobs:
            payload.append((STATUS[str(job.status)], job.vname))
        context = RequestContext(request, 
                                 {'uname': request.user.username,
                                  'req': REQ_STATUS,
                                  'req_params': '',
                                  'code': RES_SUCCESS,
                                  'list_payload': payload
                                  })
    else:
        context = RequestContext(request, 
                                 {'uname': '',
                                  'req': REQ_STATUS,
                                  'req_params': '',
                                  'code': RES_FAILURE,
                                  'payload': ["unauthenticated"]
                                  })
    return HttpResponse(template.render(context))

"""
Log out user
"""
def unauth(request):
    template = loader.get_template('sfmmanager/response.xml')
    if request.user.is_authenticated():
        logout(request)
        context = RequestContext(request, 
                                 {'uname': request.user.username,
                                  'req': REQ_DEAUTH,
                                  'req_params': '',
                                  'code': RES_SUCCESS,
                                  'payload': ["deauthenticated"]
                                  })
    else:
        context = RequestContext(request, 
                                 {'uname': '',
                                  'req': REQ_DEAUTH,
                                  'req_params': '',
                                  'code': RES_FAILURE,
                                  'payload': ["not authenticated"]
                                  })
    return HttpResponse(template.render(context))

"""
upload video content
the video must be sent as multipart/form-data with name target
such as
<form action="url" method="POST" encoding="multipart/form-data">
<input type="file" name="target"/>
</form>
""" 
def upload(request):
    template = loader.get_template('sfmmanager/response.xml')
    if request.user.is_authenticated():
        context_dict = {'uname': request.user.username,
                        'req': REQ_JOB,
                        'req_params': '',
                        'code': RES_FAILURE,
                        'payload': []
                        }
        #check if the user has reached the maximum video count
        #that is allowed to store
        user_videos = Video.objects.filter(uid=request.user)
        #the user_max_files constant is defined in the model
        if len(user_videos) >= USER_MAX_FILES:
            context_dict = {'uname': request.user.username,
                            'req': REQ_JOB,
                            'req_params': '',
                            'code': RES_FAILURE,
                            'payload': ['Maximum video upload limit reached']
                }
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
                existing = Video.objects.filter(uid=request.user, 
                                                vhash=temp_hash.hexdigest())
                if len(existing) > 1:
                    #error
                    context_dict['payload'] = ['Unrecoverable Error']
                elif len(existing) == 1:
                    #already existing entry
                    context_dict['payload'] = ['Job already exists']
                else:
                    #set response args
                    context_dict['req_params'] = video.vname
                    context_dict['code'] = RES_SUCCESS
                    context_dict['payload'] = ['Job submitted']
                    #save new entry
                    video.save()
                    #submit task chain to celery worker
                    video.process()
            else:
                #form not valid
                context_dict['payload'] = ['Invalid form format']
        else:
            #non POST request
            context_dict['payload'] = ['Invalid request']
        #get the context given
        context = RequestContext(request, context_dict)
    else:
        context = RequestContext(request, 
                                 {'uname': '',
                                  'req': REQ_JOB,
                                  'req_params': '',
                                  'code': RES_FAILURE,
                                  'payload': ["unauthenticated"]
                                  })
    #render the response using the context previously built
    return HttpResponse(template.render(context))


"""
serve requested file, se apache mod_xsendfile for production use
https://docs.djangoproject.com/en/1.2/howto/static-files/
https://github.com/johnsensible/django-sendfile/tree/master/examples/protected_downloads
"""
#TODO migrate to protected_downloads library to abstract permissions <<-----------
def getfile(request):
    template = loader.get_template('sfmmanager/response.xml')
    if request.user.is_authenticated():
        rname = request.GET.get('name', None)
        if rname:
            video = Video.objects.filter(vname=rname)[0]
            resource = ResourceData(video.data.url)
            ### WARNING this is a devel solution not suitable for production
            return serve(request, 
                         resource.getURLOutputPath(), 
                         settings.MEDIA_ROOT, 
                         show_indexes=False)
        else:
            context = RequestContext(request, 
                                 {'uname': request.user.username,
                                  'req': REQ_DOWNLOAD,
                                  'req_params': rname,
                                  'code': RES_FAILURE,
                                  'payload': ["resource not existing or not yet ready"]
                                  })
    else:
        context = RequestContext(request, 
                                 {'uname': '',
                                  'req': REQ_DOWNLOAD,
                                  'req_params': '',
                                  'code': RES_FAILURE,
                                  'payload': ["unauthenticated"]
                                  })
    return HttpResponse(template.render(context))
    
"""
remove a video and video data associated on the server
<get>
<param type='string'>video name</param>
</get>
"""
def delete(request):
    #check if user is authenticated
    template = loader.get_template('sfmmanager/response.xml')
    if request.user.is_authenticated():
        rname = request.GET.get('name', None)
        if rname:
            video_objects = Video.objects.filter(vname=rname)
            if (len(video_objects) > 0):
                video = video_objects[0]
                resource = ResourceData(video.data.url)
                #delete video and data
                resource.removeProcessingData()
                video_objects.delete()
                context = RequestContext(request, 
                                   {'uname': request.user.username,
                                    'req': REQ_DEL,
                                    'req_params': rname,
                                    'code': RES_SUCCESS,
                                    'payload': ["deleted"]
                                    })
            else:
                context = RequestContext(request, 
                                  {'uname': request.user.username,
                                  'req': REQ_DEL,
                                  'req_params': '',
                                  'code': RES_FAILURE,
                                  'payload': ["unexisting video"]
                                  })
        else:
            context = RequestContext(request, 
                                 {'uname': request.user.username,
                                  'req': REQ_DEL,
                                  'req_params': rname,
                                  'code': RES_FAILURE,
                                  'payload': ["no name given"]
                                  })
    else:
        context = RequestContext(request, 
                                 {'uname': '',
                                  'req': REQ_DEL,
                                  'req_params': '',
                                  'code': RES_FAILURE,
                                  'payload': ["unauthenticated"]
                                  })
    return HttpResponse(template.render(context))


#@####################################################################
# Testing- STUFF
def test(request):
    form = UploadFileForm()
    return render_to_response('sfmmanager/test.html', {'form': form})

def rerun(request):
    name = request.GET.get('name', None);
    vd = Video.objects.filter(vname=name)
    for v in vd:
        print "rerunning %s" % name
        nframes = request.GET.get('fps', None)
        if nframes != None:
            v.num_extract_fps = int(nframes)
            v.save()
        v.process()
    return HttpResponse('<p>Rerun</p>')
