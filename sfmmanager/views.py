"""
@author: qwattash - Alfredo Mazzinghi
@license GPLv2
"""

from django.shortcuts import render, render_to_response
from django.http import HttpResponse, Http404
from django.contrib.auth import authenticate, login, logout
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
REQ_STATUS = "status"
REQ_JOB = "job"
REQ_DOWNLOAD = "download"
RES_SUCCESS = "success"
RES_FAILURE = "failure"

"""
Handle generic requests 
"""
def index(request):
    #allow only specific resources to be accessed
    raise Http404

"""
authenticate an user, begin a new session and return a status
Message Format
<post>
<param type='string'>uname</param>
<param type='string'>password</param>
</post>
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
            payload.append((job.status, job.vname))
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
        if request.method == "POST":
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
        context = RequestContext(request, context_dict)
    else:
        context = RequestContext(request, 
                                 {'uname': '',
                                  'req': REQ_JOB,
                                  'req_params': '',
                                  'code': RES_FAILURE,
                                  'payload': ["unauthenticated"]
                                  })
    return HttpResponse(template.render(context))


"""
serve requested file, se apache mod_xsendfile for production use
https://docs.djangoproject.com/en/1.2/howto/static-files/
https://github.com/johnsensible/django-sendfile/tree/master/examples/protected_downloads
"""
#TODO migrate to protected_downloads library to abstract permissions <<-----------------------------------------------------------
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
        v.process()
    return HttpResponse('<p>Rerun</p>')
