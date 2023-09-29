from django.db import models
from django.db.models import QuerySet
from django.conf import settings
from django.utils import timezone
from .apps import BmgtPlatformConfig
import random

"""
@: Database schema
@: Field Naming Convention: snake_case without class name prefix
"""


APP_LABEL = BmgtPlatformConfig.name


class BinaryIntegerFlag(models.IntegerChoices):
    FALSE = 0
    TRUE = 1


class BMGTModelBase(models.Model):
    class Meta:
        abstract = True
        app_label = APP_LABEL

    # query_editable_fields = []

    id = models.AutoField(auto_created=True, primary_key=True, null=False)
    create_time = models.DateTimeField(auto_created=True, default=timezone.now, null=False)

    def as_dictionary(self) -> dict:
        """
        global interface for json serialization
        should be implemented by all subclasses
        the dictionary should be json serializable
        """
        raise NotImplementedError("as dictionary method not implemented")

    @property
    def formatted_create_time(self):
        # return self.create_time.astimezone().isoformat()
        return timezone.make_naive(self.create_time).isoformat(sep=' ', timespec='seconds')

    # def set_fields(self, save=False, **kwargs):
    #     for field in kwargs.keys():
    #         if field in self.query_editable_fields:
    #             setattr(self, field, kwargs[field])
    #     if save:
    #         self.save()


# class BMGTTag(BMGTModelBase):

#     query_editable_fields = ['name', ]
#     name = models.CharField(max_length=10, null=False, unique=True, default='')

#     def as_dictionary(self) -> dict:
#         return {
#             "id": self.id,
#             "name": self.name,
#         }

class BMGTSemester(BMGTModelBase):

    class Meta:
        unique_together = ('year', 'season')

    def semester_year_validator(year):
        return year >= 2022

    year = models.IntegerField(null=False, unique=False, validators=[semester_year_validator])
    season = models.CharField(max_length=10, null=False, unique=False, choices=[
        ("spring", "spring"), ("summer", "summer"), ("fall", "fall")
    ])

    @property
    def name(self) -> str:
        return f"{self.year}-{self.season}"

    def as_dictionary(self) -> dict:
        return {
            "id": self.id,
            "year": self.year,
            "season": self.season,
            "name": self.name,
        }


class BMGTGroup(BMGTModelBase):

    number = models.IntegerField(null=False, unique=False)  # group number
    semeter = models.ForeignKey(BMGTSemester, on_delete=models.SET_NULL, null=True)

    @property
    def users(self) -> QuerySet:
        return BMGTUser.objects.filter(group_id=self.id)
    
    @property
    def name(self) -> str:
        return f"Group {self.number}"

    def as_dictionary(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "users": [user.as_dictionary() for user in self.users],
            "semester_id": self.semeter.id if self.semeter else None,
            "semester_name": self.semeter.name if self.semeter else None,
        }

class BMGTUser(BMGTModelBase):

    class BMGTUserRole(models.TextChoices):
        ADMIN = 'admin'
        USER = 'user'

    # query_editable_fields = ["first_name",
    #                          "last_name", "role", "group_id", "activated", ]

    did = models.CharField(
        max_length=60, auto_created=False, null=False, unique=True,)
    first_name = models.CharField(max_length=60, null=False)
    last_name = models.CharField(max_length=60, null=False)
    # stores the password hash
    password = models.CharField(max_length=100,  null=False, default="")
    activated = models.IntegerField(
        choices=BinaryIntegerFlag.choices, default=BinaryIntegerFlag.FALSE, null=False,)
    role = models.CharField(choices=BMGTUserRole.choices,
                            default=BMGTUserRole.USER, null=False, max_length=5)
    group = models.ForeignKey(
        BMGTGroup, on_delete=models.SET_NULL, null=True)
    semester = models.ForeignKey(BMGTSemester, on_delete=models.SET_NULL, null=True)  # allow null for admin

    @property
    def name(self):
        if self.first_name and self.last_name:
            name = self.first_name + " " + self.last_name
        elif self.first_name:
            name = self.first_name
        elif self.last_name:
            name = self.last_name
        else:
            name = "Anonymous"
        return name

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time=self.formatted_create_time,
            did=self.did,
            first_name=self.first_name,
            last_name=self.last_name,
            role=self.role,
            group_id=self.group.id if self.group else None,
            group_name=self.group.name if self.group else None,
            semester_id=self.semester.id if self.semester else None,
            semester_name = self.semester.name if self.semester else None,
        )
    

class BMGTCase(BMGTModelBase):

    # query_editable_fields = ["name", "description", ]

    name = models.CharField(max_length=50, null=False, default='')
    visible = models.BooleanField(default=True, null=False)
    max_submission = models.IntegerField(default=5, null=False, unique=False)

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time=self.formatted_create_time,
            name=self.name,
        )


class BMGTCaseRecord(BMGTModelBase):

    # query_editable_fields = ["group_id", "case_id", "score", ]

    class State(models.IntegerChoices):
        RUNNING = 0
        SUCCESS = 1
        FAILED = 2

    def generate_file_name(group: BMGTGroup, user: BMGTUser, case: BMGTCase) -> str:
        """
        name of the detailed case record which is stored on the server, does not contain directory info
        """
        return f"{group.id}_{user.id}_{case.id}_{random.randint(0,99999):06d}.xlsx"

    group = models.ForeignKey(
        BMGTGroup, on_delete=models.SET_NULL, null=True,)
    user = models.ForeignKey(
        BMGTUser, on_delete=models.SET_NULL, null=True,)
    case = models.ForeignKey(
        BMGTCase, on_delete=models.SET_NULL, null=True,)
    score = models.FloatField(null=True, default=None)
    state = models.IntegerField(
        State.choices, default=State.RUNNING, null=False)
    summary_dict = models.TextField(null=False, default="")
    file_name = models.CharField(max_length=30, null=False, auto_created=False, editable=False, unique=True)

    @property
    def file_url(self) -> str:
        return f"{settings.STATIC_URL}bmgt435/case_record/{self.file_name}"


    def as_dictionary(self) -> dict:

        return dict(
                id=self.id,
                create_time=self.formatted_create_time,
                group_id=self.group.id if self.group else None,
                user_id=self.user.id if self.user else None,
                user_name=self.user.name if self.user else 'Unknown user',
                group_name=self.group.name if self.group else 'Unknown group',
                case_id=self.case.id if self.case else None,
                case_name=self.case.name if self.case else 'Unknown case',
                state=self.State.choices[self.state][1],
                score=self.score,
                file = self.file_name,
        )



class CaseConfig(BMGTModelBase):

    # query_editable_fields = ["case_id", "config_json", ]

    case = models.ForeignKey(
        BMGTCase, on_delete=models.CASCADE, null=False,)
    config_json = models.TextField(null=False, default='')

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time=self.formatted_create_time,
            case_id=self.case.id,
            case_name=self.case.name,
            config_json=self.config_json,
        )