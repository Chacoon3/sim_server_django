from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST, require_GET,  require_http_methods
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import redirect

from .simulation.Cases import FoodCenter
from .bmgtModels import *
from .utils.statusCode import Status
from .utils.jsonUtils import *
from .utils.apiUtils import *

import time
import pandas as pd
import regex as re
import json
import io



class Auth:

    @staticmethod
    def __set_auth_cookie(response: HttpResponse, user: BMGTUser) -> None:
        response.set_cookie('id', str(user.id), samesite='none', secure=True, httponly=True)
        response.set_cookie('role_id', user.role_id, samesite='none', secure=True, httponly=True) # for previlege control

    @staticmethod
    def __clear_auth_cookie(response: HttpResponse) -> None:
        response.delete_cookie('id', samesite='none')
        response.delete_cookie('role_id', samesite='none')

    @api_error_handler
    @require_POST
    @staticmethod
    def sign_in(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        data = json.loads(request.body)
        did = data['did']
        password = data['password']

        user = BMGTUser.objects.filter(did=did, activated=True, flag_deleted=0)
        if user:
            user = user[0]
            if user and user.password and check_password(password, user.password):
                resp.status_code = Status.OK
                Auth.__set_auth_cookie(resp, user)
                resp.write(serialize_model_instance(user))
            else:
                resp.status_code = Status.UNAUTHORIZED
                resp.write(
                    "Sign in failed. Please check your directory ID and password!")
        else:
            resp.status_code = Status.NOT_FOUND
            resp.write("Sign in failed! Please check your directory ID and password!")

        return resp

    @api_error_handler
    @require_POST
    @staticmethod
    def sign_up(request: HttpRequest) -> HttpResponse:

        resp = HttpResponse()
        data = json.loads(request.body)
        did = data['did']
        password = data['password']

        user = BMGTUser.objects.filter(
            did=did, activated=False, flag_deleted=0)

        if user:
            user = user[0]
            if user and password_valid(password):
                resp.status_code = Status.OK
                user.password = make_password(password)
                user.activated = True
                user.save()
            else:
                resp.status_code = Status.BAD_REQUEST
                resp.write("Sign up failed! Password should contain at least 8 alphanumeric characters!")
        else:
            resp.status_code = Status.NOT_FOUND
            resp.write("Sign up failed! Please check your directory ID!")

        return resp

    @api_error_handler
    @require_POST
    @staticmethod
    def forget_password(request: HttpRequest) -> HttpResponse:

        user_did = request.GET.get('did')
        raise NotImplementedError

    @api_error_handler
    @require_POST
    @staticmethod
    def sign_out(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        Auth.__clear_auth_cookie(resp)
        resp.status_code = Status.OK
        return resp


class UserApi:

    @api_error_handler
    @require_GET
    @staticmethod
    def me(request: HttpRequest,) -> HttpResponse:
        resp = HttpResponse()
        id = request.COOKIES.get('id')
        if id:
            obj = BMGTUser.objects.get(id=id, activated=1, flag_deleted=0)
            resp.write(serialize_model_instance(obj))
            resp.status_code = Status.OK
        else:
            resp.write("Unauthorized!")
            resp.status_code = Status.UNAUTHORIZED

        return resp

    @api_error_handler
    @staticmethod
    def users(request: HttpRequest) -> HttpResponse:
        return generic_unary_query(BMGTUser, request)

    @api_error_handler
    @require_GET
    @staticmethod
    def users_paginated(request: HttpRequest) -> HttpResponse:
        return generic_paginated_fetch(BMGTUser, request)


class GroupApi:

    @api_error_handler
    @staticmethod
    def groups(request: HttpRequest) -> HttpResponse:
        if request.method == 'PUT':
            resp = HttpResponse()
            obj_set = json.loads(request.body)
            if type(obj_set) is not list:
                obj_set= [obj_set]
            [obj.pop('id', None) for obj in obj_set]
            obj_set = [BMGTGroup(**obj) for obj in obj_set]
            count_created = len(BMGTGroup.objects.bulk_create(obj_set))
            resp.write(f'Create success on {count_created} rows!')
            resp.status_code = Status.OK
            return resp
        else:
            return generic_unary_query(BMGTGroup, request)

    @api_error_handler
    @staticmethod
    def groups_info(request: HttpRequest, id) -> HttpResponse:
        resp = HttpResponse()
        if not id:
            resp.write("Bad Request!")
            resp.status_code = Status.BAD_REQUEST
        else:
            users = BMGTUser.objects.filter(group_id=id, activated=1, flag_deleted=0)
            group = BMGTGroup.objects.filter(id=id, flag_deleted=0)
            if group:
                group = group[0]
                group['users'] = serialize_models(users)
                resp.write(serialize_model_instance(group))
                resp.status_code = Status.OK
            else:
                resp.write("Group not found!")
                resp.status_code = Status.NOT_FOUND

        return resp

    @api_error_handler
    @require_GET
    @staticmethod
    def groups_paginated(request: HttpRequest) -> HttpResponse:
        return generic_paginated_fetch(BMGTGroup, request)

    @api_error_handler
    @require_GET
    @staticmethod
    def groups_info_paginated(request: HttpRequest,) -> HttpResponse:
        resp = HttpResponse()

        page = int(request.GET.get('page', default=1))
        page_size = request.GET.get('page_size', default=__DEF_PAGE_SIZE)
        asc = request.GET.get('asc')
        order_by = request.GET.get('order_by', default='id')


        group_set = BMGTGroup.objects.filter(flag_deleted=0)
        pager = Paginator(group_set.order_by(order_by if asc else '-'+order_by), page_size)
        group_set = pager.page(page).object_list
        if group_set:
            group_set = [group.as_dictionary() for group in group_set]
            for group in group_set:
                users = BMGTUser.objects.filter(group_id=group['id'], flag_deleted=0)
                group['users'] = [user.as_dictionary() for user in users]
            resp.write(serialize_models(group_set))
            resp.status_code = Status.OK        
        else:
            resp.write('No group found!')
            resp.status_code = Status.NOT_FOUND

        return resp


class CaseApi:
    @api_error_handler
    @staticmethod
    def cases(request: HttpRequest) -> HttpResponse:
        return generic_unary_query(Case, request)

    @api_error_handler
    @require_GET
    @staticmethod
    def cases_paginated(request: HttpRequest) -> HttpResponse:
        return generic_paginated_fetch(Case, request)

    @api_error_handler
    @require_POST
    @staticmethod
    def run(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        data = json.loads(request.body)
        case_id = data.get('case_id')
        if not case_id:
            resp.status_code = Status.NOT_FOUND
            resp.write("Bad Request!")
        else:
            match case_id:
                case '1':
                    caseInst = FoodCenter(num_iterations=100, centers=[
                                          '13', ], policies=[(100, 3000)])
                    res = caseInst.run('basic')
                    resp.status_code = Status.OK
                    resp.write(json.dumps(res))
                case _:
                    resp.status_code = Status.NOT_FOUND
                    resp.write("Case not found!")

        return resp


class CaseRecordApi:
    @api_error_handler
    @staticmethod
    def case_records(request: HttpRequest) -> HttpResponse:
        return generic_unary_query(CaseRecord, request)

    @api_error_handler
    @require_GET
    @staticmethod
    def case_records_paginated(request: HttpRequest) -> HttpResponse:
        return generic_paginated_fetch(CaseRecord, request)


class TagApi:

    @api_error_handler
    @staticmethod
    def tags(request: HttpRequest) -> HttpResponse:
        return generic_unary_query(Tag, request)

    @api_error_handler
    @require_GET
    @staticmethod
    def tags_paginated(request: HttpRequest) -> HttpResponse:
        return generic_paginated_fetch(Tag, request)


class RoleApi:

    @api_error_handler
    @staticmethod
    def roles(request: HttpRequest) -> HttpResponse:
        return generic_unary_query(Role, request)

    @api_error_handler
    @require_GET
    @staticmethod
    def roles_paginated(request: HttpRequest) -> HttpResponse:
        return generic_paginated_fetch(Role, request)


class ManagementApi:
    @api_error_handler
    @staticmethod
    def import_users(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        if request.body:
            with io.BytesIO(request.body) as file:
                table = pd.read_csv(file)
                table.user_first_name = table.user_first_name.map(
                    lambda x: x.strip())
                table.user_last_name = table.user_last_name.map(
                    lambda x: x.strip())
                obj_set = [BMGTUser(**row) for row in table.to_dict('records')]
                BMGTUser.objects.bulk_create(
                    obj_set, batch_size=__BATCH_QUERY_SIZE)
                resp.status_code = Status.OK
                resp.write("Imported!")
        else:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Bad Request!")

        return resp



class TestApi(object):
    @staticmethod
    def test_lagged(request:HttpRequest) -> HttpResponse:
        """
        enforces a 3-sec time lag before redirecting to the original url
        the original url is the url without the '/test/lag' part
        """
        url = request.get_full_path()
        pattern = r'/test/lagged/(?P<sleep_time>[0-9]+)/'
        search_result =  re.search(pattern, url)
        if search_result:
            time.sleep(int(search_result.group('sleep_time')))
            redir_url = re.sub(pattern, '/', url)
            return redirect(redir_url)
        else:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write("Bad Request!")
            return resp
        