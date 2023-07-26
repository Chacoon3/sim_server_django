from django.db import models
from django.utils import timezone


"""
@: Database schema
"""


APP_LABEL = "bmgt435_platform"


class DbModelBase(models.Model):
    class Meta:
        abstract = True
        app_label = APP_LABEL


    batch_updatable_fields = []


    id = models.AutoField(auto_created=True, primary_key=True, null=False)
    create_time = models.DateTimeField(default=timezone.now, null=False)
    flag_deleted = models.IntegerField(default=0, null=False)


    def create_time_as_string(self) -> str:
        return self.create_time.astimezone().isoformat()
        

    def as_serializable(self) -> dict:
        raise NotImplementedError()


class Role(DbModelBase):

    batch_updatable_fields = ["name"]
    name=models.CharField(max_length=10, null=False, unique=True, default='')

    def as_serializable(self) -> dict:
        return dict(
            id=self.id,
            create_time = self.create_time_as_string(),
            name=self.name,
        )


class Tag(DbModelBase):

    batch_updatable_fields = ["name"]
    name=models.CharField(max_length=10, null=False, unique=True, default='')

    def as_serializable(self):
        return dict(
            id=self.id,
            create_time = self.create_time_as_string(),
            name=self.name,
        )



class BMGTGroup(DbModelBase):

    batch_updatable_fields = ["name"]
    name=models.CharField(max_length=30, null=False, unique=True, default='')

    def as_serializable(self) -> dict:
        return dict(
            id=self.id,
            create_time = self.create_time_as_string(),
            name=self.name,
        )



class BMGTUser(DbModelBase):

    batch_updatable_fields = ["user_first_name", "user_last_name", "role_id", "group_id", "user_activated"]

    did = models.CharField(max_length=100, auto_created=False, null=False, unique=True,)
    first_name = models.CharField(max_length = 60, null=False)
    last_name = models.CharField(max_length = 60, null=False)
    password = models.CharField(max_length = 100,  null=False, default="")  # stores the password hash
    activated = models.IntegerField(default=0, null=False)

    role_id = models.ForeignKey(Role, on_delete=models.CASCADE, null=True)
    group_id = models.ForeignKey(BMGTGroup, on_delete=models.CASCADE, null=True)

    def full_name(self):
        name = ''
        if self.first_name and self.last_name:
            name = self.first_name + " " + self.last_name
        elif self.first_name:
            name = self.first_name
        elif self.last_name:
            name = self.last_name
        return name

    def as_serializable(self) -> dict:
        return dict(
            id=self.id,
            create_time = self.create_time_as_string(),
            user_did=self.did,
            user_first_name=self.first_name,
            user_last_name=self.last_name,
            role_id=self.role_id,
            group_id=self.group_id,
        )


class Tagged(DbModelBase):

    batch_updatable_fields = ["tag_id", "user_id"]

    tag_id = models.ForeignKey(Tag, on_delete=models.CASCADE)
    user_id = models.ForeignKey(BMGTUser, on_delete=models.CASCADE)

    def as_serializable(self) -> dict:
        return dict(
            id=self.id,
            create_time = self.create_time_as_string(),
            tag_id=self.tag_id,
            user_id=self.user_id,
        )


class Case(DbModelBase):

    batch_updatable_fields = ["name", "case_description"]

    name = models.CharField(max_length=50, null=False, default='')
    description = models.TextField(null=False)

    def as_serializable(self) -> dict:
        return dict(
            id=self.id,
            create_time = self.create_time_as_string(),
            name=self.name,
            case_description=self.description,
        )


class CaseRecord(DbModelBase):

    batch_updatable_fields = ["group_id", "case_id", "case_record_score", "case_record_detail_json"]

    group_id = models.ForeignKey(BMGTGroup, on_delete=models.CASCADE)
    case_id = models.ForeignKey(Case, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0, null=False)
    detail_json = models.TextField(null=False, default='')

    def as_serializable(self) -> dict:
        return dict(
            id=self.id,
            create_time = self.create_time_as_string(),
            group_id=self.group_id,
            case_id=self.case_id,
            case_record_score=self.score,
            case_record_detail_json=self.detail_json,
        )