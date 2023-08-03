from django.db.models import QuerySet
from ..bmgtModels import DbModelBase
import numpy as np
import json
import datetime


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is datetime.datetime:
            return obj.isoformat()
        if obj is np.integer:
            return int(obj)
        if obj is np.floating:
            return float(obj)
        return super().default(obj)

def serialize_models(querySet:QuerySet | list[DbModelBase]) -> str:
    return json.dumps([model.as_dictionary() for model in querySet],)


def serialize_model_instance(instance:DbModelBase) -> str:
    return json.dumps(instance.as_dictionary())

def serialize_simulations(result) -> str:
    raise NotImplementedError