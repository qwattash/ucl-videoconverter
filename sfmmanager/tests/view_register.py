from django.test import TestCase

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from sfmmanager import views

# test registration view
class RegisterTestCase(TestCase):

    def setUp(self):
        #create dummy user
        User.objects.create_user("debug_user", "", "debug_user")
    
    def tearDown(self):
        #remove dummy user for security reasons
        try:
            user = User.objects.get(username="debug_user")
            user.delete()
            user = User.objects.get(username="debug_user1")
            user.delete()
        except:
            pass

    def test_register_invalid_format(self):
        response = self.client.get("/uclvr/register", {"wrong_uname": "", "email": "", "wrong_password": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_REG)
        self.assertEqual(response.context['payload'], ["Missing parameter"])

    def test_register_existing(self):
        response = self.client.get("/uclvr/register", {"uname": "debug_user", "email": "", "password": "debug_user"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_REG)
        self.assertEqual(response.context['payload'], ["Account with same name already exists"])
    
    def test_register_success(self):
        response = self.client.get("/uclvr/register", {"uname": "debug_user1", "email": "mymail@mail.com", "password": "debug_user"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user1')
        self.assertEqual(response.context['req'], views.REQ_REG)
        self.assertEqual(response.context['payload'], ["Registered"])
