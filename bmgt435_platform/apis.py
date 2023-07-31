from django.http import HttpRequest, HttpResponse
from django.db import IntegrityError
from django.views.decorators.http import require_POST, require_GET,  require_http_methods
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.contrib.auth.hashers import make_password, check_password

from .simulation.Cases import FoodCenter
from .bmgt_models import *
from .statusCode import Status
from .utils.json_utils import serialize_models
from .utils.customExceptions import DataFormatError

import pandas as pd
import regex as re
import json
import io


__DEF_PAGE_SIZE = 10
__BATCH_QUERY_SIZE = 40


def _get_batch_size(list):
    return min(len(list), __BATCH_QUERY_SIZE)


def _api_error_handler(func):
    """
    API level exception handling decorator
    """

    def wrapped(request, **kwargs) -> HttpResponse:
        try:
            return func(request, **kwargs)

        except json.JSONDecodeError as e:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write(e)

        except ObjectDoesNotExist as e:
            resp = HttpResponse()
            resp.status_code = Status.NOT_FOUND
            resp.write(e)

        except MultipleObjectsReturned as e:
            resp = HttpResponse()
            resp.status_code = Status.DATABASE_ERROR
            resp.write(e)

        except IntegrityError as e:
            resp = HttpResponse()
            resp.status_code = Status.INTEGRITY_ISSUE
            resp.write(e)

        except ValidationError as e:
            resp = HttpResponse()
            resp.status_code = Status.VALIDATION_ERROR
            resp.write(e)

        except DataFormatError as e:
            resp = HttpResponse(e)

        except NotImplementedError as e:
            resp = HttpResponse()
            resp.status_code = Status.NOT_IMPLEMENTED
            resp.write(e)

        except:
            raise

        return resp

    return wrapped


def _password_valid(password: str) -> bool:
    """
    password strength validation
    """

    leng_valid = len(password) >= 8
    has_char = bool(re.search(pattern=r'\w', string=password))
    has_num = bool(re.search(pattern=r'\d', string=password))
    return leng_valid and has_char and has_num


def _to_paginator_response(paginator: Paginator, page: int) -> str:
    """
    convert a query set acquired by pagination to a json string
    """

    return json.dumps({
        "page": page,
        "page_size": paginator.per_page,
        "total_page": paginator.num_pages,
        "total_count": paginator.count,
        "has_next": paginator.page(page).has_next(),
        "has_previous": paginator.page(page).has_previous(),
        "data": json.loads(serialize_models(paginator.page(page).object_list)),
    })


def _is_admin(request:HttpRequest) -> bool:
    return request.COOKIES.get('role_id', None) == '1'


def _generic_unary_query(cls, request: HttpRequest,) -> HttpResponse:
    """
    generic query on one table
    """

    resp = HttpResponse()

    if request.method == "GET":

        params = request.GET.dict()
        params['flag_deleted'] = '0'
        obj_set = cls.objects.filter(**params)
        if obj_set:
            resp.write(serialize_models(obj_set))
            resp.status_code = Status.OK
        else:
            resp.status_code = Status.NOT_FOUND
            resp.write("The requested resource does not exist!")

    elif request.method == "DELETE":
        params = request.GET.dict()
        if params:
            obj_set = cls.objects.filter(**params)
            if obj_set:
                for obj in obj_set:
                    obj.flag_deleted = 1
                count_update = cls.objects.bulk_update(
                        obj_set, fields=['flag_deleted'], batch_size=_get_batch_size(obj_set))
                resp.status_code = Status.OK
                resp.write(f"Delete Success on {count_update} Rows!")
            else:
                count_delete = obj_set.delete()
                resp.status_code = Status.OK
                resp.write(f"Delete Success on {count_delete} Rows!")
        else:
            resp.status_code = Status.NOT_FOUND
            resp.write("The requested resource does not exist!")
    elif request.method == "POST":
        obj_set = json.loads(request.body)
        if type(obj_set) is not list:
            obj_set = [obj_set]
        data_valid = all([obj.get('id') and cls.objects.filter(
                id=obj['id'], flag_deleted=0).exists() for obj in obj_set])
        if obj_set:
            if data_valid:
                obj_set = [cls(**obj) for obj in obj_set]
                count_update = cls.objects.bulk_update(
                    obj_set, fields=cls.batch_updatable_fields, batch_size=_get_batch_size(obj_set))
                resp.status_code = Status.UPDATED
                resp.write(f"Update Success on {count_update} Rows!")
            else:
                resp.status_code = Status.BAD_REQUEST
                resp.write("Bad Request!")
        else:
            resp.status_code = Status.NOT_FOUND
            resp.write("The requested resource does not exist!")
    elif request.method == "PUT":
        obj_set = json.loads(request.body)
        if not type(obj_set) is list:
            obj_set = [obj_set]
        data_valid = all([not obj.get('id') for obj in obj_set])
        if obj_set:
            if data_valid:
                obj_set = [cls(**obj) for obj in obj_set]
                obj_created = cls.objects.bulk_create(
                    obj_set, batch_size=_get_batch_size(obj_set))
                count_created = len(obj_created)
                resp.status_code = Status.CREATED
                resp.write(f"Create Success on {count_created} Rows!")
            else:
                resp.status_code = Status.DATA_FORMAT_ERROR
                resp.write(
                    "Format of the provided data do not meet the requirements!")
        else:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Bad Request!")
    else:
        resp.status_code = Status.METHOD_NOT_ALLOWED
        resp.write("Method Not Allowed!")
    return resp



def _generic_paginated_select(cls, request: HttpRequest,) -> HttpResponse:
    resp = HttpResponse()
    is_admin = _is_admin(request)

    params = request.GET.dict()
    page = params.pop('page', default=1)
    page_size = params.pop('page_size', default=__DEF_PAGE_SIZE)
    asc = params.pop('asc', default=True)
    order_by = params.pop('order_by', default='id')


    if not is_admin:
        params['flag_deleted'] = '0'
    obj_set = cls.objects.filter(**params)
    pager = Paginator(obj_set.order_by(
        order_by if asc else '-'+order_by), page_size)

    if page > pager.num_pages:
        resp.status_code = Status.NOT_FOUND
        resp.write("Page not found!")
    else:
        resp.status_code = Status.OK
        resp.write(_to_paginator_response(pager, page))
    return resp




class Auth:

    @staticmethod
    def __set_auth_cookie(response: HttpResponse, user: BMGTUser) -> None:
        response.set_cookie('id', str(user.id), samesite='none', secure=True)
        response.set_cookie('role_id', user.role_id, samesite='none', secure=True)

    @_api_error_handler
    @require_POST
    @staticmethod
    def sign_in(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        data = json.loads(request.body)
        user_did = data['user_did']
        user_password = data['user_password']

        user = BMGTUser.objects.get(user_did=user_did, user_activated=True, flag_deleted=0)

        if user and user.password and check_password(user_password, user.password):
            resp.status_code = Status.OK
            Auth.__set_auth_cookie(resp, user)
            resp.write(serialize_models([user]))
        else:
            resp.status_code = Status.PASSWORD_ISSUE
            resp.write(
                "Sign in failed. Please check your directory ID and password!")

        return resp

    @_api_error_handler
    @require_POST
    @staticmethod
    def sign_up(request: HttpRequest) -> HttpResponse:

        resp = HttpResponse()
        data = json.loads(request.body)
        user_did = data['user_did']
        user_password = data['user_password']

        user = BMGTUser.objects.get(
            user_did=user_did, user_activated=False, flag_deleted=0)

        if user and _password_valid(user_password):
            resp.status_code = Status.OK
            user.password = make_password(user_password)
            user.activated = True
            user.save()
        else:
            resp.status_code = Status.ACCOUNT_ISSUE
            resp.write("Sign up failed! Please check your directory ID!")

        return resp

    @_api_error_handler
    @require_POST
    @staticmethod
    def forget_password(request: HttpRequest) -> HttpResponse:

        user_did = request.GET.get('user_did')
        raise NotImplementedError


class UserApi:

    @_api_error_handler
    @require_GET
    @staticmethod
    def me(request: HttpRequest,) -> HttpResponse:
        resp = HttpResponse()
        id = request.COOKIES.get('id')
        if id:
            obj = BMGTUser.objects.get(id=id, activated=1, flag_deleted=0)
            resp.write(serialize_models([obj]))
            resp.status_code = Status.OK
        else:
            resp.write("Unauthorized!")
            resp.status_code = Status.UNAUTHORIZED

        return resp

    @_api_error_handler
    @staticmethod
    def users(request: HttpRequest) -> HttpResponse:
        return _generic_unary_query(BMGTUser, request)

    @_api_error_handler
    @require_GET
    @staticmethod
    def user_paginated(request: HttpRequest) -> HttpResponse:
        return _generic_paginated_select(BMGTUser, request)


class GroupApi:

    @_api_error_handler
    @staticmethod
    def groups(request: HttpRequest) -> HttpResponse:
        return _generic_unary_query(BMGTGroup, request)

    @_api_error_handler
    @staticmethod
    def me(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        user_id = request.COOKIES.get('id')
        if user_id:
            user = BMGTUser.objects.get(id=user_id, activated=1, flag_deleted=0)
            obj = BMGTGroup.objects.get(id=user.group_id, activated=1, flag_deleted=0)
            resp.write(serialize_models([obj]))
            resp.status_code = Status.OK
        else:
            resp.write("Unauthorized!")
            resp.status_code = Status.UNAUTHORIZED

        return resp

    @_api_error_handler
    @require_GET
    @staticmethod
    def groups_paginated(request: HttpRequest) -> HttpResponse:
        return _generic_paginated_select(BMGTGroup, request)

    @_api_error_handler
    @require_GET
    @staticmethod
    def groups_users_paginated(request: HttpRequest,) -> HttpResponse:
        resp = HttpResponse()

        page = int(request.GET.get('page', default=1))
        page_size = request.GET.get('page_size', default=__DEF_PAGE_SIZE)
        asc = request.GET.get('asc')
        order_by = request.GET.get('order_by', default='id')


        group_set = BMGTGroup.objects.filter(flag_deleted=0)
        pager = Paginator(group_set.order_by(order_by if asc else '-'+order_by), page_size)
        group_set = pager.page(page).object_list
        if group_set:
            group_set = [group.as_serializable() for group in group_set]
            for group in group_set:
                users = BMGTUser.objects.filter(group_id=group['id'], flag_deleted=0)
                group['users'] = [user.as_serializable() for user in users]
            resp.write(serialize_models(group_set))
            resp.status_code = Status.OK        
        else:
            resp.write('No group found!')
            resp.status_code = Status.NOT_FOUND

        return resp


class CaseApi:
    @_api_error_handler
    @staticmethod
    def cases(request: HttpRequest) -> HttpResponse:
        return _generic_unary_query(Case, request)

    @_api_error_handler
    @require_GET
    @staticmethod
    def cases_paginated(request: HttpRequest) -> HttpResponse:
        return _generic_paginated_select(Case, request)

    @_api_error_handler
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
    @_api_error_handler
    @staticmethod
    def case_records(request: HttpRequest) -> HttpResponse:
        return _generic_unary_query(CaseRecord, request)

    @_api_error_handler
    @require_GET
    @staticmethod
    def case_records_paginated(request: HttpRequest) -> HttpResponse:
        return _generic_paginated_select(CaseRecord, request)


class TagApi:

    @_api_error_handler
    @staticmethod
    def tags(request: HttpRequest) -> HttpResponse:
        return _generic_unary_query(Tag, request)

    @_api_error_handler
    @require_GET
    @staticmethod
    def tags_paginated(request: HttpRequest) -> HttpResponse:
        return _generic_paginated_select(Tag, request)


class RoleApi:

    @_api_error_handler
    @staticmethod
    def roles(request: HttpRequest) -> HttpResponse:
        return _generic_unary_query(Role, request)

    @_api_error_handler
    @require_GET
    @staticmethod
    def roles_paginated(request: HttpRequest) -> HttpResponse:
        return _generic_paginated_select(Role, request)


class ManagementApi:
    @_api_error_handler
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
