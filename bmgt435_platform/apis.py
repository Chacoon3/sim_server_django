from django.http import HttpRequest, HttpResponse
from django.db import IntegrityError
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.hashers import make_password, check_password

from .simulation.Cases import FoodCenter
from .bmgt_models import *
from .statusCode import Status
from .utils.json_utils import serialize_models

import pandas as  pd
import regex as re
import json
import io


__DEF_PAGE_SIZE = 10
__BATCH_QUERY_SIZE = 40



def _api_error_handler(func):
    """
    API level exception handling decorator
    """

    def wrapped(request, **kwargs) -> HttpResponse:
        try:
            return func(request, **kwargs)

        except json.JSONDecodeError:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write("Invalid data format!")

        except ObjectDoesNotExist:
            resp = HttpResponse()
            resp.status_code = Status.NOT_FOUND
            resp.write("The requested resource does not exist!")

        except MultipleObjectsReturned:
            resp = HttpResponse()
            resp.status_code = Status.DATABASE_ERROR
            resp.write("Multiple objects found while singular is expected!")

        except IntegrityError:
            resp = HttpResponse()
            resp.status_code = Status.INTEGRITY_ISSUE
            resp.write("The requested resource already exists!")

        except NotImplementedError:
            resp = HttpResponse()
            resp.status_code = Status.NOT_IMPLEMENTED
            resp.write("The feature is not implemented!")

        except:
            raise

        return resp

    return wrapped


def __password_valid(password:str) -> bool:
    """
    password strength validation
    """

    leng_valid = len(password) >= 8
    has_char = bool(re.search(pattern=r'\w', string=password))
    has_num = bool(re.search(pattern=r'\d', string=password))
    return leng_valid and has_char and has_num


def __to_paginator_response(paginator: Paginator, page: int) -> str:
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


def __generic_query(cls, request: HttpRequest, is_admin = False) -> HttpResponse:

    resp = HttpResponse()

    if request.method == "GET":
        params = request.GET.dict()
        if not is_admin:
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
                if not is_admin:
                    for obj in obj_set:
                        obj.flag_deleted = 1
                    count_update = cls.objects.bulk_update(obj_set, fields=['flag_deleted'], batch_size = __BATCH_QUERY_SIZE)
                    resp.status_code = Status.OK
                    resp.write(f"Delete Success on {count_update} Rows!")
                else:
                    count_delete = obj_set.delete()
                    resp.status_code = Status.OK
                    resp.write(f"Delete Success on {count_delete} Rows!")
            else:
                resp.status_code = Status.NOT_FOUND
                resp.write("The requested resource does not exist!")
        else:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Bad Request!")
    elif request.method == "POST":
        obj_set = json.loads(request.body)
        if not is_admin:
            data_valid = all([obj.get('id') and cls.objects.filter(id=obj['id'], flag_deleted = 0).exists() for obj in obj_set])
        else:
            data_valid = all([obj.get('id') and cls.objects.filter(id=obj['id']).exists() for obj in obj_set])
        if obj_set and data_valid:
            obj_set = [cls(**obj) for obj in obj_set]
            count_update = cls.objects.bulk_update(obj_set, fields=cls.batch_updatable_fields, batch_size = __BATCH_QUERY_SIZE)
            resp.status_code = Status.UPDATED
            resp.write(f"Update Success on {count_update} Rows!")
        else:
            resp.status_code = Status.NOT_FOUND
            resp.write("The requested resource does not exist!")
    elif request.method == "PUT":
        obj_set = json.loads(request.body)
        data_valid = all([not obj.get('id') for obj in obj_set])
        if obj_set and data_valid:
            obj_set = [cls(**obj) for obj in obj_set]
            obj_created = cls.objects.bulk_create(obj_set, update_fields = cls.batch_updatable_fields, batch_size = __BATCH_QUERY_SIZE)
            count_created = len(obj_created)
            resp.status_code = Status.CREATED
            resp.write(f"Create Success on {count_created} Rows!")
        else:
            resp.status_code = Status.NOT_FOUND
            resp.write("The requested resource does not exist!")
    else:
        resp.status_code = Status.METHOD_NOT_ALLOWED
        resp.write("Method Not Allowed!")
    return resp    


def __generic_paginated_fetch(cls, request: HttpRequest, is_admin = False) -> HttpResponse:
    resp = HttpResponse()

    page = int(request.GET.get('page', default=1))
    page_size = request.GET.get('page_size', default=__DEF_PAGE_SIZE)
    asc = request.GET.get('asc')
    order_by = request.GET.get('order_by', default='id')

    if is_admin:
        obj_set = cls.objects.all()
    else:
        obj_set = cls.objects.filter(flag_deleted = 0)
    pager = Paginator(obj_set.order_by(order_by if asc else '-'+order_by), page_size)

    if page > pager.num_pages:
        resp.status_code = 404
        resp.write("Page not found!")
    else:
        resp.status_code = 200
        resp.write(__to_paginator_response(pager, page))
    return resp



class Auth:

    @staticmethod
    def __set_auth_cookie(response: HttpResponse, user: BMGTUser) -> None:
        response.set_cookie('id', str(user.id), samesite='none', secure= True)


    @_api_error_handler
    @require_POST
    @staticmethod
    def sign_in(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        data = json.loads(request.body)
        user_did = data['user_did']
        user_password = data['user_password']

        user = BMGTUser.objects.get(user_did=user_did, user_activated=True, flag_deleted = 0)

        if user and user.password and  check_password(user_password, user.password):
            resp.status_code = Status.OK
            Auth.__set_auth_cookie(resp, user)                
            resp.write(serialize_models([user]))
        else:
            resp.status_code = Status.PASSWORD_ISSUE
            resp.write("Sign in failed. Please check your directory ID and password!")

        return resp

    @_api_error_handler
    @require_POST
    @staticmethod
    def sign_up(request: HttpRequest) -> HttpResponse:

        resp = HttpResponse()
        data = json.loads(request.body)
        user_did = data['user_did']
        user_password = data['user_password']

        user = BMGTUser.objects.get(user_did=user_did, user_activated=False, flag_deleted = 0)

        if user and __password_valid(user_password):
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

        user_did=request.GET.get('user_did')
        raise NotImplementedError


class UserApi:

    @_api_error_handler
    @require_GET
    @staticmethod
    def me(request: HttpRequest,) -> HttpResponse:
        resp = HttpResponse()
        id = request.COOKIES.get('id')
        if id:
            obj = BMGTUser.objects.get(id=id, user_activated=True, flag_deleted = 0)
            resp.write(serialize_models([obj]))
            resp.status_code = Status.OK
        else:
            resp.status_code = Status.UNAUTHORIZED
            resp.write("Unauthorized!")

        return resp
    

    @_api_error_handler
    @staticmethod
    def users(request: HttpRequest) -> HttpResponse:
        return __generic_query(BMGTUser, request)


    @_api_error_handler
    @require_GET
    @staticmethod
    def user_paginated(request: HttpRequest)-> HttpResponse:
        return __generic_paginated_fetch(BMGTUser, request)


class GroupApi:
    
    @_api_error_handler
    @staticmethod
    def groups(request: HttpRequest) -> HttpResponse:
        return __generic_query(BMGTGroup, request)


    @_api_error_handler
    @require_GET
    @staticmethod
    def groups_paginated(request: HttpRequest)-> HttpResponse:
        return __generic_paginated_fetch(BMGTGroup, request)
    

class CaseApi:
    @_api_error_handler
    @staticmethod
    def cases(request: HttpRequest) -> HttpResponse:
        return __generic_query(Case, request)
    

    @_api_error_handler
    @require_GET
    @staticmethod
    def cases_paginated(request: HttpRequest)-> HttpResponse:
        return __generic_paginated_fetch(Case, request)


    @_api_error_handler
    @require_POST
    @staticmethod
    def run(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        data = json.loads(request.body)
        case_id=data.get('case_id')
        if not case_id:
            resp.status_code = Status.NOT_FOUND
            resp.write("Bad Request!")
        else:
            match case_id:
                case '1':
                    caseInst = FoodCenter(num_iterations=100, centers=['13',], policies=[(100, 3000)])
                    res =caseInst.run('basic')
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
        return __generic_query(CaseRecord, request)
    
    @_api_error_handler
    @require_GET
    @staticmethod
    def case_records_paginated(request: HttpRequest)-> HttpResponse:
        return __generic_paginated_fetch(CaseRecord, request)


class TagApi:    

    @_api_error_handler
    @staticmethod
    def tags(request: HttpRequest) -> HttpResponse:
        return __generic_query(Tag, request)
    

    @_api_error_handler
    @require_GET
    @staticmethod
    def tags_paginated(request: HttpRequest) -> HttpResponse:
        return __generic_paginated_fetch(Tag, request)


class RoleApi:

    @_api_error_handler
    @staticmethod
    def roles(request: HttpRequest) -> HttpResponse:
        return __generic_query(Role, request)
    

    @_api_error_handler
    @require_GET
    @staticmethod
    def roles_paginated(request: HttpRequest) -> HttpResponse:
        return __generic_paginated_fetch(Role, request)


class ManagementApi:
    @_api_error_handler
    @staticmethod
    def import_users(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        if request.body:
            with io.BytesIO(request.body) as file:
                table = pd.read_csv(file)
                table.user_first_name = table.user_first_name.map(lambda x: x.strip())
                table.user_last_name = table.user_last_name.map(lambda x: x.strip())
                obj_set = [BMGTUser(**row) for row in table.to_dict('records')]
                BMGTUser.objects.bulk_create(obj_set, batch_size=__BATCH_QUERY_SIZE)
                resp.status_code = Status.OK
                resp.write("Imported!")
        else:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Bad Request!")

        return resp