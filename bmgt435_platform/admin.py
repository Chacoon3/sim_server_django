from django.contrib import admin
from .bmgtModels import *



class BMGTUserAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["did", "first_name", "last_name", "role",]}),
    ]
    
    list_display = ["id", "did", "first_name", "last_name", "create_time", "role", "group_id", "activated",]


class CaseAdmin(admin.ModelAdmin):
    fieldsets = [
       ("None",  {"fields": ["name", "max_submission",]}),
    ]

    list_display = ["id", "name", "create_time", "max_submission", "visible",]


class CaseRecordAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["group_id", "case_id", "state", "score",]}),
    ]

    list_display = ["id", "group_id", "case_id", "state", "score", "summary_dict"]


class GroupAdmin(admin.ModelAdmin):

    list_display = ["id", "create_time",]


class TagAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["name"]}),
    ]

    list_display = ["id", "name",]


admin.site.register(BMGTUser, BMGTUserAdmin)
admin.site.register(BMGTCase, CaseAdmin)
admin.site.register(BMGTCaseRecord, CaseRecordAdmin)
admin.site.register(BMGTGroup, GroupAdmin)
admin.site.register(BMGTTag, TagAdmin)