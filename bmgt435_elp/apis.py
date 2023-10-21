from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST, require_GET,  require_http_methods
from django.contrib.auth.hashers import make_password, check_password
from django.db import IntegrityError
from django.shortcuts import redirect


from .apps import bmgt435_file_system
from .simulation.Cases import FoodCenter, SimulationException
from .bmgtModels import *
from django.db.models import Max
import bmgt435_elp.bmgtAnalyticsModel as bmgtAnalyticsModel
from .utils.statusCode import Status
from .utils.jsonUtils import serialize_models, serialize_model_instance, serialize_simulation_result
from .utils.apiUtils import request_error_handler, password_valid, generic_paginated_query, pager_params_from_request, create_pager_params

import pandas as pd
import json
import io


"""
All requests have been verified to have valid user id except for those of the Auth.
"""


CASE_RECORD_PATH = bmgt435_file_system.base_location.__str__() + "case_records/"
MAX_GROUP_SIZE = 4


class AuthApi:

    @staticmethod
    def __set_auth_cookie(response: HttpResponse, user: BMGTUser) -> None:
        response.set_cookie('id', str(user.id),
                            samesite='strict', secure=True, httponly=True)

    @staticmethod
    def __clear_auth_cookie(response: HttpResponse) -> None:
        response.delete_cookie('id', samesite='strict')

    @request_error_handler
    @require_POST
    @staticmethod
    def sign_in(request: HttpRequest) -> HttpResponse:
        try:
            resp = HttpResponse()
            data = json.loads(request.body)
            did = data['did']
            password = data['password']
            user = BMGTUser.objects.get(did=did, activated=True,)
            if check_password(password, user.password):
                resp.status_code = Status.OK
                AuthApi.__set_auth_cookie(resp, user)
                resp.write(serialize_model_instance(user))
            else:
                resp.status_code = Status.UNAUTHORIZED
                resp.write("Sign in failed. Please check your directory ID and password!")
        except BMGTUser.DoesNotExist:
            resp.status_code = Status.NOT_FOUND
            resp.write("Sign in failed. Please check your directory ID!")
        except KeyError:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Sign in failed. Invalid data format!")

        return resp

    @staticmethod
    def set_session_cookie(response: HttpResponse, user: BMGTUser) -> None:
        pass

    @request_error_handler
    @require_POST
    @staticmethod
    def sign_up(request: HttpRequest) -> HttpResponse:
        try:
            resp = HttpResponse()
            data = json.loads(request.body)
            did = data['did']
            password = data['password']
            user = BMGTUser.objects.get(did=did,)
            if user.activated:
                resp.status_code = Status.BAD_REQUEST
                resp.write("Sign up failed. User already exists!")
            else:
                if password_valid(password):
                    user.password = make_password(password)
                    user.activated = True
                    user.save()
                    resp.status_code = Status.OK
                    resp.write("Sign up success!")
                else:
                    resp.status_code = Status.BAD_REQUEST
                    resp.write("Sign up failed! Password should contain at least 8 and up to 20 alphanumeric characters!")
        except BMGTUser.DoesNotExist:
            resp.status_code = Status.NOT_FOUND
            resp.write("Sign up failed. Please check your directory ID!")
        except KeyError:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Sign up failed. Invalid data format!")

        return resp

    @request_error_handler
    @require_POST
    @staticmethod
    def password_reset(request: HttpRequest) -> HttpResponse:

        user_did = request.GET.get('did')
        raise NotImplementedError

    @request_error_handler
    @require_POST
    @staticmethod
    def sign_out(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        AuthApi.__clear_auth_cookie(resp)
        resp.status_code = Status.OK
        return resp


class UserApi:

    @request_error_handler
    @require_GET
    @staticmethod
    def me(request: HttpRequest,) -> HttpResponse:
        try:
            resp = HttpResponse()
            id = request.COOKIES.get('id', None)
            user = BMGTUser.objects.get(id=id, activated=1, )
            resp.write(serialize_model_instance(user))
            resp.status_code = Status.OK
        except BMGTUser.DoesNotExist:
            resp.status_code = Status.NOT_FOUND
            resp.write("User not found!")
        except KeyError:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Invalid data format!")

        return resp


class GroupApi:

    @request_error_handler
    @require_GET
    @staticmethod
    def get_group(request: HttpRequest) -> HttpResponse:
        try:
            resp = HttpResponse()
            group_id = int(request.GET.get('id'))
            group = BMGTGroup.objects.get(id=group_id)
            resp.write(serialize_model_instance(group))
            resp.status_code = Status.OK
        except BMGTGroup.DoesNotExist:
            resp.status_code = Status.NOT_FOUND
            resp.write("Group not found!")
        except KeyError:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Invalid data format!")

        return resp

    @request_error_handler
    @require_GET
    @staticmethod
    def groups_paginated(request: HttpRequest,) -> HttpResponse:
        user: BMGTUser = request.bmgt_user     # display only groups in the same semester
        params = pager_params_from_request(request)
        if user.role == BMGTUser.BMGTUserRole.USER: # normal user only see groups in the same semester
            params['semester'] = user.semester
        return generic_paginated_query(BMGTGroup, params)
    

    @request_error_handler
    @require_POST
    @staticmethod
    def join_group(request: HttpRequest) -> HttpResponse:
        try:
            resp = HttpResponse()
            user: BMGTUser = request.bmgt_user
            data = json.loads(request.body)
            group_id = data.get('group_id')
            if user.group == None:
                if user.role == BMGTUser.BMGTUserRole.ADMIN:    # admin can join any group of any semester
                    group = BMGTGroup.objects.get(id=group_id)
                else:
                    group = BMGTGroup.objects.get(id=group_id, semester=user.semester)
                if group.users.count() < MAX_GROUP_SIZE:
                    user.group = group
                    user.save()
                    resp.write(serialize_model_instance(group))
                    resp.status_code = Status.OK
                else:
                    resp.write("Group already full!")
                    resp.status_code = Status.NOT_FOUND
            else:
                resp.write("Cannot join another group while you are alreay in a group!")
                resp.status_code = Status.BAD_REQUEST
        except BMGTGroup.DoesNotExist:
            resp.status_code = Status.NOT_FOUND
            resp.write("Group not found!")
        except KeyError:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Invalid data format!")

        return resp

    @request_error_handler
    @require_POST
    @staticmethod
    def leave_group(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        user: BMGTUser = request.bmgt_user
        if user.group != None:
            user.group = None
            user.save()
            resp.write("Group left!")
            resp.status_code = Status.OK
        else:
            resp.write("You are not in a group!")
            resp.status_code = Status.BAD_REQUEST

        return resp


class CaseApi:
    @staticmethod
    def __case_submittable(case:BMGTCase, group:BMGTGroup) -> bool:
        count_submission = BMGTCaseRecord.objects.filter(
                case=case, group=group,
                state__in=[BMGTCaseRecord.State.RUNNING, BMGTCaseRecord.State.SUCCESS]
            ).count()
        return case.max_submission == -1 or count_submission < case.max_submission


    @request_error_handler
    @require_GET
    @staticmethod
    def get(request: HttpRequest) -> HttpResponse:
        try:
            resp = HttpResponse()
            case_id = request.GET.get('case_id', None)
            case = BMGTCase.objects.get( id=case_id, visible=True)
            resp.write(serialize_model_instance(case))
            resp.status_code = Status.OK
        except BMGTCase.DoesNotExist:
            resp.status_code = Status.NOT_FOUND
            resp.write("Case not found!")
        except KeyError:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Invalid data format!")
            
        return resp
    

    @request_error_handler
    @require_GET
    @staticmethod
    def cases_paginated(request: HttpRequest) -> HttpResponse:
        return generic_paginated_query(BMGTCase, pager_params_from_request(request))


    @request_error_handler
    @require_POST
    @staticmethod
    def submit(request: HttpRequest) -> HttpResponse:
        try:
            resp = HttpResponse()
            user: BMGTUser = request.bmgt_user
            data = json.loads(request.body)
            case_id = int(data.get('case_id'))
            case_instance = BMGTCase.objects.get(id=case_id)
            if user.group != None:
                group = user.group
                if CaseApi.__case_submittable(case_instance, group):
                    case_record = BMGTCaseRecord(
                        user=user,
                        case=case_instance, group=group, state=BMGTCaseRecord.State.RUNNING,
                        file_name = BMGTCaseRecord.generate_file_name(group, user, case_instance)
                    )
                    case_record.save()
                    
                    # run logic
                    match case_id:
                        case 1:     # food center
                            params = data.get('case_params')
                            case_instance = FoodCenter(**params)
                            res = case_instance.run()
                            case_detail_bytes = res.detail_as_bytes()
                            case_summary = res.summary_as_dict()
                            case_record.summary_dict = case_summary
                            bmgt435_file_system.save(CASE_RECORD_PATH + case_record.file_name, case_detail_bytes)
                            case_record.state = BMGTCaseRecord.State.SUCCESS
                            case_record.score = res.score
                            case_record.save()
                            resp.write(json.dumps({
                                        "case_record_id": case_record.id,
                                        "summary": case_record.summary_dict,
                                        "file_url": case_record.file_url,
                                    }))
                            resp.status_code = Status.OK
                        case _:
                            resp.write("Case not found!")
                            resp.status_code = Status.NOT_FOUND
                else:
                    resp.write(
                            "You have reached the maximum submission for this case!")
                    resp.status_code = Status.BAD_REQUEST
            else:
                resp.write(
                    "You must join a group first to run the simulation!")
                resp.status_code = Status.BAD_REQUEST

        except BMGTCase.DoesNotExist:
            resp.status_code = Status.NOT_FOUND
            resp.write("Case not found!")
        except KeyError:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Invalid data format!")
        except SimulationException as e:
            resp.status_code = Status.BAD_REQUEST
            resp.write(f"Simulation failed!{e.args[0]}")
            
        return resp


class CaseRecordApi:
    @request_error_handler
    @staticmethod
    def get_case_record(request: HttpRequest) -> HttpResponse:
        try:
            resp = HttpResponse()
            case_record_id = request.GET.get('id', None)
            case_record = BMGTCaseRecord.objects.get(id=case_record_id, )
            resp.write(serialize_model_instance(case_record))
            resp.status_code = Status.OK
        except BMGTCaseRecord.DoesNotExist:
            resp.status_code = Status.NOT_FOUND
            resp.write("Case record not found!")
        except KeyError:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Invalid data format!")

        return resp

    @request_error_handler
    @require_GET
    @staticmethod
    def get_case_record_file(request: HttpRequest) -> HttpResponse:
        # feature of this interface should be replaced by direct static file get request handled by the proxy server
        case_record_id = request.GET.get('id', None)
        case_record = BMGTCaseRecord.objects.get(id=case_record_id, )
        file_name = CASE_RECORD_PATH + case_record.file_name
        with open(file_name, 'rb') as file:
            response = HttpResponse(file.read(), content_type='octet/stream')
            return response
        

    @request_error_handler
    @require_GET
    @staticmethod
    def case_records_paginated(request: HttpRequest) -> HttpResponse:
        user:BMGTUser = request.bmgt_user
        group = user.group
        if not group:
            resp = HttpResponse()
            resp.status_code = Status.NOT_FOUND
            return resp
        else:
            return generic_paginated_query(BMGTCaseRecord, pager_params_from_request(request), state=BMGTCaseRecord.State.SUCCESS, group_id=group)

    @request_error_handler
    @require_GET
    def leader_board_paginated(request: HttpRequest) -> HttpResponse:
        try:
            resp = HttpResponse()
            case_id = int(request.GET.get('case_id'))
            match case_id:
                case 1:
                    page = int(request.GET.get('page', None))
                    size = int(request.GET.get('size', None))
                    query_params = create_pager_params(page, size, 0, 'score')
                    return generic_paginated_query(
                        BMGTCaseRecord, query_params,
                        state=BMGTCaseRecord.State.SUCCESS,
                        case_id=case_id)

                case _:
                    resp.write("Case not found!")
                    resp.status_code = Status.NOT_FOUND
        except KeyError:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Invalid data format!")

        return resp


class ManageApi:

    @request_error_handler
    @require_POST
    @staticmethod
    def import_users(request: HttpRequest, semester_id) -> HttpResponse:
        try:
            resp = HttpResponse()
            semester = BMGTSemester.objects.get(id=semester_id)
            with io.BytesIO(request.body) as file:
                raw_csv = pd.read_csv(file, encoding='utf-8')
                format_valid = all([col_name in raw_csv.columns for col_name in ['user_first_name', 'user_last_name', 'directory_id']])
                if format_valid:
                    user_csv = raw_csv[['user_first_name',
                                            'user_last_name', 'directory_id']]
                    user_csv.columns = ['first_name', 'last_name', 'did']
                    user_csv.applymap(lambda x: str(x).strip())
                    obj_set = [BMGTUser(semester = semester, **row)
                                for row in user_csv.to_dict('records')]

                    BMGTUser.objects.bulk_create(obj_set, batch_size=40)
                    resp.status_code = Status.OK
                    resp.write("Imported!")
                else:
                    resp.status_code = Status.BAD_REQUEST
                    resp.write("Import failed! Please upload a CSV file that contains the following columns: user_first_name, user_last_name, directory_id")
        except IntegrityError:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Import failed! Please remove the duplicated directory ID's from the CSV file!")
        
        return resp


    @request_error_handler
    @require_POST
    @staticmethod
    def config_case(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()

        data = json.loads(request.body)

        case_id = data.get('case_id', None)

        return resp

    @request_error_handler
    @require_GET
    @staticmethod
    def view_users(request: HttpRequest) -> HttpResponse:
        return generic_paginated_query(BMGTUser, pager_params_from_request(request))

    @request_error_handler
    @require_GET
    @staticmethod
    def system_status(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()

        count_users = BMGTUser.objects.count()
        count_active_users = BMGTUser.objects.filter(activated=1).count()
        count_groups = BMGTGroup.objects.count()
        count_cases = BMGTCase.objects.count()
        count_case_records = BMGTCaseRecord.objects.count()
        count_case_records_success = BMGTCaseRecord.objects.filter(state=BMGTCaseRecord.State.SUCCESS).count()

        resp.write(json.dumps({
            "count_users": count_users,
            "count_active_users": count_active_users,
            "count_groups": count_groups,
            "count_cases": count_cases,
            "count_case_records": count_case_records,
            "count_case_records_success": count_case_records_success,
        }))

        resp.status_code = Status.OK
        return resp
    

    @request_error_handler
    @require_POST
    @staticmethod
    def create_semester(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        data = json.loads(request.body)
        year = data.get('year', None)
        season = data.get('season', None)
        if BMGTSemester.objects.filter(year=year, season=season).exists():
            resp.write("Semester already exists!")
            resp.status_code = Status.BAD_REQUEST
        else:
            semester = BMGTSemester.objects.create(year=year, season=season)
            semester.save()
            resp.write(serialize_model_instance(semester))
            resp.status_code = Status.OK
        return resp
    
    
    @request_error_handler
    @require_POST
    @staticmethod
    def delete_semester(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        data = json.loads(request.body)
        semester_id = data.get('semester_id', None)
        semester = BMGTSemester.objects.get(id=semester_id)
        semester.delete()
        resp.status_code = Status.OK
        return resp
    
    @request_error_handler
    @require_GET
    @staticmethod
    def get_semesters(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        semesters = BMGTSemester.objects.all()
        resp.write(serialize_models(semesters))
        resp.status_code = Status.OK
        return resp
    

    @request_error_handler
    @require_POST
    @staticmethod
    def batch_create_group(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        data = json.loads(request.body)
        semester_id = data.get('semester_id', None)
        size = int(data.get('size'))
        semester = BMGTSemester.objects.get(id=semester_id)
        max_group_num = BMGTGroup.objects.aggregate(max_value=Max('number'))['max_value'] or 0
        BMGTGroup.objects.bulk_create(
            [BMGTGroup(number=max_group_num + i + 1, semeter=semester) for i in range(size)]
        )
        resp.status_code = Status.OK
        return resp
    

    @request_error_handler
    @require_GET
    @staticmethod
    def group_view_paginated(request: HttpRequest) -> HttpResponse:
        return generic_paginated_query(BMGTGroup, pager_params_from_request(request))


class FeedbackApi:

    @request_error_handler
    @require_POST
    @staticmethod
    def post(request: HttpRequest) -> HttpResponse:
        try:
            resp = HttpResponse()
            data = json.loads(request.body)
            user:BMGTUser = request.bmgt_user
            content = data.get('content')
            if content:
                feedback = bmgtAnalyticsModel.BMGTFeedback(user=user, content=content)
                feedback.save()
                resp.status_code = Status.OK
                resp.write("Feedback submitted!")
            else:
                resp.status_code = Status.BAD_REQUEST
                resp.write("Feedback cannot be empty!")  
        except KeyError:
            resp.status_code = Status.BAD_REQUEST
            resp.write("Invalid data format!")
        
        return resp
    
    @request_error_handler
    @require_GET
    @staticmethod
    def feedback_paginated(request: HttpRequest) -> HttpResponse:
        return generic_paginated_query(bmgtAnalyticsModel.BMGTFeedback, pager_params_from_request(request))