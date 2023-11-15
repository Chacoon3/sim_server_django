from django.test import  TestCase, RequestFactory
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


def _sendPost(url:str, method:Callable, data, cookies:dict):
    req = RequestFactory().post(
        url,
        json.dumps(data),
        'application/json'
    )
    for key in cookies:
        req.COOKIES[key] = cookies[key]
    resp = method(req)
    return resp


def _sendGet(url:str, method:Callable, cookies:dict, getParams:dict = None):
    req = RequestFactory().get(
        url,
    )
    if getParams:
        req.GET = getParams
    for key in cookies:
        req.COOKIES[key] = cookies[key]
    resp = method(req)
    return resp


def _getResponeData(resp:HttpResponse):
    return json.loads(resp.content)


class AppTestCaeBase(TestCase):

    def _deserialize_resp_data(self, resp:HttpResponse) -> dict:
        return json.loads(resp.content)


    def assertResolved(self, resp:HttpResponse, msg=None):
        data = self._deserialize_resp_data(resp)
        self.assertTrue(data.get('resolver') is not None, msg)


    def assertRejected(self, resp:HttpResponse, msg=None):
        data = self._deserialize_resp_data(resp)
        self.assertTrue(data.get('error_msg') is not None, msg)
        

class TestAuthApi(AppTestCaeBase):

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
        self.assertResolved(resp)


    def testSignUpNegative(self):
        resp = _signUp('23132', 'Grave2231312.')
        self.assertEqual(resp.status_code, 200)
        assert not BMGTUser.objects.filter(did='').exists()
        self.assertRejected(resp)


    def testSignUpNonExistentUser(self):
        resp = _signUp('did323', 'pass32132321.$')
        self.assertEqual(resp.status_code, 200)
        self.assertRejected(resp)


    def testRepeatedSignUp(self):
        resp = _signUp(self.did, self.password)
        self.assertResolved(resp)
        resp2= _signUp(self.did, self.password)
        self.assertRejected(resp2)

    
    def testSignInPositive(self):
        did = 'did232'
        pwd = 'pa3232..ssword'
        _signUp(did, pwd)
        self.assertEqual(BMGTUser.objects.get(did=did).activated, True,)
        resp = _signIn(did, pwd)
        self.assertResolved(resp)


    def testSignInNegative(self):
        did = 'did'
        pwd = 'pa3232.ssword'
        resp = _signUp(did, pwd)
        self.assertResolved(resp)
        resp2 = _signIn(did, 'pa3232.ssword2')
        self.assertRejected(resp2)


    def testSignOutPositive(self):
        did = 'did'
        pwd = 'pa3232.ssword'
        respSignUp = _signUp(did, pwd)
        self.assertResolved(respSignUp)

        respSignIn = _signIn(did, pwd)
        self.assertResolved(respSignIn)

        req = RequestFactory().post(
            '/bmgt435-service/api/auth/sign-out',
        )
        req.COOKIES['id'] = 1
        respSignOut = AuthApi.sign_out(req)
        self.assertResolved(respSignOut)


    def testSignOutNegative(self):
        req = RequestFactory().post(
            '/bmgt435-service/api/auth/sign-out',
        )
        req.COOKIES['id'] = -1
        resp = AuthApi.sign_out(req)
        self.assertRejected(resp)

        req = RequestFactory().post(
            '/bmgt435-service/api/auth/sign-out',
        )
        req.COOKIES.clear()
        resp = AuthApi.sign_out(req)
        self.assertRejected(resp)


class TestUserApi(AppTestCaeBase):

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
        self.assertResolved(resp)


    def testUserMeNegative(self):
        resp = _sendGet('/bmgt435-service/api/users/me', UserApi.me, {})
        self.assertRejected(resp)


    def testUserMeNotActivated(self):
        resp = _sendGet('/bmgt435-service/api/users/me', UserApi.me, {'id':-1})
        self.assertRejected(resp)


class TestGroupApi(AppTestCaeBase):

    
    def setUp(self) -> None:
        BMGTUser.objects.create(first_name='f', last_name='l', did='did', role='admin', activated=1, password='Grave11.')
        BMGTUser.objects.create(first_name='f', last_name='l', did='did323', role='admin', activated=0, password='Grave11.')
        BMGTUser.objects.create(first_name='first321', last_name='last232', did='did232', role='user', activated=1, password='Grave11.')
        BMGTSemester.objects.create(year=2022, season='fall')
        BMGTGroup.objects.create(number = 1, semester = BMGTSemester.objects.get(year=2022, season='fall'))
        self.cookies = {'id':1}
        self.paginatedParams = {'page':1, 'size':10}

    
    def testGroupIntegrity(self):
        try:
            BMGTGroup(number=1).save()
            self.fail()
        except IntegrityError:
            return

    
    def testGetGroupPositive(self):
        resp = _sendGet('/bmgt435-service/api/groups?id=1', GroupApi.get_group, self.cookies)
        self.assertResolved(resp)

    
    def testGetGroupNegative(self):
        resp = _sendGet('/bmgt435-service/api/groups?id=2', GroupApi.get_group, self.cookies)
        self.assertRejected(resp)


    def testGetGroupPaginated(self):
        resp = _sendGet('/bmgt435-service/api/groups/paginated', GroupApi.groups_paginated, self.cookies, self.paginatedParams)
        self.assertResolved(resp)


    def testGetGroupPaginatedNeg(self):
        params = self.paginatedParams
        params['page'] = -1
        resp = _sendGet('/bmgt435-service/api/groups/paginated', GroupApi.groups_paginated, self.cookies, self.paginatedParams)
        self.assertRejected(resp)

        params['page'] = 100
        resp = _sendGet('/bmgt435-service/api/groups/paginated', GroupApi.groups_paginated, self.cookies, self.paginatedParams)
        self.assertRejected(resp)
        

    def testGroupSuitePos(self):
        # join
        resp = _sendPost('/bmgt435-service/api/groups/join', GroupApi.join_group, {'group_id':1}, self.cookies)
        self.assertResolved(resp)
        self.assertEqual(BMGTGroup.objects.get(id=1).users.count(), 1, 'join group failed')
        self.assertEqual(BMGTUser.objects.get(id=1).group_id, 1, 'join group failed')

        # leave
        resp = _sendPost('/bmgt435-service/api/groups/leave', GroupApi.leave_group, {'group_id':1}, self.cookies)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(BMGTGroup.objects.get(id=1).users.count(), 0, 'leave group failed')
        self.assertEqual(BMGTUser.objects.get(id=1).group_id, None, 'leave group failed')


    def testJoinGroupNeg(self):
        resp = _sendPost('/bmgt435-service/api/groups/join', GroupApi.join_group, {'group_id':-1}, self.cookies)
        self.assertEqual(resp.status_code, 200)
        self.assertRejected(resp)

        resp = _sendPost('/bmgt435-service/api/groups/join', GroupApi.join_group, {'groupid':1}, self.cookies)
        self.assertEqual(resp.status_code, 200)
        self.assertRejected(resp)