from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST, require_GET,  require_http_methods
from django.contrib.auth.hashers import make_password, check_password
from django.db import IntegrityError

from .apps import bmgt435_file_sys as app_file_system
from .simulation.Cases import FoodCenter
from .bmgtModels import *
from .utils.statusCode import Status
from .utils.jsonUtils import serialize_models, serialize_model_instance, serialize_simulation_result
from .utils.apiUtils import request_error_handler, password_valid, generic_unary_query, generic_paginated_fetch

import pandas as pd
import json
import io


CASE_RECORD_PATH = app_file_system.base_location.__str__() + "/case_records/"


class AuthApi:

    @staticmethod
    def __set_auth_cookie(response: HttpResponse, user: BMGTUser) -> None:
        response.set_cookie('id', str(user.id),
                            samesite='none', secure=True, httponly=True)
        response.set_cookie('role', user.role, samesite='none',
                            secure=True, httponly=True)  # for previlege control

    @staticmethod
    def __clear_auth_cookie(response: HttpResponse) -> None:
        response.delete_cookie('id', samesite='none')
        response.delete_cookie('role', samesite='none')

    @request_error_handler
    @require_POST
    @staticmethod
    def sign_in(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        data = json.loads(request.body)
        did = data['did']
        password = data['password']

        user = BMGTUser.objects.filter(did=did, activated=True, )
        if user:
            user = user[0]
            if user and user.password and check_password(password, user.password):
                resp.status_code = Status.OK
                AuthApi.__set_auth_cookie(resp, user)
                resp.write(serialize_model_instance(user))
            else:
                resp.status_code = Status.UNAUTHORIZED
                resp.write(
                    "Sign in failed. Please check your directory ID and password!")
        else:
            resp.status_code = Status.NOT_FOUND
            resp.write(
                "Sign in failed! Please check your directory ID and password!")

        return resp

    @request_error_handler
    @require_POST
    @staticmethod
    def sign_up(request: HttpRequest) -> HttpResponse:

        resp = HttpResponse()
        data = json.loads(request.body)
        did = data['did']
        password = data['password']

        user = BMGTUser.objects.filter(
            did=did, activated=False, )

        if user:
            user = user[0]
            if user and password_valid(password):
                user.password = make_password(password)
                user.activated = True
                user.save()
                resp.status_code = Status.OK
                resp.write("Sign up success!")
            else:
                resp.status_code = Status.BAD_REQUEST
                resp.write(
                    "Sign up failed! Password should contain at least 8 alphanumeric characters!")
        else:
            resp.status_code = Status.NOT_FOUND
            resp.write("Sign up failed! Please check your directory ID!")

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
        resp = HttpResponse()
        id = request.COOKIES.get('id', None)
        if id:
            user = BMGTUser.objects.get(id=id, activated=1, )
            resp.write(serialize_model_instance(user))
            resp.status_code = Status.OK
        else:
            resp.write("Unauthorized!")
            resp.status_code = Status.UNAUTHORIZED

        return resp

    @request_error_handler
    @staticmethod
    def users(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        match request.method:
            case 'GET':
                params = request.GET.dict()
                users = BMGTUser.objects.filter(
                    **params, activated=1, )
                resp.write(serialize_models(users))
                resp.status_code = Status.OK

            # case 'DELETE':
            #     params = request.GET.dict()
            #     if not params:
            #         resp.write("Unconditional deletion is not allowed!")
            #         resp.status_code = Status.BAD_REQUEST
            #     else:
            #         users = BMGTUser.objects.filter(
            #             **params, activated=1, )
            #         if users:
            #             count_delete = BMGTUser.objects.delete(users)[0]
            #             resp.write(f"{count_delete} user deleted!")
            #             resp.status_code = Status.DELETED
            #         else:
            #             resp.write("User not found!")
            #             resp.status_code = Status.NOT_FOUND

            case _:
                resp.write("Method not allowed!")
                resp.status_code = Status.METHOD_NOT_ALLOWED

        return resp


class GroupApi:

    @request_error_handler
    @require_GET
    @staticmethod
    def get_group(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        group_id = request.GET.get('id', None)
        group_id = int(group_id) if group_id else None
        group_query = BMGTGroup.objects.filter(id = group_id )
        if group_query.exists():
            group = group_query.get()
            resp.write(serialize_model_instance(group))
            resp.status_code = Status.OK
        else:
            resp.write("Group not found!")
            resp.status_code = Status.NOT_FOUND

        return resp

    @request_error_handler
    @require_GET
    @staticmethod
    def groups_paginated(request: HttpRequest,) -> HttpResponse:
        return generic_paginated_fetch(BMGTGroup, request)

    @request_error_handler
    @require_POST
    @staticmethod
    def create_group(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        user_id = request.COOKIES.get('id', None)
        user_exists = user_id and BMGTUser.objects.filter(
            id=user_id, activated=1, ).exists()
        if user_exists:
            user = BMGTUser.objects.get(
                id=user_id, activated=1, )
        if user.group_id == None:
            new_group = BMGTGroup.objects.create()
            new_group.save()
            user.group_id = new_group
            user.save()
            resp.write(serialize_model_instance(new_group))
            resp.status_code = Status.CREATED
        else:
            resp.write(
                "Cannot create another group while you are alreay in a group!")
            resp.status_code = Status.BAD_REQUEST

        return resp

    @request_error_handler
    @require_POST
    @staticmethod
    def join_group(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        user_id = request.COOKIES.get('id', None)
        user_exists = user_id and BMGTUser.objects.filter(
            id=user_id, activated=1, ).exists()
        if user_exists:
            user = BMGTUser.objects.get(
                id=user_id, activated=1, )
            if user.group_id == None:
                data = json.loads(request.body)
                group_id = data.get('group_id', None)
                group_exists = group_id and BMGTGroup.objects.filter(
                    id=group_id, ).exists()
                if group_exists:
                    group = BMGTGroup.objects.get(
                        id=group_id, )
                    user.group_id = group
                    user.save()
                    resp.write(serialize_model_instance(group))
                    resp.status_code = Status.OK
                else:
                    resp.write("Group not found!")
                    resp.status_code = Status.NOT_FOUND
            else:
                resp.write(
                    "Cannot join another group while you are alreay in a group!")
                resp.status_code = Status.BAD_REQUEST
        else:
            resp.write("Unauthorized!")
            resp.status_code = Status.UNAUTHORIZED

        return resp

    @request_error_handler
    @require_POST
    @staticmethod
    def leave_group(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        user_id = request.COOKIES.get('id', None)
        user_exists = user_id and BMGTUser.objects.filter(
            id=user_id, activated=1, ).exists()
        if user_exists:
            user = BMGTUser.objects.get(
                id=user_id, activated=1, )
            if user.group_id != None:
                group = BMGTGroup.objects.filter(
                    id=user.group_id.id, )
                user.group_id = None
                user.save()
                if group.exists():  # if group is empty, delete it
                    group = group.get()
                    if group.users.count() == 0:
                        group.delete()
                resp.write("Group left!")
                resp.status_code = Status.OK
            else:
                resp.write("You are not in a group!")
                resp.status_code = Status.BAD_REQUEST
        else:
            resp.write("Unauthorized!")
            resp.status_code = Status.UNAUTHORIZED

        return resp


class CaseApi:
    @request_error_handler
    @require_GET
    @staticmethod
    def get_case(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        case_id = request.GET.get('case_id', None)
        case_query = case_id and BMGTCase.objects.filter(
            id=case_id, state=BMGTCaseRecord.BMGTCaseRecordState.SUCCESS)
        if case_query.exists():
            case = case_query.get()
            resp.write(serialize_model_instance(case))
            resp.status_code = Status.OK
        else:
            resp.write("Case not found!")
            resp.status_code = Status.NOT_FOUND

    @request_error_handler
    @require_GET
    @staticmethod
    def cases_paginated(request: HttpRequest) -> HttpResponse:
        return generic_paginated_fetch(BMGTCase, request)

    # @request_error_handler
    # @require_POST
    # @staticmethod
    # def run_once(request: HttpRequest) -> HttpResponse:
    #     resp = HttpResponse()
    #     data = json.loads(request.body)
    #     case_id = data.get('case_id')
    #     group_id = data.get('group_id')
    #     if not case_id:
    #         resp.status_code = Status.NOT_FOUND
    #         resp.write("Case not found!")
    #     elif not group_id:
    #         resp.status_code = Status.BAD_REQUEST
    #         resp.write("You must join a group to run the simulation!")
    #     else:
    #         match case_id:
    #             case '1':
    #                 caseInst = FoodCenter(num_iterations=100, centers=[
    #                                       '13', ], policies=[(100, 3000)])
    #                 res = caseInst.simulate(True)
    #                 case_detail = json.dumps(res)
    #                 resp.status_code = Status.OK
    #                 resp.write(case_detail)
    #                 new_case_record = BMGTCaseRecord(
    #                     case_id=1, case_detail=case_detail)
    #             case _:
    #                 resp.status_code = Status.NOT_FOUND
    #                 resp.write("Case not found!")

    #     return resp

    @staticmethod
    def onCaseCompleted(case_record_id: int,  simRes):
        try:
            case_record = BMGTCaseRecord.objects.get(id=case_record_id)
            if simRes:
                case_detail = serialize_simulation_result(simRes)
                case_record.detail_json = case_detail
                case_record.score = simRes.score
                case_record.state = BMGTCaseRecord.BMGTCaseRecordState.SUCCESS
            else:
                case_record.state = BMGTCaseRecord.BMGTCaseRecordState.FAILED
            case_record.save()

        except Exception:
            case_record.state = BMGTCaseRecord.BMGTCaseRecordState.FAILED
            case_record.save()
            raise

    @request_error_handler
    @require_POST
    @staticmethod
    def submit(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        user_id = request.COOKIES.get('id', None)
        user = BMGTUser.objects.filter(id=user_id, activated=1, )
        if user.exists():
            user = user.get()
            if user.group_id != None:
                group = user.group_id
                data = json.loads(request.body)
                case_id = int(data.get('case_id'))
                case = BMGTCase.objects.get(id=case_id)
                count_submission = BMGTCaseRecord.objects.filter(
                    case_id=case_id, group_id=user.group_id,
                    state__in=[
                        BMGTCaseRecord.BMGTCaseRecordState.RUNNING, BMGTCaseRecord.BMGTCaseRecordState.SUCCESS]
                ).count()
                if case.max_submission == -1 or count_submission < case.max_submission:
                    # run logic
                    match case_id:
                        case 1:
                            params = data.get('case_params')
                            if params:
                                # original logic using multiprocessing

                                # caseInst = FoodCenter(**params)
                                # case_record = BMGTCaseRecord(case_id = case, group_id = group,)
                                # case_record.save()
                                # appConfig.app_process_pool.apply_async(func = caseInst.run, callback=lambda res: CaseApi.onCaseCompleted(case_record.id, res))
                                # resp.write(serialize_model_instance(case_record))
                                # resp.status_code = Status.OK
                                #
                                #  blocking logic
                                caseInst = FoodCenter(**params)
                                res = caseInst.run()
                                record_bytes = res.as_bytes()
                                record_dict = res.as_dictionary()
                                case_record = BMGTCaseRecord(
                                    user_id=user,
                                    case_id=case, group_id=group, score=res.score, state=BMGTCaseRecord.BMGTCaseRecordState.SUCCESS,
                                    summary_json = record_dict,)
                                case_record.save()
                                app_file_system.save(
                                    case_record.case_record_file_name, record_bytes)
                                resp.write(json.dumps({
                                    "case_record_id": case_record.id,
                                    "summary": record_dict,
                                }))
                                resp.status_code = Status.OK
                            else:
                                resp.write("Invalid data format!")
                                resp.status_code = Status.INTERNAL_SERVER_ERROR
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
        else:
            resp.write("Unauthorized!")
            resp.status_code = Status.UNAUTHORIZED

        return resp


class CaseRecordApi:
    @request_error_handler
    @staticmethod
    def get_case_record(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        case_record_id = request.GET.get('case_record_id', None)
        case_record_query = case_record_id and BMGTCaseRecord.objects.filter(
            id=case_record_id, )
        if case_record_query.exists():
            case_record = case_record_query.get()
            resp.write(serialize_model_instance(case_record))
            resp.status_code = Status.OK
        else:
            resp.write("Case record not found!")
            resp.status_code = Status.NOT_FOUND

        return resp

    @request_error_handler
    @require_GET
    @staticmethod
    def get_case_record_file(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        case_record_id = request.GET.get('case_record_id', None)
        case_record_query = BMGTCaseRecord.objects.filter(
            id=case_record_id, )
        if case_record_query.exists():
            pass

    @request_error_handler
    @require_GET
    @staticmethod
    def case_records_paginated(request: HttpRequest) -> HttpResponse:
        return generic_paginated_fetch(BMGTCaseRecord, request, state=BMGTCaseRecord.BMGTCaseRecordState.SUCCESS)


class TagApi:

    @request_error_handler
    @staticmethod
    def tags(request: HttpRequest) -> HttpResponse:
        return generic_unary_query(BMGTTag, request)

    @request_error_handler
    @require_GET
    @staticmethod
    def tags_paginated(request: HttpRequest) -> HttpResponse:
        return generic_paginated_fetch(BMGTTag, request)


class ManageApi:

    @request_error_handler
    @require_POST
    @staticmethod
    def import_users(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        if request.body:
            with io.BytesIO(request.body) as file:
                user_csv = pd.read_csv(file, encoding='utf-8')
                format_valid = len(user_csv.columns) == 3 and all(user_csv.columns == [
                    'user_first_name', 'user_last_name', 'directory_id'])
                if format_valid:
                    user_csv.columns = ['first_name', 'last_name', 'did']
                    user_csv.applymap(lambda x: x.strip())
                    obj_set = [BMGTUser(**row)
                               for row in user_csv.to_dict('records')]
                    try:
                        BMGTUser.objects.bulk_create(obj_set, batch_size=40)
                        resp.status_code = Status.OK
                        resp.write("Imported!")
                    except IntegrityError:
                        resp.status_code = Status.BAD_REQUEST
                        resp.write(
                            "Import failed! Please remove the duplicated directory ID's from the CSV file!")
                else:
                    resp.status_code = Status.BAD_REQUEST
                    resp.write(
                        "Import failed! Please upload a CSV file that contains the following columns: user_first_name, user_last_name, directory_id")
        else:
            resp.status_code = Status.BAD_REQUEST
            resp.write(
                "Import failed! Please upload a CSV file that contains the following columns: user_first_name, user_last_name, directory_id")

        return resp

    @request_error_handler
    @staticmethod
    @require_POST
    def clean_groups(request: HttpRequest) -> HttpResponse:
        resp = HttpResponse()
        count_deleted = 0
        for group in BMGTGroup.objects.iterator():
            if group.users.exists() == False:
                group.delete()
                count_deleted += 1
        resp.status_code = Status.DELETED
        resp.write(f"{count_deleted} dirty groups deleted!")
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
        return generic_paginated_fetch(BMGTUser, request)
