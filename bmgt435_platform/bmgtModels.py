from django.db import models
from django.utils import timezone


"""
@: Database schema
@: Field Naming Convention: snake_case without class name prefix
"""


APP_LABEL = "bmgt435_platform"



class DbModelBase(models.Model):
    class Meta:
        abstract = True
        app_label = APP_LABEL


    query_editable_fields = ["flag_deleted",]


    id = models.AutoField(auto_created=True, primary_key=True, null=False)
    create_time = models.DateTimeField(default=timezone.now, null=False)
    flag_deleted = models.IntegerField(default=0, null=False)
        

    def as_dictionary(self) -> dict:
        """
        global interface for json serialization
        should be implemented by all subclasses
        the dictionary should be json serializable
        """
        raise NotImplementedError("as dictionary method not implemented")

    @property
    def formatted_create_time(self):
        return self.create_time.astimezone().isoformat()

    def set_fields(self, save = False, **kwargs):
        for field in kwargs.keys():
            if field in self.query_editable_fields:
                setattr(self, field, kwargs[field])
        if save:
            self.save()


    def validate(self):
        raise NotImplementedError()


class Role(DbModelBase):

    query_editable_fields = ['name', "flag_deleted"]
    name=models.CharField(max_length=10, null=False, unique=True, default='')

    def as_dictionary(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
        }


class Tag(DbModelBase):

    query_editable_fields = ['name', "flag_deleted"]
    name=models.CharField(max_length=10, null=False, unique=True, default='')

    def as_dictionary(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
        }


class BMGTGroup(DbModelBase):

    query_editable_fields = ['name', "flag_deleted"]
    name=models.CharField(max_length=30, null=False, unique=True, default='')

    @property
    def users(self):
        return BMGTUser.objects.filter(group_id=self.id)


    def as_dictionary(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "users": [user.as_dictionary() for user in self.users]
        }

class BMGTUser(DbModelBase):


    query_editable_fields = ["first_name", "last_name", "role_id", "group_id", "activated", "flag_deleted"]

    did = models.CharField(max_length=100, auto_created=False, null=False, unique=True,)
    first_name = models.CharField(max_length = 60, null=False)
    last_name = models.CharField(max_length = 60, null=False)
    password = models.CharField(max_length = 100,  null=False, default="")  # stores the password hash
    activated = models.BooleanField(default=False, null=False, unique=False)
    role_id = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True,)
    group_id = models.ForeignKey(BMGTGroup, on_delete=models.SET_NULL, null=True)

    def full_name(self):
        name = ''
        if self.first_name and self.last_name:
            name = self.first_name + " " + self.last_name
        elif self.first_name:
            name = self.first_name
        elif self.last_name:
            name = self.last_name
        return name

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time = self.formatted_create_time,
            did=self.did,
            first_name=self.first_name,
            last_name=self.last_name,
            role_id=self.role_id.id if self.role_id else None,
            group_id=self.group_id.id if self.group_id else None,
        )


class Tagged(DbModelBase):

    query_editable_fields = ["tag_id", "user_id", "flag_deleted"]

    tag_id = models.ForeignKey(Tag, on_delete=models.CASCADE)
    user_id = models.ForeignKey(BMGTUser, on_delete=models.CASCADE)

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time = self.formatted_create_time,
            tag_id=self.tag_id.id,
            user_id=self.user_id.id,
        )


class Case(DbModelBase):

    query_editable_fields = ["name", "description", "flag_deleted"]

    name = models.CharField(max_length=50, null=False, default='')
    description = models.TextField(null=False)

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time = self.formatted_create_time,
            name=self.name,
            description=self.description,
        )


class CaseRecord(DbModelBase):

    query_editable_fields = ["group_id", "case_id", "score", "detail_json", "flag_deleted"]

    group_id = models.ForeignKey(BMGTGroup, on_delete=models.SET_NULL, null=True,)
    case_id = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True,)
    score = models.FloatField(default=0.0, null=False)
    detail_json = models.TextField(null=False, default='')

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time = self.formatted_create_time,
            group_id=self.group_id.id,
            case_id=self.case_id.id,
            score=self.score,
            detail_json=self.detail_json,
        )
