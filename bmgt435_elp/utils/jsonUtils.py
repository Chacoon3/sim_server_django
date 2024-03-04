import django.db.models as models
from bmgt435_elp.simulation.Core import SimulationResult
from ..bmgtModels import BMGTModelBase, BMGTJsonField
from typing import Union

import numpy as np
import json
import datetime


class CustomJSONEncoder(json.JSONEncoder):

    typeMapper = {
        datetime.datetime: lambda obj: obj.astimezone().isoformat(),
        np.integer: lambda obj: int(obj),
        np.floating: lambda obj: float(obj),
        models.QuerySet: lambda obj: [model.as_dictionary() for model in obj],
        list[BMGTModelBase]: lambda obj: [model.as_dictionary() for model in obj],
        BMGTModelBase: lambda obj: obj.as_dictionary(),
        # SimulationResult: lambda obj: obj.iteration_dataframe,
        BMGTJsonField: lambda obj : json.loads(obj),  # for json encoded data, first decode it to dict, then encode it again
    }

    def default(self, obj):
        objType = type(obj)
        if issubclass(objType, BMGTModelBase):
            return self.typeMapper[BMGTModelBase](obj)
        if self.typeMapper.get(objType, False):
            return self.typeMapper[objType](obj)
        return super().default(obj)


def serialize_models(querySet:  Union[models.QuerySet, list[BMGTModelBase]]) -> str:
    return json.dumps([model.as_dictionary() for model in querySet], cls=CustomJSONEncoder)

def serialize_model_instance(instance:BMGTModelBase) -> str:
    return json.dumps(instance.as_dictionary(), cls=CustomJSONEncoder)

def serialize_simulation_result(result: SimulationResult) -> str:
    return json.dumps(result.iterationData, cls=CustomJSONEncoder)
