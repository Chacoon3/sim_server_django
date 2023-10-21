from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .apis import *


urlpatterns = [

    path("api/auth/sign-in", AuthApi.sign_in, name="sign-in"),
    path("api/auth/sign-up", AuthApi.sign_up, name="sign-up"),
    path("api/auth/forget-password", AuthApi.password_reset, name="forget-password"),
    path('api/auth/sign-out', AuthApi.sign_out, name='sign-out'),


    path('api/users/me', UserApi.me, name='user-me'),


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


    path('api/manage/user/import/semester/<int:semester_id>', ManageApi.import_users,),
    path('api/manage/user/view', ManageApi.view_users,),

    path('api/manage/group/create', ManageApi.batch_create_group,),
    path('api/manage/group/paginated', ManageApi.group_view_paginated,),

    path('api/manage/semester/create', ManageApi.create_semester,),
    path('api/manage/semester/all', ManageApi.get_semesters,),

    path('api/manage/system/status', ManageApi.system_status,),
    path('api/manage/feedback/paginated', FeedbackApi.feedback_paginated,),

    
    path('api/feedback/post', FeedbackApi.post, ),

    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # for serving static files in development
