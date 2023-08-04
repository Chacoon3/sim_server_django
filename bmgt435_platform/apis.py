from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST, require_GET,  require_http_methods
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password, check_password

from .simulation.Cases import FoodCenter
from .bmgtModels import *
from .utils.statusCode import Status
from .utils.jsonUtils import serialize_models, serialize_model_instance, serialize_simulations
from .utils.apiUtils import api_error_handler, password_valid, generic_unary_query, generic_paginated_fetch, get_paginator_params

import pandas as pd
import json
import io



class AuthApi:

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
                AuthApi.__set_auth_cookie(resp, user)
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
        AuthApi.__clear_auth_cookie(resp)
        resp.status_code = Status.OK
        return resp


class UserApi:

    @api_error_handler
    @require_GET
    @staticmethod
    def me(request: HttpRequest,) -> HttpResponse:
        resp = HttpResponse()
        id = request.COOKIES.get('id', None) if request.COOKIES else None
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
        if request.method == 'POST':
            resp = HttpResponse()
            user_id = request.COOKIES.get('id', None)
            user = BMGTUser.objects.filter(id=user_id, activated=1, flag_deleted=0)
            if user_id and len(user) == 1:
                user = user[0];
                if user.group_id == None:
                    data = json.loads(request.body)
                    name = data['name']
                    group = BMGTGroup(name=name,)
                    group.save()
                    user.gourp_id = group.id
                    resp.write("Created group successfully!")
                    resp.status_code = Status.CREATED
                else:
                    resp.write("User already has a group!")
                    resp.status_code = Status.BAD_REQUEST
            else:
                resp.write("User unauthorized!")
                resp.status_code = Status.UNAUTHORIZED    
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
    def groups_paginated(request: HttpRequest,) -> HttpResponse:
        # resp = HttpResponse()

        # pager_params = get_paginator_params(request)

        # group_set = BMGTGroup.objects.filter(flag_deleted=0)
        # pager = Paginator(group_set.order_by(pager_params['order'] if pager_params['asc'] else '-'+pager_params['order']), pager_params['size'])
        # group_set = pager.page(pager_params['page']).object_list
        # if group_set:
        #     resp.write(serialize_models(group_set))
        #     resp.status_code = Status.OK        
        # else:
        #     resp.write('No group found!')
        #     resp.status_code = Status.NOT_FOUND

        return generic_paginated_fetch(BMGTGroup, request)


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
                    obj_set, batch_size=10)
                resp.status_code = Status.OK
                resp.write("Imported!")
        else:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Bad Request!")

        return resp