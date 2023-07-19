from django.urls import path
from .apis import *



urlpatterns = [
    path("sign_in", UserApi.sign_in, name="sign_in"),
    path("sign_up", UserApi.sign_up, name="sign_up"),
    path("forget_password", UserApi.forget_password, name="forget_password"),
    path("get_user_info", UserApi.get_user_info, name="get_user_info"),
    path("get_user_list", UserApi.get_user_list, name="get_user_list"),

    path("get_tag_info", TagApi.get_tag_info, name="get_tag_info"),
    path("get_tag_list", TagApi.get_tag_list, name="get_tag_list"),

    path("get_group_info", GroupApi.get_group_info, name="get_group_info"),
    path("get_group_list", GroupApi.get_group_list, name="get_group_list"),
    
    path("get_case_info", CaseApi.get_case_info, name="get_case_info"),
    path("get_case_list", CaseApi.get_case_list, name="get_case_list"),
    
    path("get_case_record_info", CaseRecordApi.get_case_record_info, name="get_case_record_info"),
    path("get_case_record_list", CaseRecordApi.get_case_record_list, name="get_case_record_list"),
]
