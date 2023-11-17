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

    @staticmethod
    def score(obj) -> float:
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
        ouutput_style should decide whether detailed or simplified simulation statistics should be returned
        '''
        raise NotImplementedError()
    
    def meta_data(self):
        """
        should return a dictionary object describing the parameters of the case
        """
        raise NotImplementedError()


class CaseDES(CaseBase):
    """
    base class of all descrete event simulation cases
    """

    def __init__(self,  stopCondition) -> None:
        self.__pQueue = pQueue()  # event queue
        self.__t = 0    # timer
        self.__shouldStop = stopCondition

    def run(self, ):
        while not (self.__shouldStop() or self.__pQueue.empty()):
            event = self.__pQueue.get()
            self.__t = event.time()
            if self.__shouldStop():     # check stop condition after updating system time
                break
            else:
                event.execute()

    def addEvent(self, event) -> None:
        self.__pQueue.put((event.time, event))

    def getTime(self) -> float:
        return self.__t
