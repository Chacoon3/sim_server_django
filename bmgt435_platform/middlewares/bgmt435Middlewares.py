from ..utils.statusCode import Status
from django.http import HttpRequest, HttpResponse
import time 
import random


def CORSMiddleware(get_response):
    """
    this enables the CORS policy so that frontend can access the backend
    """
    
    def middleware(request: HttpRequest):

        if request.method == 'OPTIONS':
            resp = HttpResponse()
            resp["Access-Control-Allow-Origin"] = "http://localhost:5173"
            resp["Access-Control-Allow-Credentials"] = "true"
            resp['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
            resp['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            resp['Access-Control-Expose-Headers'] = 'cookie, set-cookie'
            resp['UseHttpOnly'] = '1'
            resp.status_code = Status.OK
            return resp
        else:
            resp = get_response(request)
            resp["Access-Control-Allow-Origin"] = "http://localhost:5173"
            resp["Access-Control-Allow-Credentials"] = "true"
            resp['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
            resp['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            resp['Access-Control-Expose-Headers'] = 'cookie, set-cookie'
            resp['UseHttpOnly'] = '1'
            
            return resp
    
    return middleware



def AuthenticationMiddleware(get_response):

    def middleware(request: HttpRequest):
        """
        assert the validity of cookies
        apart from registration and password retrieval operations, all other operations require cookies
        requests without valid cookies will be rejected
        """
        
        if request.path.startswith("/bmgt435/api/auth/") or request.path.startswith("/admin/"):
            return get_response(request)
        elif request.path.startswith("/bmgt435/api/manage/"):
            request_valid = bool(request.COOKIES.get('id', None) and request.COOKIES.get('role_id', None) == '1')
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
        lag = random.randint(0, 20)
        lag = round(lag / 10, 1)
        time.sleep(lag) 
        return get_response(request)

    return middleware