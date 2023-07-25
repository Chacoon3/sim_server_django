from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.query import QuerySet 
from django.core.serializers import serialize as django_serialize
import numpy as np


class __CustomEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)



def serialize(querySet:QuerySet):
    return django_serialize('json', querySet, cls=__CustomEncoder)