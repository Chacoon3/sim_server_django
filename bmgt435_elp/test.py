from django.test import  TestCase, Client
from .bmgtModels import *
from .apis import *
import json


def _clientSetCookies(client:Client, cookies:dict):
    for k, v in cookies.items():
        client.cookies[k] = v


def _clientSignUp(client:Client, did:str, password:str):
    return client.post(
        'bmgt435-service/api/auth/sign-up',
        json.dumps({'did': did, 'password': password}),
        'application/json'
    )


def _clientSignIn(client:Client, did:str, password:str):
    resp = client.post(
        'bmgt435-service/api/auth/sign-in',
        json.dumps({'did': did, 'password': password}),
        'application/json'
    )
    return resp


class AppAuthTest(TestCase):

    def setUp(self):
        BMGTUser(first_name='first', last_name='last', did='did', role='admin').save()
        BMGTUser(first_name='first321', last_name='last232', did='did232', role='user').save()


    def testQueryBmgtUser(self):
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


    def testSignUpNonExistentUser(self):
        resp = Client().post(
            '/bmgt435-service/api/auth/sign-up',
            json.dumps({'did':'did323', 'password':"pass32132321.$"}),
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

    
    def testSignInPositive(self):
        c = Client()
        _clientSignUp(c, 'did', 'pa3232.ssword')

        resp = c.post(
            'bmgt435-service/api/auth/sign-in',
            json.dumps({'did': 'did', 'password': 'pa3232.ssword'}),
            'application/json'
        )

        self.assertEqual(resp.status_code, 200)


    def testSignInNegative(self):
        c = Client()
        c.post(
            'bmgt435-service/api/auth/sign-up',
            json.dumps({'did':'did', 'password':'pa3232.ssword'}),
            'application/json'
        )

        resp = c.post(
            'bmg435-service/api/auth/sign-in',
            json.dumps({'did':'did', 'password':'pa3232.ssw2ord'}),
            'application/json'
        )
        self.assertNotEqual(resp.status_code, 200)


class UserApiTest(TestCase):

    def setUp(self):
        BMGTUser(first_name='f', last_name='l', did='did', role='admin', activated=1, password='Grave11.').save()
        BMGTUser(first_name='f', last_name='l', did='did323', role='admin', activated=0, password='Grave11.').save()
        BMGTUser(first_name='first321', last_name='last232', did='did232', role='user', activated=1, password='Grave11.').save()

    
    def testUserMePositive(self):
        resp = Client().get(
            'bmgt435-service/api/user/me',
        )
        self.assertNotEqual(resp.status_code, 200)


    def testUserMeAfterSignIn(self):
        c = Client()
        _clientSignUp(c, 'did', 'Grave11.')
        _clientSignIn(c, 'did', 'Grave11.')
        
        resp = c.get(
            'bmgt435-service/api/users/me',
        )
        self.assertEqual(resp.status_code, 200)


    def testUserMeNegative(self):
        resp = Client().get(
            'bmgt435-service/api/users/me',
        )
        self.assertNotEqual(resp.status_code, 200)


    def testUserMeNotActivated(self):
        resp = Client().get(
            'bmgt435-service/api/users/me',
        )
        self.assertNotEqual(resp.status_code, 200)


class GroupApiTest(TestCase):

    def setUp(self) -> None:
        BMGTUser(first_name='f', last_name='l', did='did', role='admin', activated=1, password='Grave11.').save()
        BMGTUser(first_name='f', last_name='l', did='did323', role='admin', activated=0, password='Grave11.').save()
        BMGTUser(first_name='first321', last_name='last232', did='did232', role='user', activated=1, password='Grave11.').save()
        BMGTSemester(year=2022, season='fall').save()
        BMGTGroup(number = 1, semester = BMGTSemester.objects.get(year=2022, season='fall')).save()

    
    def testGetGroupPositive(self):
        c = Client()
        _clientSignUp(c, 'did', 'Grave11.')
        _clientSignIn(c, 'did', 'Grave11.')
        _clientSetCookies(c, {'id': 1})
        resp = c.get(
            'bmgt435-service/api/groups?id=1',
        )
        self.assertEqual(resp.status_code, 200)