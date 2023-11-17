from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.hashers import make_password, check_password
from django.db import IntegrityError, transaction
from django.db.models import Max

from .apps import bmgt435_file_system
from .simulation.Core import SimulationException, SimulationResult
from .simulation.FoodDelivery import FoodDelivery
from .bmgtModels import *
from .utils.apiUtils import request_error_handler, password_valid, generic_paginated_query, pager_params_from_request, create_pager_params, AppResponse

import pandas as pd
import json
import io


"""
All requests have been verified to have valid user id except for those of the Auth.
"""


CASE_RECORD_PATH = bmgt435_file_system.base_location.__str__() + "case_records/"
MAX_GROUP_SIZE = 4

def _get_session_user(request: HttpRequest) -> BMGTUser:
    """
    raise key error if cookie not found
    raise does not exist error if user not found
    """
    id = request.COOKIES.get('id', None)
    user = BMGTUser.objects.get(id=id, activated=True,)
    return user


class AuthApi:

    @staticmethod
    def __set_auth_cookie(response: HttpResponse, user: BMGTUser) -> None:
        response.set_cookie('id', str(user.id), samesite='strict', secure=True, httponly=True)

    @staticmethod
    def __clear_auth_cookie(response: HttpResponse) -> None:
        response.delete_cookie('id', samesite='strict')

    @request_error_handler
    @require_POST
    @staticmethod
    def sign_in(request: HttpRequest) -> AppResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            did = data['did']
            password = data['password']
            user = BMGTUser.objects.get(did=did, activated=True,)
            if check_password(password, user.password):
                AuthApi.__set_auth_cookie(resp, user)
                resp.resolve(user)
            else:
                resp.reject("Sign in failed. Please check your directory ID and password!")
        except BMGTUser.DoesNotExist:
            resp.reject("Sign in failed. Please check your directory ID!")
        except KeyError:
            resp.reject("Sign in failed. Invalid data format!")
        
        return resp

    @staticmethod
    def set_session_cookie(response: HttpResponse, user: BMGTUser) -> None:
        pass

    @request_error_handler
    @require_POST
    @staticmethod
    def sign_up(request: HttpRequest) -> AppResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            did = data['did']
            password = data['password']
            user = BMGTUser.objects.get(did=did,)
            if user.activated:
                resp.reject("Sign up failed. User already activated!")
            else:
                if password_valid(password):
                    user.password = make_password(password)
                    user.activated = True
                    user.save()
                    resp.resolve("Sign up success!")
                else:
                    resp.reject("Sign up failed! Password should contain at least 8 and up to 20 alphanumeric characters!")
        except BMGTUser.DoesNotExist:
            resp.reject("Sign up failed. Please check your directory ID!")
        except KeyError:
            resp.reject("Sign up failed. Invalid data format!")

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
        try:
            resp = AppResponse()
            user = _get_session_user(request)
            resp.resolve("Sign out success!")
            AuthApi.__clear_auth_cookie(resp)
        except (BMGTUser.DoesNotExist, KeyError) as e:
            resp.reject("User not found!")

        return resp


class UserApi:

    @request_error_handler
    @require_GET
    @staticmethod
    def me(request: HttpRequest,) -> HttpResponse:
        try:
            resp = AppResponse()
            user = _get_session_user(request)
            resp.resolve(user)
        except BMGTUser.DoesNotExist:
            resp.reject("User not found!")
        except KeyError:
            resp.reject("Invalid data format!")

        return resp


class GroupApi:

    @request_error_handler
    @require_GET
    @staticmethod
    def get_group(request: HttpRequest) -> AppResponse:
        try:
            resp = AppResponse()
            group_id = int(request.GET.get('id'))
            group = BMGTGroup.objects.get(id=group_id)
            resp.resolve(group)
        except BMGTGroup.DoesNotExist:
            resp.reject("Group not found!")
        except KeyError:
            resp.reject("Invalid data format!")

        return resp

    @request_error_handler
    @require_GET
    @staticmethod
    def groups_paginated(request: HttpRequest,) -> HttpResponse:
        user: BMGTUser = _get_session_user(request)
        params = pager_params_from_request(request)
        if user.role == BMGTUser.BMGTUserRole.USER: # normal user only see groups in the same semester
            params['semester'] = user.semester
        return generic_paginated_query(BMGTGroup, params)
    

    @request_error_handler
    @require_POST
    @staticmethod
    def join_group(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()

            user: BMGTUser = _get_session_user(request)
            data = json.loads(request.body)
            group_id = data['group_id']
            if user.group == None:
                if user.role == BMGTUser.BMGTUserRole.ADMIN:    # admin can join any group of any semester
                    group = BMGTGroup.objects.get(id=group_id)
                else:
                    group = BMGTGroup.objects.get(id=group_id, semester=user.semester)
                if group.users.count() < MAX_GROUP_SIZE:
                    user.group = group
                    user.save()
                    resp.resolve(group)
                else:
                    resp.reject("Group already full!")
            else:
                resp.reject("Cannot join another group while you are alreay in a group!")
        except BMGTGroup.DoesNotExist:
            resp.reject("Group not found!")
        except KeyError:
            resp.reject("Invalid data format!")

        return resp

    @request_error_handler
    @require_POST
    @staticmethod
    def leave_group(request: HttpRequest) -> HttpResponse:
        resp = AppResponse()
        user: BMGTUser = _get_session_user(request)
        if user.group != None:
            user.group = None
            user.save()
            resp.resolve("Group left!")
        else:
            resp.resolve("You are not in a group!")

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
            resp = AppResponse()
            case_id = request.GET.get('case_id', None)
            case = BMGTCase.objects.get( id=case_id, visible=True)
            resp.resolve(case)
        except BMGTCase.DoesNotExist:
            resp.reject("Case not found!")
        except KeyError:
            resp.reject("Invalid data format!")
            
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
            resp = AppResponse()
            user: BMGTUser = _get_session_user(request)
            data = json.loads(request.body)
            case_id = int(data.get('case_id'))
            case_instance = BMGTCase.objects.get(id=case_id)
            if user.group != None:
                group = user.group
                if CaseApi.__case_submittable(case_instance, group):
                    with transaction.atomic():
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
                            case_instance = FoodDelivery(**params)
                            res = case_instance.run()
                            case_detail_bytes = res.detail_as_bytes()
                            case_summary = res.summary_as_dict()
                            case_record.summary_dict = case_summary
                            bmgt435_file_system.save(CASE_RECORD_PATH + case_record.file_name, case_detail_bytes)
                            case_record.state = BMGTCaseRecord.State.SUCCESS
                            case_record.score = res.score
                            case_record.save()
                            resp.resolve({
                                        "case_record_id": case_record.id,
                                        "summary": case_record.summary_dict,
                                        "file_url": case_record.file_url,
                                    })
                        case _:
                            resp.reject("Case not found!")
                else:
                    resp.reject("You have reached the maximum submission for this case!")
            else:
                resp.reject("You must join a group first to run the simulation!")

        except BMGTCase.DoesNotExist:
            resp.reject("Case not found!")
        except KeyError:
            resp.reject("Invalid data format!")
        except SimulationException as e:
            resp.reject(f"{e.args[0]}")
            
        return resp


class CaseRecordApi:
    @request_error_handler
    @staticmethod
    def get_case_record(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            case_record_id = request.GET.get('id', None)
            case_record = BMGTCaseRecord.objects.get(id=case_record_id, )
            resp.resolve(case_record)
        except BMGTCaseRecord.DoesNotExist:
            resp.reject("Case record not found!")
        except KeyError:
            resp.reject("Invalid data format!")

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
            response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',)
            return response
        

    @request_error_handler
    @require_GET
    @staticmethod
    def case_records_paginated(request: HttpRequest) -> HttpResponse:
        user: BMGTUser = _get_session_user(request)
        group = user.group
        pagerParams = pager_params_from_request(request)
        return generic_paginated_query(BMGTCaseRecord, pagerParams, state=BMGTCaseRecord.State.SUCCESS, group_id=group)


    @request_error_handler
    @require_GET
    def leader_board_paginated(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
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
                    raise BMGTCase.DoesNotExist
        except KeyError:
            resp.reject("Invalid data format!")
        except BMGTCase.DoesNotExist:
            resp.reject("Case not found!")

        return resp


class ManageApi:

    @request_error_handler
    @require_POST
    @staticmethod
    def import_users(request: HttpRequest, semester_id) -> HttpResponse:
        try:
            resp = AppResponse()
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

                    BMGTUser.objects.bulk_create(obj_set)
                    resp.resolve(len(obj_set))
                else:
                    resp.reject("Import failed! Please upload a CSV file that contains the following columns: user_first_name, user_last_name, directory_id")
        except IntegrityError:
            resp.reject("Import failed! Please remove the duplicated directory ID's from the CSV file!")
        except BMGTSemester.DoesNotExist:
            resp.reject("Semester not found!")
        
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
        resp = AppResponse()

        count_users = BMGTUser.objects.count()
        count_active_users = BMGTUser.objects.filter(activated=True).count()
        count_groups = BMGTGroup.objects.count()
        count_cases = BMGTCase.objects.count()
        count_case_records = BMGTCaseRecord.objects.count()
        count_case_records_success = BMGTCaseRecord.objects.filter(state=BMGTCaseRecord.State.SUCCESS).count()

        resp.resolve({
            "count_users": count_users,
            "count_active_users": count_active_users,
            "count_groups": count_groups,
            "count_cases": count_cases,
            "count_case_records": count_case_records,
            "count_case_records_success": count_case_records_success,
        })

        return resp
    

    @request_error_handler
    @require_POST
    @staticmethod
    def create_semester(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            year = data.get('year', None)
            season = data.get('season', None)
            if BMGTSemester.objects.filter(year=year, season=season).exists():
                resp.reject("Failed to create semester. Semester already exists!")
            else:
                with transaction.atomic():
                    semester = BMGTSemester(year=year, season=season)
                    semester.save()
                resp.resolve("Semester created successfully!")
        except IntegrityError:
            resp.reject("Failed to create semester. Invalid semester arguments!")

        return resp
    
    
    @request_error_handler
    @require_POST
    @staticmethod
    def delete_semester(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            semester_id = data.get('semester_id', None)
            semester = BMGTSemester.objects.get(id=semester_id)
            semester.delete()
            resp.resolve("Semester deleted!")
        except BMGTSemester.DoesNotExist:
            resp.reject("Semester not found!")
        except KeyError:
            resp.reject("Invalid data format!")
        return resp
    
    @request_error_handler
    @require_GET
    @staticmethod
    def get_semesters(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            semesters = BMGTSemester.objects.all()
            resp.resolve(semesters)
        except Exception as e:
            resp.reject(e)

        return resp
    

    @request_error_handler
    @require_POST
    @staticmethod
    def batch_create_group(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            semester_id = data.get('semester_id', None)
            size = int(data.get('size'))
            semester = BMGTSemester.objects.get(id=semester_id)
            max_group_num = BMGTGroup.objects.aggregate(max_value=Max('number'))['max_value'] or 0
            BMGTGroup.objects.bulk_create(
                [BMGTGroup(number=max_group_num + i + 1, semester=semester) for i in range(size)]
            )
            resp.resolve("Groups created!")
        except BMGTSemester.DoesNotExist:
            resp.reject("Semester not found!")
        except KeyError:
            resp.reject("Invalid data format!")
        except Exception as e:
            resp.reject(e)
        
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
            resp = AppResponse()
            data = json.loads(request.body)
            user: BMGTUser = _get_session_user(request)
            content = data.get('content')
            if content:
                feedback = BMGTFeedback(user=user, content=content)
                feedback.save()
                resp.resolve("Feedback submitted!")
            else:
                resp.reject("Feedback cannot be empty!")  
        except KeyError:
            resp.reject("Invalid data format!")
        except Exception as e:
            resp.reject(e)
        
        return resp
    
    @request_error_handler
    @require_GET
    @staticmethod
    def feedback_paginated(request: HttpRequest) -> HttpResponse:
        return generic_paginated_query(BMGTFeedback, pager_params_from_request(request))