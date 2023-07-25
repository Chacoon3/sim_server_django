from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.core import serializers
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password, check_password, is_password_usable
from .simulation.Cases import FoodCenter
from .bmgt_models import *
from .statusCode import Status
from .utils.query import Query


import regex as re
import json


DEF_PAGE_SIZE = 10


def api_error_handler(func):
    """
    API level exception handling decorator
    """

    def wrapped(request, **kwargs) -> HttpResponse:
        try:
            return func(request, **kwargs)

        except (KeyError, json.JSONDecodeError):
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write("Invalid data format! This could be issues with the website itself. Please contact the administrator.")

        except NotImplementedError:
            resp = HttpResponse()
            resp.status_code = Status.NOT_IMPLEMENTED
            resp.write("The feature is not implemented!")

        except:
            raise

        return resp

    return wrapped


def is_password_valid(password:str) -> bool:
    """
    password strength validation
    """

    leng_valid = len(password) >= 8
    has_char = bool(re.search(pattern=r'\w', string=password))
    has_num = bool(re.search(pattern=r'\d', string=password))
    return leng_valid and has_char and has_num


def to_paginator_response(paginator: Paginator, page: int) -> str:
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
        "data": json.loads(serializers.serialize("json", paginator.page(page).object_list)),
    })



class Auth:

    @staticmethod
    def set_auth_cookie(response: HttpResponse, user: BMGTUser) -> None:
        response.set_cookie('user_did', user.user_did, samesite='none', secure= True)
        response.set_cookie('user_name', user.full_name(), samesite='none', secure= True)
        response.set_cookie('group_id', str(user.group_id), samesite='none', secure= True)


    @api_error_handler
    @require_POST
    @staticmethod
    def sign_in(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        data = json.loads(request.body)
        user_did = data['user_did']
        user_password = data['user_password']
        user = BMGTUser.objects.filter(
            id = user_did, user_password = user_password, user_activated = True
        ).get()
        
        if user:
            resp.status_code = Status.OK
            Auth.set_auth_cookie(resp, user)                
            resp.write(serializers.serialize('json', [user]))
        else:
            resp.status_code = Status.PASSWORD_ISSUE
            resp.write("Sign in failed. Please check your directory ID and password!")

        return resp

    @api_error_handler
    @require_POST
    @staticmethod
    def sign_up(request: HttpRequest) -> HttpResponse:

        resp = HttpResponse()
        data = json.loads(request.body)
        user_did = data['user_did']
        user_password = data['user_password']

        user = BMGTUser.objects.filter(
            user_did=user_did,
            user_activated = False
        ).get()
        
    
        if user:

            if is_password_valid(user_password):
                resp.status_code = Status.OK
                user.user_password = make_password(user_password)
                user.user_activated = True
                user.save()
            else:
                resp.status_code = Status.PASSWORD_ISSUE
                resp.write("Sign up failed! Password must contain at least 8 characters, including at least one letter and one number!")
        else:
            resp.status_code = Status.ACCOUNT_ISSUE
            resp.write("Sign up failed! Please check your directory ID!")

        return resp

    @api_error_handler
    @require_GET
    @staticmethod
    def forget_password(request: HttpRequest) -> HttpResponse:

        user_did=request.GET.get(UserApi.field_user_did,default='')
        raise NotImplementedError




class UserApi:

    field_user_did = "user_did"
    field_user_password = "user_password"
    field_user_group_id = "group_id"


    @api_error_handler
    @require_GET
    @staticmethod
    def me(request: HttpRequest,) -> HttpResponse:
        resp = HttpResponse()
        id = request.COOKIES.get('id')
        if id:
            user = BMGTUser.objects.filter(id=id).get()
            if user:
                resp.write(serializers.serialize('json', [user]))
                resp.status_code = Status.OK
            else:
                resp.status_code = Status.NOT_FOUND
                resp.write("User not found!")
        else:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Bad Request!")

        return resp
    

    @api_error_handler
    @require_http_methods(["GET", "POST"])
    @staticmethod
    def users(request: HttpRequest, id = None,) -> HttpResponse:
        resp = HttpResponse()

        if request.method == "GET":
            if id:
                user = BMGTUser.objects.filter(id=id).get()
                if user:
                    resp.status_code = Status.OK
                    resp.write(serializers.serialize('json', [user]))
                else:
                    resp.status_code = Status.NOT_FOUND
                    resp.write("User not found!")
            else:
                user_set = BMGTUser.objects.all()
                resp.status_code = Status.OK
                resp.write(serializers.serialize('json', user_set))
        elif request.method == "POST":
            user_set = serializers.deserialize('json', request.body)
            if user_set:
                for user in user_set:
                    user.save()
                resp.status_code = Status.OK
            else:
                resp.status_code = Status.BAD_REQUEST
                resp.write("Bad Request!")
        else:
            resp.status_code = Status.METHOD_NOT_ALLOWED
            resp.write("Method Not Allowed!")
        return resp


    @api_error_handler
    @require_GET
    @staticmethod
    def user_paginated(request: HttpRequest)-> HttpResponse:
        resp = HttpResponse()

        page=int(request.GET.get('page', default=1))
        page_size=request.GET.get('page_size', default=DEF_PAGE_SIZE)
        asc=request.GET.get('asc')
        order_by=request.GET.get('order_by', default=UserApi.field_user_did)

        pager = Paginator(
                BMGTUser.objects.all().order_by(order_by if asc else '-'+order_by), 
                page_size
            )
        
        if page > pager.num_pages:
            resp.status_code = 404
            resp.write("Page not found!")
        else:
            resp.status_code = 200
            resp.write(to_paginator_response(pager, page))
        return resp


class GroupApi:
    """
    this is for the custom BMGT group model rather than the default Django group model
    """
    
    @api_error_handler
    @require_GET
    @staticmethod
    def get_group_info(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        group_id=request.GET.get('group_id')

        if not group_id:
            resp.status_code = 400
            resp.write("Invalid parameters!")
        else:
            queryRes = BMGTGroup.objects.filter(group_id=group_id)
            if queryRes.count() == 1:
                resp.status_code = 200
                resp.write(serializers.serialize('json', queryRes))
            else:
                resp.status_code = 404
                resp.write("Group not found!")
        return resp
    

    @api_error_handler
    @require_GET
    @staticmethod
    def get_group_list(request: HttpRequest)-> HttpResponse:
        resp = HttpResponse()
        
        page=int(request.GET.get('page', default=1))
        page_size=request.GET.get('page_size', default=DEF_PAGE_SIZE)
        asc=request.GET.get('asc')
        order_by=request.GET.get('order_by', default='group_id')

        pager = Paginator(
                BMGTGroup.objects.all().order_by(order_by if asc else '-'+order_by), 
                page_size
            )
        
        if page > pager.num_pages:
            resp.status_code = 404
            resp.write("Page not found!")
        else:
            resp.status_code = 200
            resp.write(to_paginator_response(pager, page))
        return resp


class CaseApi:
    @api_error_handler
    @require_GET
    @staticmethod
    def get_case_info(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        case_id=request.GET.get('case_id')

        if not case_id or case_id == '':
            resp.status_code = 400
            resp.write("Bad Request!")
        else:
            queryRes = Case.objects.filter(case_id=case_id)
            if queryRes.count() == 1:
                resp.status_code = 200
                resp.write(serializers.serialize('json', queryRes))
            else:
                resp.status_code = 404
                resp.write("Case not found!")
        return resp
    

    @api_error_handler
    @require_GET
    @staticmethod
    def get_case_list(request: HttpRequest)-> HttpResponse:
        resp = HttpResponse()
        
        page=int(request.GET.get('page', default=1))
        page_size=request.GET.get('page_size', default=DEF_PAGE_SIZE)
        asc=request.GET.get('asc', default= True)
        order_by=request.GET.get('order_by', default='case_id')

        pager = Paginator(
                Case.objects.all().order_by(order_by if asc else '-'+order_by), 
                page_size
            )
        
        if page > pager.num_pages:
            resp.status_code = 404
            resp.write("Page not found!")
        else:
            resp.status_code = 200
            resp.write(to_paginator_response(pager, page))
        return resp


    @api_error_handler
    @require_POST
    @staticmethod
    def run_case(request: HttpRequest) -> HttpResponse:
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
    @api_error_handler
    @require_GET
    @staticmethod
    def get_case_record_info(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()

        case_id=request.GET.get('case_id')

        if not case_id or case_id == '':
            resp.status_code = 400
            resp.write("Bad Request!")
        else:
            queryRes = CaseRecord.objects.filter(case_id=case_id)
            if queryRes.count() == 1:
                resp.status_code = 200
                resp.write(serializers.serialize('json', queryRes))
            else:
                resp.status_code = 404
                resp.write("Case record not found!")
        return resp
    

    @api_error_handler
    @require_GET
    @staticmethod
    def get_case_record_list(request: HttpRequest)-> HttpResponse:
        resp = HttpResponse()

        page=int(request.GET.get('page', default=1))
        page_size=request.GET.get('page_size', default=DEF_PAGE_SIZE)
        asc=request.GET.get('asc')
        order_by=request.GET.get('order_by', default=UserApi.field_user_did)

        pager = Paginator(
                CaseRecord.objects.all().order_by(order_by if asc else '-'+order_by),
                page_size
            )
        
        if page > pager.num_pages:
            resp.status_code = 404
            resp.write("Page not found!")
        else:
            resp.status_code = 200
            resp.write(to_paginator_response(pager, page))
        return resp


class TagApi:
    @api_error_handler
    @require_POST
    @staticmethod
    def add_tag(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        tag_name=request.POST.get('tag_name')

        if not tag_name or tag_name == '':
            resp.status_code = 400
            resp.write("Bad Request!")
        else:
            tag = Tag(tag_name=tag_name)
            tag.save()
            resp.status_code = 200
            resp.write(serializers.serialize('json', [tag]))
        return resp
    

    @api_error_handler
    @require_GET
    @staticmethod
    def get_tag_info(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        tag_id=request.GET.get('tag_id')

        if not tag_id or tag_id == '':
            resp.status_code = 400
            resp.write("Bad Request!")
        else:
            queryRes = Tag.objects.filter(tag_id=tag_id)
            if queryRes.count() == 1:
                resp.status_code = 200
                resp.write(serializers.serialize('json', queryRes))
            else:
                resp.status_code = 404
                resp.write("Tag not found!")

        return resp
    

    @api_error_handler
    @require_GET
    @staticmethod
    def get_tag_list(request: HttpRequest)-> HttpResponse:
        resp = HttpResponse()
        
        page=int(request.GET.get('page', default=1))
        page_size=request.GET.get('page_size', default=DEF_PAGE_SIZE)
        asc=request.GET.get('asc')
        order_by=request.GET.get('order_by', default='tag_id')

        pager = Paginator(
                Tag.objects.all().order_by(order_by if asc else '-'+order_by), 
                page_size
            )
        
        if page > pager.num_pages:
            resp.status_code = 404
            resp.write("Page not found!")
        else:
            resp.status_code = 200
            resp.write(to_paginator_response(pager, page))
        return resp