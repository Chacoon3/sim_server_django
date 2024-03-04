"""
This module defines the framework-level objects and interfaces for running simulation
"""

from io import BytesIO
from dataclasses import dataclass, field
from typing import Any, Union

class SimulationHelper:
    """
    helper class
    """

    @staticmethod
    def minGreaterThan(arr:list[Union[float,int]], than: Union[float,int]) -> Union[float,int]:
        """
        returns the minimum value in the array that is greater than the specified value
        """
        minVal = float("inf")
        for v in arr:
            if v > than and v < minVal:
                minVal = v
        return minVal
    
    @staticmethod
    def maxLessThan(arr:list[Union[float,int]], than: Union[float,int]) -> Union[float,int]:
        """
        returns the maximum value in the array that is less than the specified value
        """
        maxVal = float("-inf")
        for v in arr:
            if v < than and v > maxVal:
                maxVal = v
        return maxVal
    


@dataclass(order=True)
class _PrioritizedItem:
    priority: float
    item: Any=field(compare=False)


class AppPriorityQueue(object):
    """
    single-threaded priority queue
    """

    def __init__(self) -> None:
        self.__list = list[_PrioritizedItem]()
        self._count = 0
        self.__cursor = 0

    def enqueue(self, priority:float, item):
        priorityItem = _PrioritizedItem(priority, item)
        self.__list.append(None)
        self.__siftup(priorityItem, len(self.__list)-1)
        self._count += 1

    def __siftup(self, priorityItem:_PrioritizedItem, last:int):
        elements, i, j = self.__list, last, (last-1) // 2
        while i > 0 and priorityItem.priority < elements[j].priority:
            elements[i] = elements[j]
            i, j = j, (j-1) // 2
        elements[i] = priorityItem

    def dequeue(self) -> object:
        if self._count == 0:
            raise Exception("Queue is empty!")
        items = self.__list
        item = items[0]
        last = items.pop()
        if len(items) > 0:
            self.__siftdown(last, 0, len(items))
        self._count -= 1
        return item.item
    
    def __siftdown(self, priorityItem:_PrioritizedItem, start:int, end:int):
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
        return self._count == 0
    
    def clear(self):
        self.__list.clear()
        self._count = 0

    def __len__(self):
        return self._count


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


class SimulationCase(object):
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

    def simulate(self):
        '''
        the logic of one iteration in this simulation case.\n
        returns an object storing the result of the iteration
        '''
        raise NotImplementedError()

    def run(self, num_iterations:int=100) -> SimulationResult:
        '''
        run the simulation case with specified number of iterations
        '''
        raise NotImplementedError()


class DiscreteEventCase(SimulationCase):
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
      
    def _setSystemTime(self, time:float):
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
    
    def reset(self):
        """
        reset the state of the system so that next iteration can start
        """
        raise NotImplementedError()
    

class ResourceQueue(AppPriorityQueue):
    """
    priority queue for system recourse
    """

    def __init__(self, system: DiscreteEventCase) -> None:
        super().__init__()
        self.__system:DiscreteEventCase = system
        self.__queueLength = dict[float, int]() # key: time, value: queue length
        self.__queueLength[0] = 0   # initial queue length
        self.__maxQueueLength = 0

    def enqueue(self, priority:int, item: object):
        super().enqueue(priority, item)
        time = self.__system.systemTime
        self.__queueLength[time]  = self._count
        if self._count > self.__maxQueueLength:
            self.__maxQueueLength = self._count
    
    def dequeue(self) -> object:
        item = super().dequeue()
        time = self.__system.systemTime
        self.__queueLength[time]  = self._count
        return item
        
    @property
    def queueLengthRecord(self) -> dict[float, int]:
        """
        a dictionary recording the queue length over time.\n
        key: time, value: queue length
        """
        return self.__queueLength
    
    @property
    def maxQueueLength(self) -> int:
        return self.__maxQueueLength
    
    def avgQueueLengthOverTime(self, start:float, end:float) -> float:
        """
        calculate the average queue length over time
        """
        
        if start < 0 or end < 0 or start > end:
            raise SimulationException("Invalid time range!")
        
        timeLength = end - start
        total = 0

        if start > 0:
            timeStart = SimulationHelper.maxLessThan(list(self.__queueLength.keys()), start)
            total += self.__queueLength[timeStart] * (start - timeStart)

        if end < max(self.__queueLength.keys()):
            keyEnd = SimulationHelper.minGreaterThan(list(self.__queueLength.keys()), end)
            total += self.__queueLength[keyEnd] * (keyEnd - end)
            
        prevTime = start
        sortedKeys = sorted(self.__queueLength.keys())
        for time in sortedKeys:
            if time == prevTime:
                continue
            if time > end:
                break   
            length = self.__queueLength[time]
            total += length * (time - prevTime)
            prevTime = time 
        return total/timeLength

    
    def clear(self):
        super().clear()
        self.__queueLength.clear()
        self.__queueLength[0] = 0
    

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