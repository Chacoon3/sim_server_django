from django.urls import path
from .apis import *



urlpatterns = [

    path("api/auth/sign-in", Auth.sign_in, name="sign-in"),
    path("api/auth/sign-up", Auth.sign_up, name="sign-up"),
    path("api/auth/forget-password", Auth.forget_password, name="forget-password"),


    path('api/users/me', UserApi.me,),
    path('api/users', UserApi.users,),
    path('api/users/<int:id>', UserApi.users, ),
    path('api/users_paginated', UserApi.user_paginated, ),

    # path("user/get-user-info", UserApi.users, name="get-user-info"),
    # path("user/get-user-list", UserApi.get_user_list, name="get-user-list"),

    # path("tag/get-tag-info", TagApi.get_tag_info, name="get-tag-info"),
    # path("tag/get-tag-list", TagApi.get_tag_list, name="get-tag-list"),

    # path("group/get-group-info", GroupApi.get_group_info, name="get-group-info"),
    # path("group/get-group-list", GroupApi.get_group_list, name="get-group-list"),
    
    # path("case/get-case-info", CaseApi.get_case_info, name="get-case-info"),
    # path("case/get-case-list", CaseApi.get_case_list, name="get-case-list"),
    # path("case/run-case", CaseApi.run_case, name="run-case"),  
    # path("case/get-case-record-info", CaseRecordApi.get_case_record_info, name="get-case-record-info"),
    # path("case/get-case-record-list", CaseRecordApi.get_case_record_list, name="get-case-record-list"),

]
