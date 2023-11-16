from .utils.statusCode import Status
from django.http import HttpRequest, HttpResponse
import os
from .bmgtModels import BMGTUser
from .utils.apiUtils import AppResponse


def CORSMiddleware(get_response):

    origin = os.environ.get("APP_FRONTEND_HOST",)

    def config_cors_response(resp: HttpResponse):
        resp["Access-Control-Allow-Origin"] = origin
        resp["Access-Control-Allow-Credentials"] = "true"
        resp['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept, x-xsrf-token'
        resp['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        resp['Access-Control-Expose-Headers'] = 'cookie, set-cookie, x-xsrf-token'
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

    def middleware(request: HttpRequest):
        """
        assert the validity of cookies
        apart from registration and password retrieval operations, all other operations require cookies
        requests without valid cookies will be rejected

        authentication rules:
        1. authentication api's are always allowed
        2. user utility api's are allowed if there is a user id cookie
        3. manage api's are allowed if there is a user id cookie, and if the user is an admin (validated by a database query)
        """
        ADMIN_ROLE = "admin"
        FailedPrompt = "Failed to verify authentication!"

        # no authentication required
        if request.path.startswith("/bmgt435-service/api/auth/") or request.path.startswith("/bmgt435-service/admin") or request.path.startswith("/bmgt435-service/static"):
            return get_response(request)

        user_id = request.COOKIES.get('id', None)
        if user_id is None:
            resp = AppResponse(reject=FailedPrompt)
            return resp
        else:
            user_query = BMGTUser.objects.filter(id=user_id, activated=True)
            if user_query.exists():
                user = user_query.get()
                request.bmgt_user = user    # store the user info
                # admin authentication required
                if request.path.startswith("/bmgt435-service/api/manage/"):
                    if user.role == ADMIN_ROLE:
                        return get_response(request)
                    else:
                        resp = AppResponse(reject=FailedPrompt)
                        return resp
                else:      # user authentication required             
                     return get_response(request)
            else:
                resp = AppResponse(reject=FailedPrompt)
                return resp

    return middleware