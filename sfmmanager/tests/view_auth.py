from django.test import TestCase

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from sfmmanager import views

# authentication test view
class AuthTestCase(TestCase):
    
    def setUp(self):
        #create dummy user
        User.objects.create_user("debug_user", "", "debug_user")

    def tearDown(self):
        #remove dummy user for security reasons
        user = User.objects.get(username="debug_user")
        user.delete()
    
    def test_auth_invalid_format(self):
        response = self.client.get("/uclvr/auth", {"wronguname": "debug_user", "wrongpwd": "debug_user"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_AUTH)
        self.assertEqual(response.context['payload'], ["Invalid request format"])

    def test_auth_wrong_uname(self):
        response = self.client.get("/uclvr/auth", {"uname": "debug_wrong", "password": "debug_user"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_AUTH)
        self.assertEqual(response.context['payload'], ["Invalid username or password"])

    def test_auth_wrong_password(self):
        response = self.client.get("/uclvr/auth", {"uname": "debug_user", "password": "debug_wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_AUTH)
        self.assertEqual(response.context['payload'], ["Invalid username or password"])

    def test_auth_success(self):
        response = self.client.get("/uclvr/auth", {"uname": "debug_user", "password": "debug_user"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_AUTH)
        self.assertEqual(response.context['payload'], ["authentication succeded"])
