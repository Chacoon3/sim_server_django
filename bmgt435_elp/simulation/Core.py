"""
This module defines the framework-level objects and interfaces for running simulation
"""


import pandas as pd
from queue import PriorityQueue as pQueue
from io import BytesIO


class SimulationException(Exception):
    """
    base class of all exceptions in this simulation platform
    """
    pass


class SimulationResult(object):
    """
    abstraction of simulation result"
    """
    def __init__(self, score: float, aggregated_data: pd.DataFrame = None, iteration_data = None) -> None:
        """
        score is the single metric used to evaluate a simulation strategy
        per_iteration_data is a list of data collected in each iteration
        """
        self.__score = score
        self.__aggregation_dataframe = aggregated_data
        self.__iteration_dataframe = iteration_data

    @property
    def score(self):
        return self.__score

    @property
    def aggregation_dataframe(self) -> pd.DataFrame:
        return self.__aggregation_dataframe

    @property
    def iteration_dataframe(self):
        return self.__iteration_dataframe
    
    def detail_as_bytes(self) -> BytesIO:
        """
        returns the simulation result as an IO bytes for server-side persistence
        """

        raise NotImplementedError()

    def summary_as_dict(self) -> str:
        """
        returns the simulation result as a json string
        """
        raise NotImplementedError()


class CaseBase(object):
    """
    Base class of all the simulation cases
    """

    _msg_assert_err_ = "Invalid case setting. Simulation cannot execute!"

    def __init__(self,) -> None:
        return

    def _assert_params(self) -> None:
        """
        should be called in the initiator of all subclasses
        """
        raise NotImplementedError()

    def score(self, obj) -> float:
        """
        returns the score of the simulation
        """
        raise NotImplementedError()

    def simulate(self, ):
        '''
        the logic of one iteration in this simulation case
        '''
        raise NotImplementedError()

    def run(self, num_iterations=100) -> SimulationResult:
        '''
        run the simulation case with specified number of iterations
        '''
        raise NotImplementedError()
    
    def meta_data(self):
        """
        should return a dictionary object describing the parameters of the case
        """
        raise NotImplementedError()


class BaseDiscreteEventCase(CaseBase):
    """
    abstraction of the state of the system being simulated
    """

    def __init__(self) -> None:
        self.__time = 0
        self.__eventQueue = pQueue()
        return
    
    @property.setter
    def systemTime(self, time:float):
        if time < 0:
            raise SimulationException("Invalid time. Time cannot be negative!")
        if time < self.__time:
            raise SimulationException(f"Invalid time. Time cannot be decreased! Current time: {self.__time}, new time: {time}")
        self.__time = time
    
    @property
    def systemTime(self):
        return self.__time
    
    def shouldStop(self) -> bool:
        raise NotImplementedError()
    
    def run(self):
        while not (self.shouldStop() or self.__eventQueue.empty()):
            event = self.__eventQueue.get()
            self.systemTime = event.time
            event.execute(self)
        return
    
    def addEvent(self, event):
        if event.time < self.__time:
            raise SimulationException(f"Invalid event time. Event time cannot be earlier than current time! Current time: {self.__time}, event time: {event.time}")
        self.__eventQueue.put(event)
        return


class BaseDESEvent:
    """
    base class for all discrete event simulation events
    """

    def __init__(self, time:float) -> None:
        if time < 0:
            raise SimulationException("Invalid time. Time cannot be negative!")
        self.__time = time

    @property
    def time(self):
        return self.__time

    def execute(self, systemState:BaseDiscreteEventCase):
        if systemState is None:
            raise SimulationException("Invalid system state. System state cannot be None!")