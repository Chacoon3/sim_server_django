from django.contrib import admin
from .bmgtModels import *



class BMGTUserAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["did", "first_name", "last_name", "role", "group_id"]}),
    ]
    
    list_display = ["id", "did", "first_name", "last_name", "create_time", "role", "group_id", "activated",]


class CaseAdmin(admin.ModelAdmin):
    # fieldsets = [
    #     ("None", {"fields": ["name", "case_description"]}),
    # ]

    list_display = ["id", "name", "create_time", "visible"]


class CaseRecordAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["group_id", "case_id", "score",]}),
    ]

    list_display = ["id", "group_id", "case_id", "score"]


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