from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.hashers import make_password, check_password
from django.db import IntegrityError, transaction
from django.db.models import Max

from .apps import bmgt435_file_system
from .simulation import FoodDelivery, SimulationException
from .bmgtModels import *
from .utils.apiUtils import request_error_handler, password_valid, generic_paginated_query, pager_params_from_request, create_pager_params, AppResponse
from .utils.databaseUtils import InMemoryCache

import pandas as pd
import json
import io


"""
All requests have been verified to have valid user id except for those of the Auth.
"""


CASE_RECORD_PATH = bmgt435_file_system.base_location.__str__() + "case_records/"
MAX_GROUP_SIZE = 4
FOOD_DELIVERY_CASE_ID = 1


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
                group = BMGTGroup.objects.get(id=group_id)
                if user.role == BMGTUser.BMGTUserRole.USER and user.semester_id != group.semester_id:
                    resp.reject("You cannot join a group in another semester!")
                else:
                    if group.users.count() >= MAX_GROUP_SIZE:
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
        return generic_paginated_query(BMGTCase, pager_params_from_request(request))


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
                    match case_id:
                        case 1:     # food center
                            params = data.get('case_params')
                            configQuery = BMGTCaseConfig.objects.filter(case_id=case_id,)
                            if configQuery.exists():
                                config = json.loads(configQuery.get().config_json)
                                params['config'] = config
                            simulation_instance = FoodDelivery(**params)
                        case _:
                            resp.reject("Case not found!")

                    # create case record first. simulation eligibility is calculated based on valid case records
                    with transaction.atomic():
                        case_record = BMGTCaseRecord(
                            user=user,
                            case=case_instance, group=group, state=BMGTCaseRecord.State.RUNNING,
                            file_name = BMGTCaseRecord.generate_file_name(group, user, case_instance)
                        )
                        case_record.save()

                    # run simulation
                    res = simulation_instance.run()
                    case_detail_bytes = res.detail_as_excel_stream()
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
    def update_food_delivery_config(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            semester_id = data['semester_id']
            case_id = FOOD_DELIVERY_CASE_ID
            query = BMGTCaseConfig.objects.filter(case_id=case_id, )
            if query.exists():
                config = query.get()
            else:
                with transaction.atomic():
                    config = BMGTCaseConfig(case_id=case_id,)
                    config.save()
            
            params = dict(data['config'])
            if FoodDelivery.is_config_valid(params):
                config.config_json = json.dumps(params)
                config.edited_time = timezone.now()
                config.save()
                resp.resolve("Case configured!")
            else:
                resp.reject("Invalid case configuration!")
            
        except BMGTCase.DoesNotExist:
            resp.reject("Case not found!")
        except KeyError:
            resp.reject("Invalid data format!")

        return resp
    

    @request_error_handler
    @require_GET
    @staticmethod
    def  view_food_delivery_config(request: HttpRequest) -> HttpResponse:
        pager_params = pager_params_from_request(request)
        pager_params['case_id'] = FOOD_DELIVERY_CASE_ID
        return generic_paginated_query(BMGTCaseConfig, pager_params)



    @request_error_handler
    @require_GET
    @staticmethod
    def view_users(request: HttpRequest) -> HttpResponse:
        return generic_paginated_query(BMGTUser, pager_params_from_request(request))

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
    def create_group(request: HttpRequest) -> HttpResponse:
        try:
            resp = AppResponse()
            data = json.loads(request.body)
            semester_id = data['semester_id']
            size = int(data['size'])
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