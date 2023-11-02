from ..utils.statusCode import Status
from django.http import HttpRequest, HttpResponse
import os
from ..bmgtModels import BMGTUser


def CORSMiddleware(get_response):

    origin = os.environ.get("BMGT435_INDEX")

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

    ADMIN_ROLE = "admin"

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
        # no authentication required
        if request.path.startswith("/bmgt435-service/api/auth/") or request.path.startswith("/bmgt435-service/admin") or request.path.startswith("/bmgt435-service/static"):
            return get_response(request)

        user_id = request.COOKIES.get('id', None)
        if not user_id:
            resp = HttpResponse(status=Status.NOT_FOUND)
            resp.write("Failed to verify authentication!")
            return resp
        else:
            user_query = BMGTUser.objects.filter(id=user_id, activated=1)
            if user_query.exists():
                user = user_query.get()
                request.bmgt_user = user    # store the user info
                # admin authentication required
                if request.path.startswith("/bmgt435-service/api/manage/"):
                    if user.role == ADMIN_ROLE:
                        return get_response(request)
                    else:
                        resp = HttpResponse(status=Status.NOT_FOUND)
                        resp.write("Failed to verify authentication!")
                        return resp
                else:      # user authentication required             
                     return get_response(request)
            else:
                resp = HttpResponse(status=Status.NOT_FOUND)
                resp.write("Failed to verify authentication!")
                return resp

    return middleware


# def TestModeMiddleware(get_response):
#     # add random lag to simulate network latency
#     def middleware(request: HttpRequest):
#         if not request.path.startswith("/bmgt435/api/manage/") and not request.path.startswith("/admin/"):
#             lag = random.randint(0, 20)
#             lag = round(lag / 10, 1)
#             time.sleep(lag)
#         return get_response(request)

#     return middleware
