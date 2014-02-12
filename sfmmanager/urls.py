"""
@author: qwattash - Alfredo Mazzinghi
@license GPLv2
"""

from django.conf.urls import patterns, url

from sfmmanager import views

urlpatterns = patterns('',
                       url(r'^$', views.index, name='index'),
                       url(r'^auth/?$', views.auth, name='auth'),
                       url(r'^status/?$', views.status, name='status'),
                       url(r'^unauth/?$', views.unauth, name='unauth'),
                       url(r'^upload/?$', views.upload, name='upload'),
                       url(r'^download/?$', views.getfile, name='getfile'),
                       url(r'^test/?$', views.test, name='test'),
                       url(r'^rerun/?$', views.rerun, name='rerun'),
                       url(r'^register/?$', views.register, name='register'),
                       url(r'^delete/?$', views.delete, name='delete')
)
