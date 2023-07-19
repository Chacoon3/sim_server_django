from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.core import serializers
from django.core.paginator import Paginator
from .bmgt_models import *

import json


DEF_PAGE_SIZE = 10

def api_error_handler(func):

    def wrapped(request) -> HttpResponse:
        try:
            return func(request)
        
        except (models.Model.DoesNotExist, User.MultipleObjectsReturned):
            resp = HttpResponse()
            resp.status_code = 404
            resp.write("Object Not Found!")

        
        except (KeyError, json.JSONDecodeError):
            resp = HttpResponse()
            resp.status_code = 400
            resp.write("Bad Request!")

        except NotImplementedError:
            resp = HttpResponse()
            resp.status_code = 501
            resp.write("Not Implemented!")

        except:
            raise   # re-raise the exception

        return resp

    return wrapped


def to_paginator_response_json(paginator: Paginator, page: int) -> str:
    """
    converts a query set acquired by pagination to a json string
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


class UserApi:

    __field_user_did = "user_did"
    __field_user_password = "user_password"



    @api_error_handler
    @require_POST
    @staticmethod
    def sign_in(request: HttpRequest) -> HttpResponse:

        resp = HttpResponse()
        data = json.loads(request.body)
        user_did = data[UserApi.__field_user_did]
        user_password = data[UserApi.__field_user_password]
        queryRes = User.objects.filter(
                user_did=user_did, 
                user_activated = True,
                user_password=user_password
            )
        
        if queryRes.count() == 1:
            resp.status_code = 200
            resp.set_cookie(UserApi.__field_user_did, user_did)
        else:
            resp.status_code = 401
            resp.write("Sign in failed. Please check your directory ID and password!")

        return resp

    @api_error_handler
    @require_POST
    @staticmethod
    def sign_up(request: HttpRequest) -> HttpResponse:

        resp = HttpResponse()
        data = json.loads(request.body)
        user_did = data[UserApi.__field_user_did]
        user_password = data[UserApi.__field_user_password]
        queryRes = User.objects.filter(
            user_did=user_did,
            user_activated = False
        )
        
    
        if queryRes.count() == 1:
            resp.status_code = 200
            queryRes[0].user_password = user_password
            queryRes[0].user_activated = True
            queryRes[0].save()
        else:
            resp.status_code = 401
            resp.write("Sign up failed! Please check your directory ID!")

        return resp

    @api_error_handler
    @require_GET
    @staticmethod
    def forget_password(request: HttpRequest) -> HttpResponse:

        user_did=request.GET.get(UserApi.__field_user_did,default='')
        raise NotImplementedError

    
    @api_error_handler
    @require_GET
    @staticmethod
    def get_user_info(request):
        resp = HttpResponse()
        user_did=request.GET.get('user_did')
        if not user_did:
            resp.status_code = 400
            resp.write("Bad Request!")
        else:
            queryRes = User.objects.filter(user_did=user_did)
            if queryRes.count() == 1:
                resp.status_code = 200
                resp.write(serializers.serialize('json', queryRes))
            else:
                resp.status_code = 404
                resp.write("User not found!")
        return resp


    @api_error_handler
    @require_GET
    @staticmethod
    def get_user_list(request: HttpRequest)-> HttpResponse:
        resp = HttpResponse()

        page=int(request.GET.get('page', default=1))
        page_size=request.GET.get('page_size', default=DEF_PAGE_SIZE)
        asc=request.GET.get('asc')
        order_by=request.GET.get('order_by', default=UserApi.__field_user_did)

        pager = Paginator(
                User.objects.all().order_by(order_by if asc else '-'+order_by), 
                page_size
            )
        
        if page > pager.num_pages:
            resp.status_code = 404
            resp.write("Page not found!")
        else:
            resp.status_code = 200
            resp.write(to_paginator_response_json(pager, page))
        return resp


class GroupApi:
    @api_error_handler
    @require_GET
    @staticmethod
    def get_group_info(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        group_id=request.GET.get('group_id')

        if not group_id:
            resp.status_code = 400
            resp.write("Bad Request!")
        else:
            queryRes = Group.objects.filter(group_id=group_id)
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
                Group.objects.all().order_by(order_by if asc else '-'+order_by), 
                page_size
            )
        
        if page > pager.num_pages:
            resp.status_code = 404
            resp.write("Page not found!")
        else:
            resp.status_code = 200
            resp.write(to_paginator_response_json(pager, page))
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
        asc=request.GET.get('asc')
        order_by=request.GET.get('order_by', default=UserApi.__field_user_did)

        pager = Paginator(
                Case.objects.all().order_by(order_by if asc else '-'+order_by), 
                page_size
            )
        
        if page > pager.num_pages:
            resp.status_code = 404
            resp.write("Page not found!")
        else:
            resp.status_code = 200
            resp.write(to_paginator_response_json(pager, page))
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
        order_by=request.GET.get('order_by', default=UserApi.__field_user_did)

        pager = Paginator(
                CaseRecord.objects.all().order_by(order_by if asc else '-'+order_by),
                page_size
            )
        
        if page > pager.num_pages:
            resp.status_code = 404
            resp.write("Page not found!")
        else:
            resp.status_code = 200
            resp.write(to_paginator_response_json(pager, page))
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
            resp.write(to_paginator_response_json(pager, page))
        return resp