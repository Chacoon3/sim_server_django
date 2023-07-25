from django.contrib import admin

from .bmgt_models import *



class BMGTUserAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["user_did",]}),
    ]
    
    list_display = ["user_did", "user_first_name", "user_last_name", "create_time", "role_id", "tag_id", "user_activated",]


class CaseAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["name", "case_description"]}),
    ]

    list_display = ["name", "create_time",]


class CaseRecordAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["group_id", "case_id", "case_record_score", 'case_record_status']}),
    ]

    list_display = ["group_id", "case_id", "case_record_score", 'case_record_status']


class GroupAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["name"]}),
    ]

    list_display = ["id", "name", "create_time",]


class RoleAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["name"]}),
    ]

    list_display = ["id", "name",]


class TagAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["name"]}),
    ]

    list_display = ["id", "name",]


admin.site.register(BMGTUser, BMGTUserAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(CaseRecord, CaseRecordAdmin)
admin.site.register(BMGTGroup, GroupAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Tag, TagAdmin)