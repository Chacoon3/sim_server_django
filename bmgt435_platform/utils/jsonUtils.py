from django.db.models import QuerySet
from ..bmgtModels import DbModelBase
import numpy as np
import json
import datetime



class CustomJSONEncoder(json.JSONEncoder):

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
    return json.dumps([model.as_dictionary() for model in querySet], cls=CustomJSONEncoder)


def serialize_model_instance(instance:DbModelBase) -> str:
    return json.dumps(instance.as_dictionary(), cls=CustomJSONEncoder)


def serialize_paginated_data(paginator, pageIndex: int) -> str:

    return json.dumps({
        "page": pageIndex,
        "totalPage": paginator.num_pages,
        "data": json.loads(serialize_models(paginator.page(pageIndex).object_list)),
    })


def serialize_simulations(result) -> str:
    raise NotImplementedError