from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.db import IntegrityError
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.conf import settings
from .statusCode import Status
from .jsonUtils import serialize_paginated_data, serialize_models
from ..simulation.Cases import SimulationException

import regex as re
import json


__BATCH_QUERY_SIZE = 40


def get_batch_size(listObj):
    return min(len(listObj), __BATCH_QUERY_SIZE)


def request_error_handler(func):
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
            resp.write(f'Key missing: {e.args[0]}')

        except IntegrityError as e:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write(e.args[0])

        except ValidationError as e:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write(e.args[0])

        except NotImplementedError as e:
            resp = HttpResponse()
            resp.status_code = Status.NOT_IMPLEMENTED
            resp.write(e.args[0])

        except SimulationException as e:
            resp = HttpResponse()
            resp.status_code = Status.BAD_REQUEST
            resp.write(e.args[0])

        except ValueError as e:
            resp = HttpResponse()
            resp.write(e.args[0])
            resp.status_code = Status.BAD_REQUEST

        except Exception as e:
            # resp = HttpResponse()
            # resp.write(e.args[0])
            # resp.status_code = Status.INTERNAL_SERVER_ERROR

            if settings.DEBUG:
                raise
            else:
                resp = HttpResponse()
                resp.status_code = Status.INTERNAL_SERVER_ERROR
                resp.write("Internal server error!")
        
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


def generic_paginated_query(cls, pager_params, **kwargs) -> HttpResponse:
    """
    generic paginated query on one table
    pass in a model class and a request object    
    kwargs: filter conditions
    """
    resp = HttpResponse()

    obj_set = cls.objects.filter(**kwargs)
    obj_set = obj_set.order_by(
        pager_params['order'] if pager_params['asc'] else '-'+pager_params['order'])
    pager = Paginator(obj_set, pager_params['size'])

    if pager_params['page'] > pager.num_pages:
        resp.write("Page not found!")
        resp.status_code = Status.NOT_FOUND
    else:
        resp.write(serialize_paginated_data(pager, pager_params['page']))
        resp.status_code = Status.OK
    return resp