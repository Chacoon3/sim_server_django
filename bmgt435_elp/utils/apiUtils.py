from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.db import IntegrityError
from django.core.paginator import Paginator, EmptyPage
from django.http import HttpRequest, HttpResponse
from http import HTTPStatus
from .jsonUtils import CustomJSONEncoder
from ..simulation.Core import SimulationException
from ..bmgtModels import BMGTTransaction

import regex as re
import json


__BATCH_QUERY_SIZE = 40


def get_batch_size(listObj):
    return min(len(listObj), __BATCH_QUERY_SIZE)


def request_error_handler(func):
    """
    API level exception handling
    """

    def wrapped(request, *args, **kwargs) -> HttpResponse:
        try:
            return func(request, *args, **kwargs)

        except json.JSONDecodeError as e:
            resp = AppResponse()
            resp.reject(e.args[0])

        except ObjectDoesNotExist as e:
            resp = AppResponse()
            resp.reject(e.args[0])

        except MultipleObjectsReturned as e:
            resp = AppResponse()
            resp.reject(e.args[0])

        except KeyError as e:
            resp = AppResponse()
            resp.reject(f'Key missing: {e.args[0]}')

        except IntegrityError as e:
            resp = AppResponse()
            resp.reject(e.args[0])

        except ValidationError as e:
            resp = AppResponse()
            resp.reject(e.args[0])

        except NotImplementedError as e:
            resp = AppResponse()
            resp.reject(e.args[0])

        except SimulationException as e:
            resp = AppResponse()
            resp.reject(e.args[0])

        except ValueError as e:
            resp = AppResponse()
            resp.reject(e.args[0])
            
        except Exception as e:
            # resp = HttpResponse()
            # resp.reject(e.args[0])
            # resp.status_code = HTTPStatus.INTERNAL_SERVER_ERROR

            # if settings.DEBUG:
            raise
            # else:
                # resp = HttpResponse()
                # resp.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                # resp.write("Internal server error!")
        
        return resp

    return wrapped


def password_valid(password: str) -> bool:
    """
    password strength validation
    """

    leng_valid = len(password) >= 8 and len(password) <= 20
    has_char = bool(re.search(pattern=r'\w', string=password))
    has_num = bool(re.search(pattern=r'\d', string=password))
    return leng_valid and has_char and has_num


def create_pager_params(page: int, size: int, asc: int, order: str) -> dict:
    """
    convert get parameters to pagination parameters for paginated query
    """

    params = {}
    params['page'] = page
    params['size'] = size
    params['asc'] = asc
    params['order'] = order
    return params


def pager_params_from_request(request: HttpRequest) -> dict:
    """
    convert get parameters to pagination parameters for paginated query
    """

    params = {}
    params['page'] = request.GET.get('page', None)
    params['size'] = request.GET.get('size', None)
    params['asc'] = request.GET.get('asc', '1')
    params['order'] = request.GET.get('order', 'id')
    if not params['page'] or not params['size']:
        raise KeyError("missing pagination parameters")
    params['page'] = int(params['page'])
    params['size'] = int(params['size'])
    if not params['size'] > 0:
        raise ValueError("invalid page size")
    return params


def generic_paginated_query(dbModel, pager_params, **kwargs) -> HttpResponse:
    """
    generic paginated query on one table
    pass in a model class and a request object    
    kwargs: filter conditions
    """
    try:
        resp = AppResponse()

        obj_set = dbModel.objects.filter(**kwargs)
        obj_set = obj_set.order_by(
            pager_params['order'] if pager_params['asc'] else '-'+pager_params['order'])
        pager = Paginator(obj_set, pager_params['size'])
        page = pager_params['page']

        if page > pager.num_pages or page < 1:
            resp.reject("Page not found!")
        else:
            resp.resolve({
                "page": page,
                "totalPage": pager.num_pages,
                "data":pager.page(page).object_list,
            })
        
    except EmptyPage:
        resp.reject("Page empty!")
    except KeyError:
        resp.reject("Missing pagination parameters!")

    return resp


def __log_event(request: HttpRequest, status_code: int):
    try:
        user = request.user or None
        ip = request.META.get('REMOTE_ADDR')[:BMGTTransaction.IP_MAX_LENGTH]
        device = request.META.get('HTTP_USER_AGENT')[:BMGTTransaction.DEVICE_MAX_LENGTH]
        path = request.path
        met = request.method
        new_record = BMGTTransaction(user = user, ip = ip, device= device, method=met, path=path, status_code=status_code)
        new_record.save()
    except Exception as e:
        raise e
    

def logger(func):
    def wrapper(request: HttpRequest, **kwargs):
        try:
            response = func(request, **kwargs)
            status_code = response.status_code
            __log_event(request, status_code)
            return response
        except Exception as e:
            raise e
    return wrapper


class AppResponse(HttpResponse):
    def __init__(self, status: int = HTTPStatus.OK, reject = None, resolve= None) -> None:
        super().__init__(status=status)
        if reject and resolve:
            raise ValueError("reject and resolve cannot be both non-null")
        
        if reject:
            self.reject(reject)
        elif resolve:
            self.resolve(resolve)

    def reject(self, errorMsg: str):
        self.flush()
        self.write(json.dumps({
            'errorMsg': errorMsg,
        }, cls=CustomJSONEncoder
        ))

    def resolve(self, data):
        self.flush()
        self.write(json.dumps({
            'data': data
        }, cls=CustomJSONEncoder
        ))