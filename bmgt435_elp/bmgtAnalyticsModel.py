from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
import bmgt435_elp.bmgtModels as bmgtModels
from .apps import BmgtPlatformConfig


class AnalyticsModelBase(models.Model):
    class Meta:
        abstract = True
        app_label = BmgtPlatformConfig.name

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
    

class UserActivity(AnalyticsModelBase):
    
    USER_ACT= [
        ('sign-in', 'sign-in'),
        ('sign-up', 'sign-up'),
        ('sign-out', 'sign-out'),
        ('forget-password', 'forget-password'),
        ('submit-case', 'submit-case'),
    ]

    user = models.ForeignKey(bmgtModels.BMGTUser, on_delete=models.SET_NULL, null=True)
    activity = models.CharField(choices=USER_ACT, max_length=20, null=False)


class BMGTFeedback(AnalyticsModelBase):

    id = models.AutoField(auto_created=True, primary_key=True, null=False)
    user = models.ForeignKey(bmgtModels.BMGTUser, on_delete=models.SET_NULL, null=True,)
    content = models.TextField(null=False, default='')

    def as_dictionary(self) -> dict:
        return dict(
            id=self.id,
            create_time=self.formatted_create_time,
            user_id=self.user.id,
            user_name=self.user.name,
            content=self.content,
        )