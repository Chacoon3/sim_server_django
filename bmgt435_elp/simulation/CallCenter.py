import io
import numpy as np
import pandas as pd
import scipy.stats
from .Core import SimulationException, SimulationResult, BaseDiscreteEventCase, BaseDESEvent


class Customer:
    __id = -1
    __priorityCumDist = [0.03, 0.06, 0.57, 0.98, 1.  ]

    @staticmethod
    def determinePriority() -> int:
        prob = np.random.random()
        for cumProb in Customer.__priorityCumDist:
            if prob <= cumProb:
                return cumProb

    def __init__(self, arrTime:float) -> None:
        Customer.__id += 1
        self.__id = Customer.__id
        self.__priority = Customer.determinePriority()
        self.__arrivalTime = arrTime

    @property
    def id(self):
        return self.__id
    
    @property
    def priority(self):
        return self.__priority
    
    @property
    def arrivalTime(self):
        return self.__arrivalTime
    

class CallCenterCase(BaseDiscreteEventCase):
    def __init__(self) -> None:
        super().__init__()
        self.__customers = list[Customer]()

    def addCustomer(self, customer: Customer):
        self.__customers.append(customer)


class ArrivalEvent(BaseDESEvent):
    def __init__(self, time: float) -> None:
        super().__init__(time)
    
    def execute(self, system: CallCenterCase):
        super().execute(system)

        # next arrival logic
        deltaTime = np.random.exponential(1/5)  # this should be replaced later by the true distribution of service time
        nextArrTime = system.systemTime + deltaTime
        nextArrEvent = ArrivalEvent(nextArrTime)
        system.addEvent(nextArrEvent)

        # current customer logic
        customer = Customer(system.systemTime)
        system.addCustomer(customer)


    def __str__(self) -> str:
        return f"ArrivalEvent(time={self.time}"