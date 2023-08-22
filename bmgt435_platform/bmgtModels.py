from django.db import models
from django.db.models import QuerySet
from django.utils import timezone


"""
@: Database schema
@: Field Naming Convention: snake_case without class name prefix
"""


APP_LABEL = "bmgt435_platform"


class BinaryIntegerFlag(models.IntegerChoices):
    FALSE = 0
    TRUE = 1


class DbModelBase(models.Model):
    class Meta:
        abstract = True
        app_label = APP_LABEL

    query_editable_fields = []

    id = models.AutoField(auto_created=True, primary_key=True, null=False)
    create_time = models.DateTimeField(
        auto_created=True, default=timezone.now, null=False)

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

    def set_fields(self, save=False, **kwargs):
        for field in kwargs.keys():
            if field in self.query_editable_fields:
                setattr(self, field, kwargs[field])
        if save:
            self.save()

    def validate(self):
        raise NotImplementedError()


class BMGTTag(DbModelBase):

    query_editable_fields = ['name', ]
    name = models.CharField(max_length=10, null=False, unique=True, default='')

    def as_dictionary(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
        }


class BMGTGroup(DbModelBase):

    @property
    def users(self) -> QuerySet:
        return BMGTUser.objects.filter(group_id=self.id)

    @property
    def name(self):
        return f"Group {self.id}"

    def as_dictionary(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "users": [user.as_dictionary() for user in self.users]
        }


class BMGTUser(DbModelBase):

    class BMGTUserRole(models.TextChoices):
        ADMIN = 'admin'
        USER = 'user'

    query_editable_fields = ["first_name",
                             "last_name", "role", "group_id", "activated", ]

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
    group_id = models.ForeignKey(
        BMGTGroup, on_delete=models.SET_NULL, null=True)

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
            group_id=self.group_id.id if self.group_id else None,
            group_name=self.group_id.name if self.group_id else None,
        )


class BMGTTagged(DbModelBase):

    query_editable_fields = ["tag_id", "user_id", ]

    tag_id = models.ForeignKey(BMGTTag, on_delete=models.CASCADE)
    user_id = models.ForeignKey(BMGTUser, on_delete=models.CASCADE)

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time=self.formatted_create_time,
            tag_id=self.tag_id.id,
            user_id=self.user_id.id,
        )


class BMGTCase(DbModelBase):

    query_editable_fields = ["name", "description", ]

    name = models.CharField(max_length=50, null=False, default='')
    visible = models.IntegerField(
        BinaryIntegerFlag.choices, default=BinaryIntegerFlag.TRUE, null=False)
    # how many times a user can submit for this case
    max_submission = models.IntegerField(default=5, null=False, unique=False)

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time=self.formatted_create_time,
            name=self.name,
        )


class BMGTCaseRecord(DbModelBase):

    query_editable_fields = ["group_id", "case_id", "score", ]

    class State(models.IntegerChoices):
        RUNNING = 0
        SUCCESS = 1
        FAILED = 2

    group_id = models.ForeignKey(
        BMGTGroup, on_delete=models.SET_NULL, null=True,)
    user_id = models.ForeignKey(
        BMGTUser, on_delete=models.SET_NULL, null=True,)
    case_id = models.ForeignKey(
        BMGTCase, on_delete=models.SET_NULL, null=True,)
    score = models.FloatField(null=True, default=None)
    state = models.IntegerField(
        State.choices, default=State.RUNNING, null=False)
    summary_dict = models.TextField(null=False, default="")

    @property
    def case_record_file_name(self) -> str:
        """
        name of the detailed case record which is stored on the server, does not contain directory info
        """
        return f"{self.case_id.name}_{self.group_id.name}_record_index_{self.id}.xlsx"

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time=self.formatted_create_time,
            group_id=self.group_id.id,
            user_id=self.user_id.id,
            user_name=self.user_id.name,
            group_name=self.group_id.name,
            case_id=self.case_id.id,
            case_name=self.case_id.name,
            state=self.State.choices[self.state][1],
            score=self.score,
        )


class CaseConfig(DbModelBase):

    query_editable_fields = ["case_id", "config_json", ]

    case_id = models.ForeignKey(
        BMGTCase, on_delete=models.CASCADE, null=False,)
    config_json = models.TextField(null=False, default='')

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time=self.formatted_create_time,
            case_id=self.case_id.id,
            case_name=self.case_id.name,
            config_json=self.config_json,
        )


class BMGTFeedback(DbModelBase):


    id = models.AutoField(auto_created=True, primary_key=True, null=False)
    user_id = models.ForeignKey(BMGTUser, on_delete=models.SET_NULL, null=True,)
    content = models.TextField(null=False, default='')

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time=self.formatted_create_time,
            user_id=self.user_id.id,
            user_name=self.user_id.name,
            content=self.content,
        )