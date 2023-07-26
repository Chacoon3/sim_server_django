from django.urls import path
from .apis import *



urlpatterns = [

    path("api/auth/sign-in", Auth.sign_in, name="sign-in"),
    path("api/auth/sign-up", Auth.sign_up, name="sign-up"),
    path("api/auth/forget-password", Auth.forget_password, name="forget-password"),


    path('api/users/me', UserApi.me, name='user-me'),
    path('api/users', UserApi.users, name='users'),
    path('api/users-paginated', UserApi.user_paginated, name='users_paginated'),

    path('api/groups', GroupApi.groups, ),
    path('api/groups-paginated', GroupApi.groups_paginated, ),

    path('api/cases', CaseApi.cases, ),
    path('api/cases-paginated', CaseApi.cases_paginated,),

    path('api/case-records', CaseRecordApi.case_records, ),
    path('api/case-records-paginated', CaseRecordApi.case_records_paginated,),

    path("api/tags", TagApi.tags, name="tags"),
    path("api/tags-paginated", TagApi.tags_paginated, name="tags_paginated"),

    path("api/roles", RoleApi.roles, name="roles"),
    path("api/roles-paginated", RoleApi.roles_paginated, name="roles_paginated"),

    path('api/manage/import-users', ManagementApi.import_users, name='import_users'),
]
