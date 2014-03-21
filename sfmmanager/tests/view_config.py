from django.core.urlresolvers import reverse

from sfmmanager import views
from sfmmanager.models import *
from .base import *
import mock

# test config view
class ConfigTestCase(AuthUserTestCase):
    
    def setUp(self):
        super(ConfigTestCase, self).setUp()
        self.video = Video()
        self.video.data = None
        self.video.uid = self.user
        self.video.vname = "dummy"
        self.video.vhash = ""
        self.video.status = Video.STATUS_RECONSTRUCTED
        self.video.save()
    
    def tearDown(self):
        Video.objects.filter(uid=self.user).delete()
        super(ConfigTestCase, self).tearDown()

    def test_param_created(self):
        self.video = Video()
        self.video.data = None
        self.video.uid = self.user
        self.video.vname = "foo"
        self.video.vhash = ""
        self.video.status = Video.STATUS_RECONSTRUCTED
        self.video.save()
        params = Parameter.objects.filter(vid=self.video)
        self.assertTrue(len(params) > 0)
        self.assertEqual(params[0].name, Parameter.PARAM_FPS)
        self.assertEqual(params[0].value, Parameter.DEFAULTS[Parameter.PARAM_FPS])

    def test_config_unauth(self):
        self.deauth()
        response = self.client.get("/uclvr/config", {'name': 'dummy', 'cmd': 'reset', 'pname': 'frames'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_CONF)
        self.assertEqual(response.context['payload'], ["Unauthenticated"])

    def test_config_unexisting(self):
        self.auth()
        response = self.client.get("/uclvr/config", {'name': 'unexisting', 'cmd': 'reset', 'pname': 'frames'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_CONF)
        self.assertEqual(response.context['payload'], ["Unexisting video"])

    def test_no_name(self):
        self.auth()
        response = self.client.get("/uclvr/config", {'cmd': 'reset', 'pname': 'frames'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_CONF)
        self.assertEqual(response.context['payload'], ["Missing name of video or command"])
    
    """
    see http://www.mattjmorrison.com/2011/09/mocking-django.html
    """
    @mock.patch("sfmmanager.models.Parameter.reset", mock.Mock())
    def test_reset(self):
        self.auth()
        Parameter.reset.return_value = '1'
        response = self.client.get("/uclvr/config", {'name': 'dummy', 'pname': 'frames', 'cmd': 'reset'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_CONF)
        self.assertEqual(response.context['payload'], ["Config reset: frames = 1"])
        self.assertEqual(Parameter.reset.call_count, 1)
        self.assertEqual(Parameter.objects.filter(vid=self.video, name='frames')[0].value, '1')

    def test_set_noarg(self):
        self.auth()
        response = self.client.get("/uclvr/config", {'name': 'dummy', 'pname': 'frames', 'cmd': 'set'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_CONF)
        self.assertEqual(response.context['payload'], ["Illegal parameter value"])

    def test_set_wrong_arg(self):
        self.auth()
        response = self.client.get("/uclvr/config", {'name': 'dummy', 'pname': 'frames', 'cmd': 'set', 'arg': 'thisShouldBeInt'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_CONF)
        self.assertEqual(response.context['payload'], ["Illegal parameter value"])

    def test_set_wrong_param(self):
        self.auth()
        response = self.client.get("/uclvr/config", {'name': 'dummy', 'pname': 'unexistingparam', 'cmd': 'set', 'arg': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_CONF)
        self.assertEqual(response.context['payload'], ["Invalid parameter"])

    def test_set(self):
        self.auth()
        response = self.client.get("/uclvr/config", {'name': 'dummy', 'pname': 'frames', 'cmd': 'set', 'arg': '10'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_CONF)
        self.assertEqual(response.context['payload'], ["Config set: frames = 10"])
        self.assertEqual(Parameter.objects.filter(vid=self.video, name='frames')[0].value, '10')

    def test_get(self):
        self.auth()
        param = Parameter.objects.filter(vid=self.video, name='frames')[0]
        param.value = '99'
        param.save()
        response = self.client.get("/uclvr/config", {'name': 'dummy', 'pname': 'frames', 'cmd': 'get'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_CONF)
        self.assertEqual(response.context['payload'], ["Config get: frames = 99"])
    
    def test_invalid_command(self):
        self.auth()
        response = self.client.get("/uclvr/config", {'name': 'dummy', 'pname': 'frames', 'cmd': 'unexisting_command', 'arg': '10'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_CONF)
        self.assertEqual(response.context['payload'], ["Invalid command"])
