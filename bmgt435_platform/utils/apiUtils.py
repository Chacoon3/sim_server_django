from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.db import IntegrityError
from .customExceptions import DataFormatError
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from .statusCode import Status

import json


__DEF_PAGE_SIZE = 10
__BATCH_QUERY_SIZE = 40


def get_batch_size(list):
    return min(len(list), __BATCH_QUERY_SIZE)


def api_error_handler(func):
    """
    API level exception handling decorator
    """

    def wrapped(request, **kwargs) -> HttpResponse:
        try:
            return func(request, **kwargs)

        except json.JSONDecodeError as e:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write(e.message or e)

        except ObjectDoesNotExist as e:
            resp = HttpResponse()
            resp.status_code = Status.NOT_FOUND
            resp.write(e)

        except MultipleObjectsReturned as e:
            resp = HttpResponse()
            resp.status_code = Status.DATABASE_ERROR
            resp.write(e)

        except KeyError as e:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write(e)

        except IntegrityError as e:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write(e.args)

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


def password_valid(password: str) -> bool:
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
        "data": json.loads(serialize_models(paginator.page(page).object_list)),
    })


def _is_admin(request:HttpRequest) -> bool:
    return request.COOKIES.get('role_id', None) == '1'


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
                resp.status_code = Status.OK
                resp.write(f"Delete Success on {count_update} Rows!")
            else:
                count_delete = obj_set.delete()
                resp.status_code = Status.OK
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
                target_set, fields=cls.batch_updatable_fields, batch_size=get_batch_size(target_set))
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



def generic_paginated_fetch(cls, request: HttpRequest,) -> HttpResponse:
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
        resp.write(to_paginator_response(pager, page))
    return resp