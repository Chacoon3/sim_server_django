from django.test import  TestCase, Client, RequestFactory
from .bmgtModels import *
from .apis import *
from typing import Callable
import json


def _signUp(did:str, password:str):
    req = RequestFactory().post(
        '/bmgt435-service/api/auth/sign-up',
        json.dumps({'did':did, 'password':password}),
        'application/json'
    )
    resp = AuthApi.sign_up(req)
    return resp


def _signIn(did:str, password:str):
    req = RequestFactory().post(
        '/bmgt435-service/api/auth/sign-in',
        json.dumps({'did':did, 'password':password}),
        'application/json'
    )
    resp = AuthApi.sign_in(req)
    return resp


def sendPost(url:str, method:Callable, data:dict, cookies:dict):
    req = RequestFactory().post(
        url,
        json.dumps(data),
        'application/json'
    )
    for key in cookies:
        req.COOKIES[key] = cookies[key]
    resp = method(req)
    return resp


def sendGet(url:str, method:Callable, cookies:dict):
    req = RequestFactory().get(
        url,
    )
    for key in cookies:
        req.COOKIES[key] = cookies[key]
    resp = method(req)
    return resp


class TestSignUp(TestCase):

    def setUp(self):
        self.did = 'did'
        self.password = 'pa3232.ssword'
        BMGTUser.objects.create(first_name='first', last_name='last', did=self.did, role='admin')
        BMGTUser.objects.create(first_name='first321', last_name='last232', did='did232', role='user')


    def testQueryBmgtUser(self):
        user1 = BMGTUser.objects.get(first_name='first')
        user2 = BMGTUser.objects.get(first_name='first321')
        self.assertEqual(user1.first_name, 'first')
        self.assertEqual(user2.first_name, 'first321')


    def testSignUpPositive(self):
        resp = _signUp(self.did, self.password)
        user = BMGTUser.objects.get(did=self.did)
        self.assertEqual(user.activated, True, 'user should be activated after sign up')
        self.assertEqual(resp.status_code, 200)


    def testSignUpNegative(self):
        resp = _signUp('', '')
        self.assertNotEqual(resp.status_code, 200)
        assert not BMGTUser.objects.filter(did='').exists()


    def testSignUpNonExistentUser(self):
        resp = _signUp('did323', 'pass32132321.$')
        self.assertNotEqual(resp.status_code, 200)


    def testRepeatedSignUp(self):
        resp = _signUp(self.did, self.password)
        self.assertEqual(resp.status_code, 200)
        resp2= _signUp(self.did, self.password)
        self.assertNotEqual(resp2.status_code, 200)

    
    def testSignInPositive(self):
        did = 'did232'
        pwd = 'pa3232..ssword'
        _signUp(did, pwd)
        self.assertEqual(BMGTUser.objects.get(did=did).activated, True, 'user should be activated after sign up')
        resp = _signIn(did, pwd)
        self.assertEqual(resp.status_code, 200)


    def testSignInNegative(self):
        did = 'did'
        pwd = 'pa3232.ssword'
        _signUp(did, pwd)
        resp = _signIn(did, 'pa3232.ssword2')
        self.assertNotEqual(resp.status_code, 200)


class UserApiTest(TestCase):

    def setUp(self):
        BMGTUser(first_name='f', last_name='l', did='did', role='admin', activated=1, password='Grave11.').save()
        BMGTUser(first_name='f', last_name='l', did='did323', role='admin', activated=0, password='Grave11.').save()
        BMGTUser(first_name='first321', last_name='last232', did='did232', role='user', activated=1, password='Grave11.').save()


    def testUserMeAfterSignIn(self):
        _signUp( 'did', 'Grave11.')
        _signIn('did', 'Grave11.')
        
        req = RequestFactory().get(
            'bmgt435-service/api/users/me',
        )
        req.COOKIES['id'] = 1

        resp = UserApi.me(req)
        self.assertEqual(resp.status_code, 200)


    def testUserMeNegative(self):
        resp = Client().get(
            'bmgt435-service/api/users/me',
        )
        self.assertNotEqual(resp.status_code, 200)


    def testUserMeNotActivated(self):
        c = Client()
        c.cookies['id'] = 2
        resp = c.get(
            'bmgt435-service/api/users/me',
        )
        self.assertNotEqual(resp.status_code, 200)


class GroupApiTest(TestCase):

    
    def setUp(self) -> None:
        BMGTUser.objects.create(first_name='f', last_name='l', did='did', role='admin', activated=1, password='Grave11.')
        BMGTUser.objects.create(first_name='f', last_name='l', did='did323', role='admin', activated=0, password='Grave11.')
        BMGTUser.objects.create(first_name='first321', last_name='last232', did='did232', role='user', activated=1, password='Grave11.')
        BMGTSemester.objects.create(year=2022, season='fall')
        BMGTGroup.objects.create(number = 1, semester = BMGTSemester.objects.get(year=2022, season='fall'))

    
    def testGetGroupPositive(self):
        c = RequestFactory()
        c.cookies['id'] = 1
        req = c.get(
            'bmgt435-service/api/groups?id=1',
        )
        resp = GroupApi.get_group(req)
        self.assertEqual(resp.status_code, 200)
        
