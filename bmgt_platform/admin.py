from django.contrib import admin

from .bmgt_models import *



class BMGTUserAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["user_did",]}),
    ]
    
    list_display = ["user_did", "user_first_name", "user_last_name", "user_create_time", "role_id", "tag_id", "user_activated",]


class CaseAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["case_id"]}),
    ]

    list_display = ["case_id", "case_name", "case_create_time",]


class CaseRecordAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["case_record_id"]}),
    ]

    list_display = ["case_record_id", "case_record_create_time",]


class GroupAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["group_id"]}),
    ]

    list_display = ["group_id", "group_name", "group_create_time",]


class RoleAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["role_id"]}),
    ]

    list_display = ["role_id", "role_name",]


class TagAdmin(admin.ModelAdmin):
    fieldsets = [
        ("None", {"fields": ["tag_id"]}),
    ]

    list_display = ["tag_id", "tag_name",]


admin.site.register(BMGTUser, BMGTUserAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(CaseRecord, CaseRecordAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Tag, TagAdmin)