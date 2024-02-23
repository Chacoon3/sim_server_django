"""
This module defines the framework-level objects and interfaces for running simulation
"""

from io import BytesIO
from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class PrioritizedItem:
    priority: float
    item: Any=field(compare=False)


class AppPriorityQueue(object):
    """
    decorator pattern to encapsulate the priority queue
    simplifies the interface of the priority queue
    """

    def __init__(self) -> None:
        self.__list = list[PrioritizedItem]()
        self.__counter = 0

    def add(self, priority:float, item):
        priorityItem = PrioritizedItem(priority, item)
        self.__list.append(None)
        self.__siftup(priorityItem, len(self.__list)-1)
        self.__counter += 1

    def __siftup(self, priorityItem:PrioritizedItem, last:int):
        elements, i, j = self.__list, last, (last-1) // 2
        while i > 0 and priorityItem.priority < elements[j].priority:
            elements[i] = elements[j]
            i, j = j, (j-1) // 2
        elements[i] = priorityItem

    def get(self) -> object:
        if self.__counter == 0:
            raise Exception("Queue is empty!")
        items = self.__list
        item = items[0]
        last = items.pop()
        if len(items) > 0:
            self.__siftdown(last, 0, len(items))
        self.__counter -= 1
        return item.item
    
    def __siftdown(self, priorityItem:PrioritizedItem, start:int, end:int):
        elements, i, j = self.__list, start, start*2+1
        while j < end:
            if j+1 < end and elements[j+1].priority < elements[j].priority:
                j += 1
            if priorityItem.priority < elements[j].priority:
                break
            elements[i] = elements[j]
            i, j = j, j*2+1
        elements[i] = priorityItem
    
    def empty(self) -> bool:
        return self.__counter == 0
    
    def clear(self):
        self.__list.clear()
        self.__counter = 0

    def __len__(self):
        return self.__counter


class SimulationException(Exception):
    """
    base class of all exceptions raised in the simulation framework
    """
    
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class SimulationResult(object):
    """
    abstraction of simulation result"
    """

    def __init__(self, score: float, summaryData, iterationData) -> None:
        """
        score is the single metric used to evaluate a simulation strategy
        per_iteration_data is a list of data collected in each iteration
        """
        self.__score = score
        self.__summary = summaryData
        self.__iterationData = iterationData

    @property
    def score(self):
        return self.__score

    @property
    def summaryData(self) -> object:
        return self.__summary

    @property
    def iterationData(self) -> object:
        return self.__iterationData
    
    def asFileStream(self) -> BytesIO:
        """
        returns a file stream that contains detailed simulation result
        """
        raise NotImplementedError()

    def asDict(self) -> dict:
        """
        returns a dictionary that provides summary of the simulation result
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
        self._eventQueue = AppPriorityQueue()
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
    
    def addEvent(self, event) -> bool:
        raise NotImplementedError()
    

class BaseDESEvent:
    """
    base class for all discrete event simulation events
    """

    def __init__(self, time:float) -> None:
        if time < 0:
            raise SimulationException("Invalid time. Time cannot be negative!")
        self._time = time

    @property
    def time(self):
        """
        the time when the event is scheduled to be executed
        """
        return self._time

    def execute(self):
        raise NotImplementedError()