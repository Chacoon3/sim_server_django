from django.db.models import QuerySet
from ..bmgtModels import DbModelBase
import numpy as np
import json
import datetime


class GlobalJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) is datetime.datetime:
            return obj.astimezone().isoformat()
        elif type(obj) is np.integer:
            return int(obj)
        elif type(obj) is np.floating:
            return float(obj)
        else:
            return super().default(obj)

def serialize_models(querySet:QuerySet | list[DbModelBase]) -> str:
    return json.dumps([model.as_dictionary() for model in querySet], cls=GlobalJSONEncoder)


def serialize_model_instance(instance:DbModelBase) -> str:
    return json.dumps(instance.as_dictionary(), cls=GlobalJSONEncoder)

def serialize_simulations(result) -> str:
    raise NotImplementedError