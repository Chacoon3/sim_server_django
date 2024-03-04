from django.urls import path
from .apis import *


urlpatterns = [

    path("api/auth/sign-in", AuthApi.sign_in, name="sign-in"),
    path("api/auth/sign-up", AuthApi.sign_up, name="sign-up"),
    path("api/auth/forget-password", AuthApi.password_reset, name="forget-password"),
    path('api/auth/sign-out', AuthApi.sign_out, name='sign-out'),


    path('api/users/me', UserApi.me, name='user-me'),


    path('api/groups/me', GroupApi.me,),
    path('api/groups/get', GroupApi.get_group, ),
    path('api/groups/paginated', GroupApi.groups_paginated, ),
    path('api/groups/join', GroupApi.join_group, ),
    path('api/groups/leave', GroupApi.leave_group, ),


    path('api/cases/get', CaseApi.get, ),
    path('api/cases/paginated', CaseApi.cases_paginated,),
    path('api/cases/submit', CaseApi.submit, ),


    path('api/case-records/get', CaseRecordApi.get_case_record, ),
    path('api/case-records/file/get', CaseRecordApi.get_case_record_file, ),
    path('api/case-records/paginated', CaseRecordApi.case_records_paginated,),
    path("api/leader-board/paginated", CaseRecordApi.leader_board_paginated ),


    path('api/manage/users/import/semester/<int:semester_id>', ManageApi.import_users,),
    path('api/manage/users/view', ManageApi.view_users,),

    path('api/manage/groups/create', ManageApi.create_group,),
    path('api/manage/groups/paginated', ManageApi.group_view_paginated,),
    path('api/manage/groups/delete', ManageApi.delete_group,),

    path('api/manage/case/submission-limit', ManageApi.set_case_submission_limit,),

    path('api/manage/food-delivery-config/update', ManageApi.set_food_delivery_config,),
    path('api/manage/food-delivery-config/view', ManageApi.view_food_delivery_config,),

    path('api/manage/semesters/create', ManageApi.create_semester,),
    path('api/manage/semesters/all', ManageApi.get_semesters,),
    path('api/manage/semesters/delete', ManageApi.delete_semesters,),

    path('api/manage/system/view', ManageApi.view_system_state,),
    path('api/manage/system/update', ManageApi.update_system_state,),
    
    path('api/feedbacks/post', FeedbackApi.post, ),
    path('api/manage/feedbacks/paginated', FeedbackApi.feedback_paginated,),
    
]
