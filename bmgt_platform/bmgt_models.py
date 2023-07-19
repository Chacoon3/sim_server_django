from django.db import models
from django.utils import timezone
from django.contrib import admin
import datetime


"""
@: Database schema
"""


APP_LABEL = "bmgt_platform"


class Role(models.Model):
    class Meta:
        app_label = APP_LABEL


    role_id=models.IntegerField(auto_created=True, primary_key=True)
    role_name=models.CharField(max_length=10, default="")



class Tag(models.Model):
    class Meta:
        app_label = APP_LABEL


    tag_id=models.IntegerField(auto_created=True, primary_key=True)
    tag_name=models.CharField(max_length=10, default="")



class User(models.Model):
    class Meta:
        app_label = APP_LABEL


    user_did = models.CharField(max_length=100, primary_key=True)
    user_first_name = models.CharField(max_length = 60, null=True)
    user_last_name = models.CharField(max_length = 60, null=True)
    user_email = models.CharField(max_length = 70, null=True)
    user_password = models.CharField(max_length = 50)
    user_create_time = models.DateTimeField(default=timezone.now)
    user_role_id = models.ForeignKey(Role, on_delete=models.CASCADE, null=True)
    user_tag_id = models.ForeignKey(Tag, on_delete=models.CASCADE, null=True)
    user_activated = models.BooleanField(default=False)
    


class Group(models.Model):
    class Meta:
        app_label = APP_LABEL

    group_id=models.IntegerField(auto_created=True, primary_key=True)
    group_name=models.CharField(max_length=30, default="")
    group_create_time=models.DateTimeField()
    group_owner_id=models.ForeignKey(User, on_delete=models.CASCADE,)



class Case(models.Model):
    class Meta:
        app_label = APP_LABEL

    
    case_id = models.IntegerField(auto_created=True, primary_key=True)
    case_name = models.CharField(max_length=50)
    case_create_time = models.DateTimeField()
    case_description = models.TextField(null=True)
    


class CaseRecord(models.Model):
    class Meta:
        app_label = APP_LABEL


    case_record_id = models.IntegerField(auto_created=True, primary_key=True)
    group_id = models.ForeignKey(Group, on_delete=models.CASCADE)
    case_id = models.ForeignKey(Case, on_delete=models.CASCADE)
    case_record_create_time = models.DateTimeField()
    case_record_status = models.IntegerField(default=0)
    case_record_score = models.FloatField(default=0.0)
    
    # the detail of each simulation cases should be dramatically different. They are stored in json format owing to the unstructured nature.
    case_record_detail_json = models.TextField(null=True)