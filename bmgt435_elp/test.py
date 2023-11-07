from django.test import  TestCase
from .bmgtModels import *
from .apis import *
from django.contrib.auth.hashers import make_password, check_password
from requests import Request, Response
from django.test import Client
import json 

class AppTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        BMGTUser.objects.create(first_name='first', last_name='last', did='did', role='admin').save()
        BMGTUser.objects.create(first_name='first321', last_name='last232', did='did232', role='user').save()


    def testBmgtUser(self):
        user1 = BMGTUser.objects.get(first_name='first')
        user2 = BMGTUser.objects.get(first_name='first321')
        self.assertEqual(user1.first_name, 'first')
        self.assertEqual(user2.first_name, 'first321')


    def testSignUpPositive(self):
        client = Client()
        resp = client.post(
            '/bmgt435-service/api/auth/sign-up', 
            json.dumps({'did': 'did', 'password': 'pa3232.ssword'}),
            'application/json'
        )
        self.assertEqual(resp.status_code, 200)


    def testSignUpNegative(self):
        resp = Client().post(
            '/bmgt435-service/api/auth/sign-up',
            json.dumps({'did':'', 'password':""}),
            'application/json'
        )
        self.assertNotEqual(resp.status_code, 200)


    def testRepeatedSignUp(self):
        client = Client()
        resp = client.post(
            '/bmgt435-service/api/auth/sign-up', 
            json.dumps({'did': 'did', 'password': 'pa3232.ssword'}),
            'application/json'
        )
        
        resp= client.post(
            '/bmgt435-service/api/auth/sign-up',
            json.dumps({'did': 'did', 'password': 'pa3232.ssword'}),
            'application/json'
        )
        self.assertNotEqual(resp.status_code, 200)