from django.db import models
from django.utils import timezone
import datetime


"""
@: Database schema
"""


APP_LABEL = "bmgt_platform"


class object(models.Model):
    class Meta:
        abstract = True
        app_label = APP_LABEL

    id = models.AutoField(auto_created=True, primary_key=True)
    create_time = models.DateTimeField(default=timezone.now)


class Role(object):
    # class Meta:
    #     app_label = APP_LABEL

    name=models.CharField(max_length=10, default="")



class Tag(object):
    # class Meta:
    #     app_label = APP_LABEL


    name=models.CharField(max_length=10, default="")



class BMGTGroup(object):
    # class Meta:
    #     app_label = APP_LABEL

    name=models.CharField(max_length=30, default="")



class BMGTUser(object):
    # class Meta:
    #     app_label = APP_LABEL


    user_did = models.CharField(max_length=100, auto_created=False, null=False)
    user_first_name = models.CharField(max_length = 60, null=True)
    user_last_name = models.CharField(max_length = 60, null=True)
    user_password = models.CharField(max_length = 100, default="")
    user_activated = models.BooleanField(default=False)

    role_id = models.ForeignKey(Role, on_delete=models.CASCADE, null=True)
    tag_id = models.ForeignKey(Tag, on_delete=models.CASCADE, null=True)
    group_id = models.ForeignKey(BMGTGroup, on_delete=models.CASCADE, null=True)

    def full_name(self):
        name = ''
        if self.user_first_name and self.user_last_name:
            name = self.user_first_name + " " + self.user_last_name
        elif self.user_first_name:
            name = self.user_first_name
        elif self.user_last_name:
            name = self.user_last_name
        return name
    


class Case(object):
    # class Meta:
    #     app_label = APP_LABEL

    
    name = models.CharField(max_length=50)
    case_description = models.TextField(null=True)
    


class CaseRecord(object):
    # class Meta:
    #     app_label = APP_LABEL


    group_id = models.ForeignKey(BMGTGroup, on_delete=models.CASCADE)
    case_id = models.ForeignKey(Case, on_delete=models.CASCADE)
    case_record_status = models.IntegerField(default=0)
    case_record_score = models.FloatField(default=0.0)

    # the detail of each simulation cases should be dramatically different. They are stored in json format owing to the unstructured nature.
    case_record_detail_json = models.TextField(null=True)