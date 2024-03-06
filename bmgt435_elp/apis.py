from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.contrib.auth.hashers import make_password, check_password
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.conf import settings

from .simulation import FoodDelivery, SimulationException
from .bmgtModels import *
from .utils.apiUtils import request_error_handler, password_valid, generic_paginated_query, pager_params_from_request, create_pager_params, AppResponse

import pandas as pd
import json
import io
import os

"""
All requests have been verified to have valid user id except for those of the Auth.
"""

_CASE_RECORD_PATH = settings.MEDIA_ROOT  + "bmgt435/case-records/"
_MAX_GROUP_SIZE = 4
_FOOD_DELIVERY_CASE_ID = 1
_CALL_CENTER_CASE_ID = 2


def _get_session_user(request: HttpRequest) -> BMGTUser:
    """
    raise key error if cookie not found
    raise does not exist error if user not found
    """

    try:
        user: BMGTUser = request.app_user
    except: # fallback
        id = request.COOKIES.get('id', None)
        user = BMGTUser.objects.get(id=id, activated=True,)
    return user

def _resolvePaginatedData(data: dict, resp: AppResponse = None) -> AppResponse:
    resp = resp or AppResponse()
    resp.resolve(data)
    return resp


class AuthApi:

    __MAX_AGE_REMEMBER = 60 * 60 * 24 * 7 # 7 days

    @staticmethod
    def __set_auth_cookie(response: HttpResponse, user: BMGTUser, remember: bool) -> None:
        if remember:
            response.set_cookie('id', str(user.id), samesite='strict', secure=True, httponly=True, max_age=AuthApi.__MAX_AGE_REMEMBER)
        else:
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
            remember = data['remember']
            user = BMGTUser.objects.get(did=did, activated=True,)
            if check_password(password, user.password):
                AuthApi.__set_auth_cookie(resp, user, remember)
                resp.resolve(user)
            else:
                resp.reject("Sign in failed. Please check your directory ID and password!")
        except BMGTUser.DoesNotExist:
            resp.reject("Sign in failed. Please check your directory ID!")
        except KeyError:
            resp.reject("Sign in failed. Invalid data format!")
        
        return resp

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
            id = request.COOKIES.get('id', None)
            user = BMGTUser.objects.get(id=id, activated=True)
            resp.resolve("Sign out success!")
            AuthApi.__clear_auth_cookie(resp)
        except Exception as e:
            resp.reject("Sign out failed!")
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
    def me(request: HttpRequest,) -> HttpResponse:
        try:
            resp = AppResponse()
            user = _get_session_user(request)
            if user.group != None:
                resp.resolve(user.group)
            else:
                resp.resolve(None)
        except BMGTUser.DoesNotExist:
            resp.reject("User not found!")
        except KeyError:
            resp.reject("Invalid data format!")

        return resp

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
            data = generic_paginated_query(BMGTGroup, params, semester_id=user.semester.id)
        else:
            data = generic_paginated_query(BMGTGroup, params)
        return _resolvePaginatedData(data)
    

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
                group = BMGTGroup.objects.get(id=group_id)
                if user.role == BMGTUser.BMGTUserRole.USER and user.semester_id != group.semester_id:
                    resp.reject("You cannot join a group in another semester!")
                else:
                    if group.users.count() >= _MAX_GROUP_SIZE:
                        resp.reject("Group already full!")
                    elif group.is_frozen:
                        resp.reject("Cannot join the group at this time!")
                    else:
                        user.group = group
                        user.save()
                        resp.resolve(group)
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
        try:
            resp = AppResponse()
            user: BMGTUser = _get_session_user(request)
            if user.group != None:
                if user.group.is_frozen:
                    resp.reject("Cannot leave the group at this time!")
                else:
                    user.group = None
                    user.save()
                    resp.resolve("Group left!")
            else:
                resp.reject("You are not in a group!")
        except BMGTUser.DoesNotExist:
            resp.reject("User not found!")

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
        data = generic_paginated_query(BMGTCase, pager_params_from_request(request))
        return _resolvePaginatedData(data)


    @request_error_handler
    @require_POST
    @staticmethod
    def submit(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            case_record = None # place holder
            user = _get_session_user(request)
            data = json.loads(request.body)
            case_id = int(data['case_id'])
            case_instance = BMGTCase.objects.get(id=case_id)
            if user.group != None:
                group = user.group
                if CaseApi.__case_submittable(case_instance, group):                    
                    # id to simulation case mapping
                    if case_id == 1:     # food center
                        params = data['case_params']
                        configQuery = BMGTCaseConfig.objects.filter(case_id=case_id,)
                        if configQuery.exists():
                            config = json.loads(configQuery.get().config_json)
                            params['config'] = config
                        simulation_instance = FoodDelivery(**params)
                    else:
                        resp.reject("Case not found!")

                    # create case record first. simulation eligibility is calculated based on valid case records
                    with transaction.atomic():
                        case_record = BMGTCaseRecord(
                            user=user,
                            case=case_instance, group=group, state=BMGTCaseRecord.State.RUNNING,
                            file_name = BMGTCaseRecord.get_file_name(group, user, case_instance),
                        )
                        case_record.save()

                    # run simulation
                    res = simulation_instance.run()
                    caseRecordStream = res.asFileStream()
                    caseSummary = res.asDict()
                    case_record.summary_dict = caseSummary
                    with open(_CASE_RECORD_PATH + case_record.file_name, "wb") as file:
                        file.write(caseRecordStream.getvalue())
                    case_record.state = BMGTCaseRecord.State.SUCCESS
                    case_record.score = res.score
                    case_record.performance_metric = res.performance_metric
                    case_record.save()
                    resp.resolve({
                        "case_record_id": case_record.id,
                        "summary": case_record.summary_dict,
                        "file_name": case_record.file_name,
                        })
                else:
                    resp.reject("You have reached the maximum submission for this case!")
            else:
                resp.reject("You must join a group to run the simulation!")

        except BMGTUser.DoesNotExist:
            resp.reject("Invalid credential!")
            if case_record:
                case_record.state = BMGTCaseRecord.State.FAILED
                case_record.save()
        except BMGTCase.DoesNotExist:
            resp.reject("Case not found!")
            if case_record:
                case_record.state = BMGTCaseRecord.State.FAILED
                case_record.save()
        except KeyError:
            resp.reject("Invalid data format!")
            if case_record:
                case_record.state = BMGTCaseRecord.State.FAILED
                case_record.save()
        except SimulationException as e:
            resp.reject(f"{e.args[0]}")
            if case_record:
                case_record.state = BMGTCaseRecord.State.FAILED
                case_record.save()
        except Exception:
            if case_record:
                case_record.state = BMGTCaseRecord.State.FAILED
                case_record.save()
            
            raise
            
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
    def download_case_record(request: HttpRequest, file_name:str) -> HttpResponse:
        full_path = _CASE_RECORD_PATH + file_name
        if os.path.exists(full_path):
            with open(full_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',)
                return response
        else:
            return AppResponse().reject("File not found!")
        

    @request_error_handler
    @require_GET
    @staticmethod
    def case_records_paginated(request: HttpRequest) -> HttpResponse:
        resp = AppResponse()
        user: BMGTUser = _get_session_user(request)
        if not user.group:
            resp.reject("You must join a group to view case records!")
        else:
            pagerParams = pager_params_from_request(request)
            data = generic_paginated_query(BMGTCaseRecord, pagerParams, state=BMGTCaseRecord.State.SUCCESS, group_id=user.group.id)
            _resolvePaginatedData(data, resp=resp)
        return resp

    @request_error_handler
    @require_GET
    def leader_board_paginated(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            case_id = int(request.GET.get('case_id'))
            user = _get_session_user(request)
            if case_id == 1:
                page = int(request.GET.get('page', None))
                size = int(request.GET.get('size', None))
                query_params = create_pager_params(page, size, ['-performance_metric', '-score'])
                data = generic_paginated_query(
                    BMGTCaseRecord, query_params,
                    user__semester=user.semester,
                    state=BMGTCaseRecord.State.SUCCESS,
                    case_id=case_id,
                    )
                resp.resolve(data)
            else:
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

                    created_set = BMGTUser.objects.bulk_create(obj_set)
                    resp.resolve(f"Imported {len(created_set)} users!")
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
    def set_case_config(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            configObj = {}
            for pair in data['config']:
                val1 = pair[0]
                val2 = pair[1]
                configObj[val1] = val2
            case_id = int(data['case_id'])
            querySet = BMGTCaseConfig.objects.filter(case_id=case_id)
            if not querySet.exists():
                config = BMGTCaseConfig(case_id=case_id)
            else:
                config = querySet.get()
            if case_id == _FOOD_DELIVERY_CASE_ID:
                if FoodDelivery.is_config_valid(configObj):
                    config.config_json = json.dumps(configObj)
                    config.edited_time = timezone.now()
                    config.save()
                    resp.resolve("New map applied!")
                else:
                    resp.reject("Invalid case configuration!")
            elif case_id == _CALL_CENTER_CASE_ID:
                ManageApi.set_call_center_config(configObj)
            else:
                raise BMGTCase.DoesNotExist
            
        except BMGTCase.DoesNotExist:
            resp.reject("Case not found!")
        except KeyError:
            resp.reject("Invalid data format!")

        return resp
    

    @request_error_handler
    @require_GET
    @staticmethod
    def  view_case_config(request: HttpRequest) -> HttpResponse:
        pager_params = pager_params_from_request(request)
        pager_params['case_id'] = _FOOD_DELIVERY_CASE_ID
        data = generic_paginated_query(BMGTCaseConfig, pager_params)
        return _resolvePaginatedData(data)
    

    @request_error_handler
    @require_GET
    @staticmethod
    def view_users(request: HttpRequest) -> HttpResponse:
        data = generic_paginated_query(BMGTUser, pager_params_from_request(request))
        return _resolvePaginatedData(data)
    
    @request_error_handler
    @require_POST
    @staticmethod
    def delete_users(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            arr_user_id = data['arr_user_id']
            users = BMGTUser.objects.filter(id__in=arr_user_id)
            if users.filter(role = BMGTUser.BMGTUserRole.ADMIN).exists():
                resp.reject("Cannot delete admin users!") 
            else:
                with transaction.atomic():
                    users.delete()
                resp.resolve("Users deleted!")
        except BMGTUser.DoesNotExist:
            resp.reject("User not found!")
        except KeyError:
            resp.reject("Invalid data format!")

        return resp

    @request_error_handler
    @require_GET
    @staticmethod
    def view_system_state(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            status = BMGTSystemStatus.objects.get(id=1)
            resp.resolve(status)
        except BMGTSystemStatus.DoesNotExist:
            resp.reject("System not found!")

        return resp
    
    @request_error_handler
    @require_POST
    @staticmethod
    def update_system_state(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            system = BMGTSystemStatus.objects.get(id=1)
            for key, value in data.items():
                system.__setattr__(key, value)
            system.save()
            resp.resolve("System updated!")
        except BMGTSystemStatus.DoesNotExist:
            resp.reject("System not found!")
        except KeyError:
            resp.reject("Invalid data format!")

        return resp
    

    @staticmethod
    def __set_case_submission_limit(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            case_id = data['case_id']
            max_submission = int(data['max_submission'])
            case = BMGTCase.objects.get(id=case_id)
            case.max_submission = max_submission
            case.save()
            resp.resolve(f"Case submission set to {max_submission}!")
        except BMGTCase.DoesNotExist:
            resp.reject("Case not found!")
        except KeyError:
            resp.reject("Invalid data format!")
        return resp
    

    @staticmethod
    def __get_case_submission_limit(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            case_id = request.GET.get('case_id')
            case = BMGTCase.objects.get(id=case_id)
            resp.resolve(case.max_submission)
        except BMGTCase.DoesNotExist:
            resp.reject("Case not found!")
        except KeyError:
            resp.reject("Invalid data format!")
        return resp
    
    
    @request_error_handler
    @require_http_methods(["POST", "GET"])
    @staticmethod
    def case_submission_limit(request: HttpRequest) -> HttpResponse:
        if request.method == "POST":
            return ManageApi.__set_case_submission_limit(request)
        elif request.method == "GET":
            return ManageApi.__get_case_submission_limit(request)
        
    
    @request_error_handler
    @require_GET
    @staticmethod
    def case_submissions(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            case_id = request.GET.get('case_id')
            pagerParams = pager_params_from_request(request)
            data = generic_paginated_query(BMGTCaseRecord, pagerParams, case_id=case_id)
            resp.resolve(data)
        except BMGTCase.DoesNotExist:
            resp.reject("Case not found!")
        except KeyError:
            resp.reject("Invalid data format!")

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
                semester = BMGTSemester(year=year, season=season)
                semester.save()
                resp.resolve("Semester created successfully!")
        except IntegrityError:
            resp.reject("Failed to create semester. Invalid semester arguments!")
        except KeyError:
            resp.reject("Invalid data format!")

        return resp
    
    
    @request_error_handler
    @require_POST
    @staticmethod
    def delete_semesters(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            arr_semester_id = data['arr_semester_id']
            semester = BMGTSemester.objects.filter(id__in=arr_semester_id)
            semester.delete()
            resp.resolve("Semester deleted!")
        except BMGTSemester.DoesNotExist:
            resp.reject("Semester not found!")
        except KeyError:
            resp.reject("Invalid data format!")
        except IntegrityError:
            resp.reject("Semester cannot be deleted. Please delete all the users and groups in the semester first!")

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
    def create_groups(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            semester_id = data['semester_id']
            size = int(data['size'])
            semester = BMGTSemester.objects.get(id=semester_id)
            max_group_num = BMGTGroup.objects.filter(semester_id = semester_id).aggregate(max_value=Max('number'))['max_value'] or 0
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
        data = generic_paginated_query(BMGTGroup, pager_params_from_request(request))
        return _resolvePaginatedData(data)
    
    @request_error_handler
    @require_POST 
    @staticmethod
    def delete_group(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            arr_group_id = data.get('arr_group_id', None)
            with transaction.atomic():
                groups = BMGTGroup.objects.filter(id__in=arr_group_id)
                groups.delete()
            resp.resolve("Group deleted!")
        except BMGTGroup.DoesNotExist:
            resp.reject("Group not found!")
        except KeyError:
            resp.reject("Invalid data format!")
        return resp
    

def apiStartUp():
    # handle previous case records that do not have performance metric
    records = BMGTCaseRecord.objects.filter(performance_metric__isnull=True, state = BMGTCaseRecord.State.SUCCESS)
    if records.exists():
        for r in records:
            summary = json.loads(r.summary_dict.replace("\'", "\""))
            r.performance_metric = summary['perf_metric']
            r.save()

    # create default case objects if not exist
    try:
        BMGTCase.objects.get(id=_FOOD_DELIVERY_CASE_ID)
    except BMGTCase.DoesNotExist:
        foodCenter = BMGTCase(id=_FOOD_DELIVERY_CASE_ID, name="Food Delivery", max_submission=-1, visible=False)
        foodCenter.save()

    try:
        BMGTCase.objects.get(id=_CALL_CENTER_CASE_ID)
    except BMGTCase.DoesNotExist:
        callCenter = BMGTCase(id=_CALL_CENTER_CASE_ID, name="Call Center", max_submission=-1, visible=False)
        callCenter.save()         


apiStartUp()