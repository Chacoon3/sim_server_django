from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.db import IntegrityError
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse

from .customExceptions import DataFormatError
from .statusCode import Status
from .jsonUtils import serialize_paginated_data, serialize_models

import regex as re
import json


__BATCH_QUERY_SIZE = 40


def get_batch_size(listObj):
    return min(len(listObj), __BATCH_QUERY_SIZE)


def api_error_handler(func):
    """
    API level exception handling
    """

    def wrapped(request, **kwargs) -> HttpResponse:
        try:
            return func(request, **kwargs)

        except json.JSONDecodeError as e:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write(e.args[0])

        except ObjectDoesNotExist as e:
            resp = HttpResponse()
            resp.status_code = Status.NOT_FOUND
            resp.write(e.args[0])

        except MultipleObjectsReturned as e:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write(e.args[0])

        except KeyError as e:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write(e.args[0])

        except IntegrityError as e:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write(e.args[0])

        except ValidationError as e:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write(e.args[0])

        except DataFormatError as e:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write(e.args[0])

        except NotImplementedError as e:
            resp = HttpResponse()
            resp.status_code = Status.NOT_IMPLEMENTED
            resp.write(e.args[0])

        except Exception as e:
            raise


        return resp

    return wrapped


def password_valid(password: str) -> bool:
    """
    password strength validation
    """

    leng_valid = len(password) >= 8
    has_char = bool(re.search(pattern=r'\w', string=password))
    has_num = bool(re.search(pattern=r'\d', string=password))
    return leng_valid and has_char and has_num


def get_paginator_params(request:HttpRequest) -> dict:
    params = {}
    params['page'] = request.GET.get('page', None)
    params['size'] = request.GET.get('size', None)
    params['asc'] = request.GET.get('asc', '1')
    params['order'] = request.GET.get('order', 'id')
    if not params['page'] or not params['size']:
        raise DataFormatError("missing pagination parameters")
    params['page'] = int(params['page'])
    params['size'] = int(params['size'])
    if not params['size'] > 0:
        raise DataFormatError("invalid page size")
    return params



def generic_unary_query(cls, request: HttpRequest,) -> HttpResponse:
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
                        obj_set, fields=['flag_deleted'], batch_size=get_batch_size(obj_set))
                resp.status_code = Status.DELETED
                resp.write(f"Delete Success on {count_update} Rows!")
            else:
                count_delete = obj_set.delete()
                resp.status_code = Status.DELETED
                resp.write(f"Delete Success on {count_delete} Rows!")
        else:
            resp.status_code = Status.NOT_FOUND
            resp.write("The requested resource does not exist!")
    elif request.method == "PUT":
        obj_set = json.loads(request.body)
        if type(obj_set) is not list:
            obj_set = [obj_set]
        target_set = [cls.objects.get(id=obj.get('id')) for obj in obj_set]
        all_exists = (len(target_set) == len(obj_set))
        if all_exists:
            [target.set_fields(**obj) for target, obj in zip(target_set, obj_set)]
            count_update = cls.objects.bulk_update(
                target_set, fields=cls.query_editable_fields, batch_size=get_batch_size(target_set))
            resp.status_code = Status.UPDATED
            resp.write(f"Update Success on {count_update} Rows!")
        else:
            resp.status_code = Status.NOT_FOUND
            resp.write("The requested resource does not exist!")
    elif request.method == "POST":
        obj_set = json.loads(request.body)
        if type(obj_set) is not list:
            obj_set = [obj_set]
        data_valid = all([not (obj.get('id')) for obj in obj_set])
        if obj_set:
            if data_valid:
                obj_set = [cls(**obj) for obj in obj_set]
                obj_created = cls.objects.bulk_create(
                    obj_set, batch_size=get_batch_size(obj_set))
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



def generic_paginated_fetch(cls, request: HttpRequest, **kwargs) -> HttpResponse:
    """
    generic paginated fetch on one table
    pass in a model class and a request object    
    kwargs: filter conditions
    """
    resp = HttpResponse()
    pager_params = get_paginator_params(request)


    obj_set = cls.objects if not kwargs else cls.objects.filter(**kwargs)
    obj_set = obj_set.order_by(pager_params['order'] if pager_params['asc'] else '-'+pager_params['order'])
    pager = Paginator(obj_set, pager_params['size'])

    if pager_params['page'] > pager.num_pages:
        resp.write("Page not found!")
        resp.status_code = Status.NOT_FOUND
    else:
        resp.write(serialize_paginated_data(pager, pager_params['page']))
        resp.status_code = Status.OK
    return resp