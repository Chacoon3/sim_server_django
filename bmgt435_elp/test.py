from django.test import  TestCase
from .bmgtModels import *
from .apis import *
from django.contrib.auth.hashers import make_password, check_password
from django.test import Client
import json 


class AppAuthTest(TestCase):

    def setUp(self):
        BMGTUser.objects.create(first_name='first', last_name='last', did='did', role='admin').save()
        BMGTUser.objects.create(first_name='first321', last_name='last232', did='did232', role='user').save()


    def queryBmgtUser(self):
        user1 = BMGTUser.objects.get(first_name='first')
        user2 = BMGTUser.objects.get(first_name='first321')
        self.assertEqual(user1.first_name, 'first')
        self.assertEqual(user2.first_name, 'first321')


    def signUpPositive(self):
        client = Client()
        resp = client.post(
            '/bmgt435-service/api/auth/sign-up', 
            json.dumps({'did': 'did', 'password': 'pa3232.ssword'}),
            'application/json'
        )
        self.assertEqual(resp.status_code, 200)


    def signUpNegative(self):
        resp = Client().post(
            '/bmgt435-service/api/auth/sign-up',
            json.dumps({'did':'', 'password':""}),
            'application/json'
        )
        self.assertNotEqual(resp.status_code, 200)


    def signUpNonExistentUser(self):
        resp = Client().post(
            '/bmgt435-service/api/auth/sign-up',
            json.dumps({'did':'did323', 'password':"pass32132321.$"}),
            'application/json'
        )
        self.assertNotEqual(resp.status_code, 200)


    def repeatedSignUp(self):
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

    
    def signInPositive(self):
        c = Client()
        c.post(
            'bmgt435-service/api/auth/sign-up',
            json.dumps({'did':'did', 'password':'pa3232.ssword'}),
        )

        resp = c.post(
            'bmgt435-service/api/auth/sign-in',
            json.dumps({'did': 'did', 'password': 'pa3232.ssword'}),
            'application/json'
        )

        self.assertEqual(resp.status_code, 200)


    def signInNegative(self):
        c = Client()
        c.post(
            'bmgt435-service/api/auth/sign-up',
            json.dumps({'did':'did', 'password':'pa3232.ssword'}),
        )

        resp = c.post(
            'bmg435-service/api/auth/sign-in',
            json.dumps({'did':'did', 'password':'pa3232.ssw2ord'}),
        )
        self.assertNotEqual(resp.status_code, 200)