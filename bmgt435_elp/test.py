from django.test import  TestCase, RequestFactory, Client
from django.db import IntegrityError, transaction
from .bmgtModels import *
from .apis import *
from typing import Callable
import json
import pandas as pd
import io
from http.cookies  import SimpleCookie

"""
Note:
    request factory based tests bypass the middleware layer
    to test middleware functionality use the client based tests
"""



def _signUp(did:str, password:str):
    req = RequestFactory().post(
        '/bmgt435-service/api/auth/sign-up',
        json.dumps({'did':did, 'password':password}),
        'application/json'
    )
    resp = AuthApi.sign_up(req)
    return resp


def _signIn(did:str, password:str, remember:bool = False):
    req = RequestFactory().post(
        '/bmgt435-service/api/auth/sign-in',
        json.dumps({'did':did, 'password':password, 'remember':remember}),
        'application/json'
    )
    resp = AuthApi.sign_in(req)
    return resp


def _sendPost(url:str, method:Callable, jsonSerializable, cookies:dict):
    req = RequestFactory().post(
        url,
        json.dumps(jsonSerializable),
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

def _makeFoodCenterCaseParams() -> dict:
    return {
        'case_id':1,
        'case_params': {
            'centers':['1','2','5'],
            'policies':[
                (1900, 3000),
                (2000, 4000),
                (3000, 5000),
            ]
        }
    }

def _makeImportUserData() -> pd.DataFrame:
    return pd.DataFrame({
        'user_first_name':['32131sdsacx', 'f2', 'f3'],
        'user_last_name':['l1', 'dasdz2asz', 'l3'],
        'directory_id':['ddddd', 'fffsazcxzcz', 'didsad3d3'],
    })

class AppTestCaeBase(TestCase):

    def _deserialize_resp_data(self, resp:HttpResponse) -> dict:
        return json.loads(resp.content)

    def assertResolved(self, resp:HttpResponse, msg=None):
        data = self._deserialize_resp_data(resp)
        self.assertTrue(data.get('data', None) is not None, msg if msg else data.get('errorMsg', None))

    def assertRejected(self, resp:HttpResponse, msg=None):
        data = self._deserialize_resp_data(resp)
        self.assertTrue(data.get('errorMsg', None) is not None, msg)
        

class TestAuthApi(AppTestCaeBase):

    def setUp(self):
        self.did = 'did'
        self.password = 'pa3232.ssword'
        BMGTUser.objects.create(first_name='first', last_name='last', did=self.did, role='admin')
        BMGTUser.objects.create(first_name='first321', last_name='last232', did='did232', role='user')

    
    def testBulkCreate(self):
        try:
            with transaction.atomic():
                BMGTUser.objects.bulk_create([
                    BMGTUser(first_name='f', last_name='l', did='did', role='admin', activated=1, password='Grave11.'),
                    BMGTUser(first_name='f', last_name='l', did='did323', role='admin', activated=0, password='Grave11.'),
                    BMGTUser(first_name='first321', last_name='last232', did='did232', role='user', activated=1, password='Grave11.'),
                ])
            self.fail()
        except IntegrityError:
            self.assertEqual(
                BMGTUser.objects.all().count(), 2,
            )


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
        self.assertTrue(resp.cookies.get('id', None) is not None)
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


class TestCaseAndRecordApi(AppTestCaeBase):
    def setUp(self):
        BMGTUser.objects.create(first_name='f', last_name='l', did='did', role='admin', activated=1, password='Grave11.')
        BMGTUser.objects.create(first_name='f', last_name='l', did='did323', role='admin', activated=0, password='Grave11.')
        BMGTUser.objects.create(first_name='first321', last_name='last232', did='did232', role='user', activated=1, password='Grave11.')
        BMGTSemester.objects.create(year=2022, season='fall')
        BMGTGroup.objects.create(number = 1, semester = BMGTSemester.objects.get(year=2022, season='fall'))
        BMGTCase.objects.create(name = 'food center', visible = True, max_submission = -1)
        self.cookies = {'id':1}
        self.paginatedParams = {'page':1, 'size':10}

        _sendPost('/bmgt435-service/api/groups/join', GroupApi.join_group, {'group_id':1}, self.cookies)

        self.assertEqual(BMGTGroup.objects.get(id=1).users.count(), 1, 'join group failed')
        self.assertEqual(BMGTUser.objects.get(id=1).group_id, 1, 'join group failed')

    
    def testGetCasePositive(self):
        resp = _sendGet('/bmgt435-service/api/cases/get?case_id=1', CaseApi.get, self.cookies)
        self.assertResolved(resp)


    def testGetCaseNegative(self):
        resp = _sendGet('/bmgt435-service/api/cases/get?id=-1', CaseApi.get, self.cookies)
        self.assertRejected(resp)

        resp = _sendGet('/bmgt435-service/api/cases/get?id=2', CaseApi.get, self.cookies)
        self.assertRejected(resp)


    def testSubmitCasePositive(self):
        params = _makeFoodCenterCaseParams()
        resp = _sendPost('/bmgt435-service/api/cases/submit', CaseApi.submit, params, self.cookies)
        self.assertResolved(resp)
        self.assertTrue(BMGTCaseRecord.objects.filter(group_id=1, case_id=1).exists(), 'case record not created')

        resp = _sendGet(
            'bmgt435-service/api/leader-board/paginated', 
            CaseRecordApi.leader_board_paginated, 
            self.cookies,
            {'page':1, 'size':10, 'case_id':1}
            )
        self.assertResolved(resp)


    def testSubmitCaseNegative(self):
        params = _makeFoodCenterCaseParams()
        negativeCookies = self.cookies.copy()
        negativeCookies['id'] = -1
        resp = _sendPost('/bmgt435-service/api/cases/submit', CaseApi.submit, params, negativeCookies)
        self.assertRejected(resp)

        params = _makeFoodCenterCaseParams()
        # leave group
        resp = _sendPost('/bmgt435-service/api/groups/leave', GroupApi.leave_group, {'group_id':1}, self.cookies)
        self.assertResolved(resp)

        resp = _sendPost('/bmgt435-service/api/cases/submit', CaseApi.submit, params, self.cookies)
        self.assertRejected(resp)

        self.assertTrue(BMGTCaseRecord.objects.all().count() == 0, 'case record created')


class TestManageApi(AppTestCaeBase):

    def setUp(self) -> None:
        BMGTUser.objects.create(first_name='f', last_name='l', did='did', role='admin', activated=True, password='Grave11.')
        BMGTUser.objects.create(first_name='f', last_name='l', did='did323', role='admin', activated=False, password='Grave11.')
        BMGTUser.objects.create(first_name='first321', last_name='last232', did='did232', role='user', activated=True, password='Grave11.')

        BMGTSemester.objects.create(year=2022, season='fall')

        BMGTGroup.objects.create(number = 1, semester = BMGTSemester.objects.get(year=2022, season='fall'))
        BMGTGroup.objects.create(number = 2, semester = BMGTSemester.objects.get(year=2022, season='fall'))

        BMGTCase.objects.create(name = 'food center', visible = True, max_submission = -1)

        self.cookies = {'id':1}
        self.paginatedParams = {'page':1, 'size':10}

    
    def testImportUsersPositive(self):
        df = _makeImportUserData()
        ioBuffer = io.BytesIO()

        df.to_csv(ioBuffer, index=False)
        req = RequestFactory().post(
            '/bmgt435-service/api/manage/user/import/semester/1',
            content_type='octet/stream',
            data=ioBuffer.getvalue(),
        )

        resp = ManageApi.import_users(req, 1)

        self.assertResolved(resp,)
        self.assertEqual(BMGTUser.objects.all().count(), 6, )
        

    def testImportUsersNegative(self):
        df = _makeImportUserData()
        ioBuffer = io.BytesIO()
        df.to_csv(ioBuffer, index=False)
        req = RequestFactory().post(
            '/bmgt435-service/api/manage/user/import/semester/1',
            content_type='octet/stream',
            data=ioBuffer.getvalue(),
        )
        resp = ManageApi.import_users(req, 2)
        self.assertRejected(resp,)


        df.columns = ['user_first_name', 'user_last_name', 'did']
        ioBuffer = io.BytesIO()
        df.to_csv(ioBuffer, index=False)
        req = RequestFactory().post(
            '/bmgt435-service/api/manage/user/import/semester/1',
            content_type='octet/stream',
            data=ioBuffer.getvalue(),
        )
        resp = ManageApi.import_users(req, 1)
        self.assertRejected(resp,)


        fakeCookies = self.cookies.copy()
        fakeCookies['id'] = -1
        req = RequestFactory().post(
            '/bmgt435-service/api/manage/user/import/semester/1',
            content_type='octet/stream',
            data=ioBuffer.getvalue(),
        )
        resp = ManageApi.import_users(req, 1)
        self.assertRejected(resp)

    def testViewUsers(self):
        # positive
        params = {
            'page':1,
            'size':10,
        }
        resp = _sendGet('/bmgt435-service/api/manage/user/view', ManageApi.view_users, self.cookies, params)
        self.assertResolved(resp)

        
    def testViewUserNegative(self):
        params = {
            'page':1,
            'size':10,
        }
        negCookies = self.cookies.copy()
        negCookies['id'] = -1
        resp = _sendGet('/bmgt435-service/api/manage/user/view', ManageApi.view_users, negCookies, params)
        self.assertResolved(resp)

        negCookies = self.cookies.copy()
        negCookies['id'] = 2
        resp = _sendGet('/bmgt435-service/api/manage/user/view', ManageApi.view_users, negCookies, params)
        self.assertResolved(resp)


    def testCreateSemesterPositive(self):
        req = RequestFactory().post(
            '/bmgt435-service/api/manage/semester/create',
            json.dumps({'year':2022, 'season':'spring'}),
            'application/json'
        )
        resp = ManageApi.create_semester(req)
        self.assertResolved(resp)
        self.assertEqual(BMGTSemester.objects.count(), 2)


    def testCreateSemesterNegative(self):
        c = Client()
        negCookies = self.cookies.copy()
        negCookies['id'] = 2
        c.cookies = SimpleCookie(negCookies)
        resp = c.post('/bmgt435-service/api/manage/semester/create', json.dumps({'year':2022, 'season':'spring'}), content_type='application/json')
        self.assertRejected(resp)
        self.assertEqual(BMGTSemester.objects.count(), 1)

        negCookies = self.cookies.copy()
        negCookies['id'] = -1
        c.cookies = SimpleCookie(negCookies)
        resp = c.post('/bmgt435-service/api/manage/semester/create', json.dumps({'year':2021, 'season':'fall'}), content_type='application/json')      
        self.assertRejected(resp)
        self.assertEqual(BMGTSemester.objects.count(), 1)


    def testFoodDeliveryConfigPositive(self):
        config= {
            'config':[
                [1, 2],
                [2, 1],
                [3, 4],
                [4, 3],
                [5, 6],
                [6, 5],
            ],
            "case_id":1
        }
        c = Client()
        c.cookies = SimpleCookie({'id':1})
        resp = c.post('/bmgt435-service/api/manage/case-config/update', json.dumps(config), content_type='application/json')
        self.assertResolved(resp)


    def testFoodDeliveryConfigNegative(self):
        config= {
            'config':[
                [1, 2],
                [2, 1],
                [3, 4],
                [4, 3],
                [5, 6],
                [6, 5],
            ],
            "case_id":1
        }
        c = Client()
        c.cookies = SimpleCookie({'id':2})
        resp = c.post('/bmgt435-service/api/manage/case-config/update', json.dumps(config), content_type='application/json')
        self.assertRejected(resp)

        c.cookies = SimpleCookie({'id':-1})
        resp = c.post('/bmgt435-service/api/manage/case-config/update', json.dumps(config), content_type='application/json')
        self.assertRejected(resp)

        badConfig = {
            'config':[
                [1, 2],
                [2, 1],
                [3, 4],
                [4, 3],
                [5, 6],
                [6, 5],
                [7, 8],
            ],
            "case_id":1
        }

        c.cookies = SimpleCookie({'id':1})
        resp = c.post('/bmgt435-service/api/manage/case-config/update', json.dumps(badConfig), content_type='application/json')
        self.assertRejected(resp)

        badConfig2 = {
            'config':[
                [1, 2],
                [2, 1],
                [3, 4],
                [4, 3],
                [5, 6],
                [6, 1],
            ],
            "case_id":1
        }
        resp = c.post('/bmgt435-service/api/manage/case-config/update', json.dumps(badConfig2), content_type='application/json')
        self.assertRejected(resp)
        

    def testCaseConfigIntegrity(self):
        try:
            BMGTCaseConfig(case_id=1).save()
            BMGTCaseConfig(case_id=1).save()
            self.fail()
        except IntegrityError:
            return
        

    def testSetCaseSubmissionLimitPositive(self):
        c = Client()
        c.cookies = SimpleCookie({'id':1})
        resp = c.post('/bmgt435-service/api/manage/case-submissions/limit', json.dumps({'case_id':1, 'max_submission':10}), content_type='application/json')
        self.assertResolved(resp)

        resp = c.get('/bmgt435-service/api/manage/case-submissions/limit', {'case_id':1})
        self.assertResolved(resp)
        self.assertEqual(json.loads(resp.content)['data'], 10)