from django.db.models import QuerySet
from bmgt435_platform.simulation.Cases import SimulationResult
from ..bmgtModels import DbModelBase

import numpy as np
import json
import datetime



class CustomJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.astimezone().isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
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


def serialize_simulation_result(result: SimulationResult) -> str:
    return json.dumps(result.iteration_dataframe, cls=CustomJSONEncoder)