from ..utils.statusCode import Status
from django.http import HttpRequest, HttpResponse
import time 
import random
import os


def CORSMiddleware(get_response):
    
    origin = os.environ.get("BMGT435_INDEX")
    def config_cors_response(resp: HttpResponse):
            resp["Access-Control-Allow-Origin"] = origin
            resp["Access-Control-Allow-Credentials"] = "true"
            resp['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
            resp['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            resp['Access-Control-Expose-Headers'] = 'cookie, set-cookie'
            resp['UseHttpOnly'] = '1'
    
    def middleware(request: HttpRequest):

        if request.method == 'OPTIONS':
            resp = HttpResponse()
            config_cors_response(resp)
            resp.status_code = Status.OK
            return resp
        else:
            resp = get_response(request)
            config_cors_response(resp)
            return resp
    
    return middleware


def AuthenticationMiddleware(get_response):

    ADMIN_ROLE = "admin"

    def middleware(request: HttpRequest):
        """
        assert the validity of cookies
        apart from registration and password retrieval operations, all other operations require cookies
        requests without valid cookies will be rejected
        """
        
        if request.path.startswith("/bmgt435/api/auth/") or request.path.startswith("/admin") or request.path.startswith("/static/"):
            return get_response(request)
        elif request.path.startswith("/bmgt435/api/manage/"):
            request_valid = bool(request.COOKIES.get('id', None) and request.COOKIES.get('role', None) == ADMIN_ROLE)
            if request_valid:
                return get_response(request)
            else:
                resp = HttpResponse(status=Status.UNAUTHORIZED)
                resp.write("Failed to verify authentication!")
                return resp
        else:
            request_valid = bool(request.COOKIES.get('id', None))
            if request_valid:
                return get_response(request)
            else:
                resp = HttpResponse(status=Status.UNAUTHORIZED)
                resp.write("Failed to verify authentication!")
                return resp

    return middleware


def TestModeMiddleware(get_response):
    # add random lag to simulate network latency
    def middleware(request: HttpRequest):
        if not request.path.startswith("/bmgt435/api/manage/") and not request.path.startswith("/admin/"):
            lag = random.randint(0, 20)
            lag = round(lag / 10, 1)
            time.sleep(lag) 
        return get_response(request)

    return middleware