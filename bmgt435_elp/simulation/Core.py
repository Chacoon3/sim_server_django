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

    def score(self, iterationStats) -> float:
        """
        returns the score of the simulation
        """
        raise NotImplementedError()

    def simulate(self) -> object:
        '''
        the logic of one iteration in this simulation case.\n
        returns an object storing the result of the iteration
        '''
        raise NotImplementedError()

    def run(self, num_iterations=100) -> SimulationResult:
        '''
        run the simulation case with specified number of iterations
        '''
        raise NotImplementedError()


class BaseDiscreteEventSimulator(CaseBase):
    """
    abstraction of the state of the system being simulated
    """

    def __init__(self) -> None:
        self._time = 0
        self._eventQueue = pQueue()
        return
  
    @property
    def systemTime(self) -> float:
        return self._time
      
    @systemTime.setter
    def systemTime(self, time:float):
        if time < 0:
            raise SimulationException("Invalid time. Time cannot be negative!")
        if time < self._time:
            raise SimulationException(f"Invalid time. Time cannot be decreased! Current time: {self._time}, new time: {time}")
        self._time = time
    
    def shouldStop(self) -> bool:
        """
        determine if the DES simulator should stop
        """
        raise NotImplementedError()
    
    def tryAddEvent(self, event) -> bool:
        raise NotImplementedError()
    

class BaseDESEvent:
    """
    base class for all discrete event simulation events
    """

    def __init__(self, time:float, system: BaseDiscreteEventSimulator) -> None:
        if time < 0:
            raise SimulationException("Invalid time. Time cannot be negative!")
        self.__time = time
        self.__system = system

    @property
    def time(self):
        return self.__time
    
    @property
    def system(self):
        return self.__system

    def execute(self, system:BaseDiscreteEventSimulator):
        raise NotImplementedError()