from django.test import TestCase

from django.contrib.auth.models import User

# base test case for authenticated views testing
class AuthUserTestCase(TestCase):
    
    def setUp(self):
        #create dummy user
        self.user = User.objects.create_user("debug_user", "", "debug_user")
        self.user.save()

    def tearDown(self):
        #user = User.objects.get(username="debug_user")
        self.user.delete()

    def auth(self):
        self.client.login(username="debug_user", password="debug_user")

    def deauth(self):
        self.client.logout()

    def getUser(self):
        return self.user
