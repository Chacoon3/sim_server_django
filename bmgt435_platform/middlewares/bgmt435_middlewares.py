from ..statusCode import Status
from django.http.request import HttpRequest
from django.http.response import HttpResponse


def CORSMiddleware(get_response):
    """
    this enables the CORS policy so that frontend can access the backend
    """
    
    def middleware(request):

        response = get_response(request)
        response["Access-Control-Allow-Origin"] = "http://localhost:5173"
        response["Access-Control-Allow-Credentials"] = "true"
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Expose-Headers'] = 'cookie, set-cookie'
        response['UseHttpOnly'] = '1'
        
        return response
    
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
            request_valid = bool(request.COOKIES.get('id', None) and request.COOKIES.get('role_name', None) == 'admin')
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