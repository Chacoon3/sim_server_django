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


class BMGTModelBase(models.Model):
    class Meta:
        abstract = True
        app_label = APP_LABEL


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
        return timezone.make_naive(self.create_time).isoformat(sep=' ', timespec='seconds')
    

class BMGTJsonField(models.TextField):
    """
    Subclassed to flag data stored in JSON format
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BMGTSemester(BMGTModelBase):

    class Meta:
        app_label = APP_LABEL
        constraints = [
            models.UniqueConstraint(fields=('year', 'season'), name='unique_semester'),
            models.CheckConstraint(check=models.Q(year__gte=2022), name='year_constraint'),
            models.CheckConstraint(check=models.Q(season__in=["spring", "summer", "fall"]), name='season_constraint'),
        ]

    year = models.IntegerField(null=False, unique=False,)
    season = models.CharField(max_length=10, null=False, unique=False, choices=[
        ("spring", "spring"), ("summer", "summer"), ("fall", "fall"),
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

    is_frozen = models.BooleanField(default=False, null=False)  # if true, no user can join this group
    number = models.IntegerField(null=False, unique=False)  # group number
    semester = models.ForeignKey(BMGTSemester, on_delete=models.RESTRICT, null=False)

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
            "is_frozen": self.is_frozen,
            "users": [user.as_dictionary() for user in self.users],
            "semester_id": self.semester.id if self.semester else None,
            "semester_name": self.semester.name if self.semester else None,
        }


class BMGTUser(BMGTModelBase):

    class BMGTUserRole(models.TextChoices):
        ADMIN = 'admin'
        USER = 'user'

    did = models.CharField(max_length=60, auto_created=False, null=False, unique=True, db_index=True)
    first_name = models.CharField(max_length=60, null=False)
    last_name = models.CharField(max_length=60, null=False)
    password = models.CharField(max_length=100,  null=False, default="")    # stores the password hash
    activated = models.BooleanField(default=False,  null=False)
    role = models.CharField(choices=BMGTUserRole.choices, default=BMGTUserRole.USER, null=False, max_length=5)
    group = models.ForeignKey(BMGTGroup, on_delete=models.SET_NULL, null=True)
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
            activated = self.activated,
            first_name=self.first_name,
            last_name=self.last_name,
            role=self.role,
            group_id=self.group.id if self.group else None,
            group_name=self.group.name if self.group else None,
            semester_id=self.semester.id if self.semester else None,
            semester_name = self.semester.name if self.semester else None,
        )
    

class BMGTCase(BMGTModelBase):

    # this pk has to be manually set because app logic depends on it
    id = models.IntegerField(auto_created=False, primary_key=True, null=False)
    name = models.CharField(max_length=50, null=False, default='')
    visible = models.BooleanField(default=True, null=False)
    max_submission = models.IntegerField(default=5, null=False, unique=False)

    def as_dictionary(self,) -> dict:
        return dict(
            id=self.id,
            create_time=self.formatted_create_time,
            name=self.name,
        )
    

class BMGTCaseConfig(BMGTModelBase):

    class Meta:
        app_label = APP_LABEL
        constraints = [
            models.UniqueConstraint(fields=('case_id', 'semester_id'), name='unique_case_config'),
        ]
    
    case = models.ForeignKey(BMGTCase, on_delete=models.CASCADE, null=False)
    semester = models.ForeignKey(BMGTSemester, on_delete=models.CASCADE, null=False)
    config_json = BMGTJsonField(null=False, default="", unique=False)  # editable configuration regarding a case
    edited_time = models.DateTimeField(auto_created=True, default=timezone.now, null=False)

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time=self.formatted_create_time,
            edited_time=timezone.make_naive(self.edited_time).isoformat(sep=' ', timespec='seconds'),
            case_id=self.case.id if self.case else None,
            case_name=self.case.name if self.case else None,
            semester_id=self.semester.id if self.semester else None,
            semester_name=self.semester.name if self.semester else None,
            config_json=self.config_json,
        )


class BMGTCaseRecord(BMGTModelBase):

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


class BMGTTransaction(BMGTModelBase):

    DEVICE_MAX_LENGTH = 20
    IP_MAX_LENGTH = 20
    
    METHOD= [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
    ]

    user = models.ForeignKey(BMGTUser, on_delete=models.SET_NULL, null=True)
    method = models.CharField(choices=METHOD, max_length=10, null=False, default='UNKNOWN')
    path = models.CharField(max_length=100, null=False, default='')
    status_code = models.IntegerField(null=False, default=0)
    ip = models.CharField(max_length=IP_MAX_LENGTH, null=False, default='')
    device = models.CharField(max_length=DEVICE_MAX_LENGTH, null=False, default='')

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time=self.formatted_create_time,
            user_id=self.user.id,
            user_name=self.user.name,
            method=self.method,
            path=self.path,
            status_code=self.status_code,
            ip=self.ip,
            device=self.device,
        )


class BMGTFeedback(BMGTModelBase):

    id = models.AutoField(auto_created=True, primary_key=True, null=False)
    user = models.ForeignKey(BMGTUser, on_delete=models.SET_NULL, null=True,)
    content = models.TextField(null=False, default='')

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time=self.formatted_create_time,
            user_id=self.user.id,
            user_name=self.user.name,
            content=self.content,
        )
    

class BMGTSystemStatus(BMGTModelBase):

    allow_join_group = models.BooleanField(default=True, null=False)
    allow_user_login = models.BooleanField(default=True, null=False)
    allow_case_submit = models.BooleanField(default=True, null=False)