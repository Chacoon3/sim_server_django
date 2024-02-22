import io
import numpy as np
import pandas as pd
from queue import PriorityQueue as pQueue
from .Core import SimulationException, SimulationResult, BaseDiscreteEventSimulator, BaseDESEvent    
from typing import Union


class Customer:
    __id = -1
    __priorityCumDist = [0.03, 0.06, 0.57, 0.98, 1.  ]

    @staticmethod
    def __determinePriority() -> int:
        prob = np.random.random()
        for cumProb in Customer.__priorityCumDist:
            if prob <= cumProb:
                return cumProb
            
    @staticmethod
    def __determineServiceType() -> int:
        return np.random.choice([1, 2, 3], p=[0.5, 0.3, 0.2])

    def __init__(self, arrTime:float) -> None:
        Customer.__id += 1
        self.__id = Customer.__id
        self.__priority = Customer.__determinePriority()
        self.__arrivalTime = arrTime
        self.__exitTime:float = None
        self.__enqueueTime:float = None
        self.__serviceStartTime:float = None
        self.__serviceType = Customer.__determineServiceType()

    @property
    def id(self) -> int:
        return self.__id
    
    @property
    def priority(self) -> int:
        return self.__priority
    
    @property
    def arrivalTime(self) -> float:
        return self.__arrivalTime
    
    @property
    def exitTime(self) -> float:
        return self.__exitTime

    @exitTime.setter
    def exitTime(self, value:float):
        if self.__exitTime is not None:
            raise SimulationException("Invalid exit time. Customer has already exited!")
        if value < self.__arrivalTime:
            raise SimulationException("Invalid exit time. Exit time cannot be less than arrival time!")
        self.__exitTime = value
    
    @property
    def enqueueTime(self) -> Union[float, None]:
        return self.__enqueueTime
    
    @enqueueTime.setter
    def enqueueTime(self, value:float):
        if self.__enqueueTime is not None:
            raise SimulationException("Invalid enqueue time. Customer has already enqueued!")
        if value < self.__arrivalTime:
            raise SimulationException("Invalid enqueue time. Enqueue time cannot be less than arrival time!")
        self.__enqueueTime = value

    @property
    def serviceStartTime(self) -> float:
        return self.__serviceStartTime
    
    @serviceStartTime.setter
    def serviceStartTime(self, value:float):
        if self.__serviceStartTime is not None:
            raise SimulationException("Invalid dequeue time. Customer has already dequeued!")
        if value < self.__enqueueTime:
            raise SimulationException("Invalid dequeue time. Dequeue time cannot be less than enqueue time!")
        self.__serviceStartTime = value

    @property
    def waitTime(self) -> Union[float, None]:
        if self.__enqueueTime is None or self.__serviceStartTime is None:
            return None
        return self.__serviceStartTime - self.__enqueueTime
    
    @property
    def serviceTime(self) -> float:
        if self.__exitTime is None:
            return None
        return self.__serviceStartTime - self.__arrivalTime
    
    @property
    def serviceType(self) -> int:
        return self.__serviceType


class AgentSchedule:

    def __init__(self, schedule:list[list[float]]) -> None:
        # validate
        prev = None
        for s in schedule:
            if len(s) != 2:
                raise SimulationException("Invalid schedule. Each schedule must have two elements!")
            if s[0] < 0 or s[1] < 0:
                raise SimulationException("Invalid schedule. Schedule cannot have negative values!")
            if s[0] > s[1]:
                raise SimulationException("Invalid schedule. Start time cannot be greater than end time!")
            if prev is not None and s[0] < prev:
                raise SimulationException("Invalid schedule. Start time cannot be less than the previous end time!")
            prev = s[1]

        self.__schedule = schedule

    @property
    def schedule(self) -> list[list[float]]:
        return self.__schedule
    

class Agent:
    __id = -1

    @staticmethod
    def generateServiceTime() -> float:
        return np.random.exponential(228.98) + 77.020

    def __init__(self, schedule:AgentSchedule, level:int) -> None:
        Agent.__id += 1
        self.__id = Agent.__id
        self.__level = level
        self.__schedule = schedule
        self.__isBusy = False

    @property
    def id(self):
        return self.__id
    
    @property
    def level(self):
        return self.__level
    
    @property
    def schedule(self):
        return self.__schedule
        
    def isAvailable(self, time:float) -> bool:
        for s in self.__schedule.schedule:
            if s[0] <= time <= s[1]:
                return True
        return False
    
    @property
    def isBusy(self):
        return self.__isBusy

    @isBusy.setter
    def isBusy(self, value:bool):
        self.__isBusy = value
    
    
class CallCenterResult(SimulationResult):
    pass


class CallCenterSimulator(BaseDiscreteEventSimulator):
    """
    systemTime: float, refers to the current time in the simulation, measured by seconds, starting at 0.
    """

    class IterationStats:
        def __init__(self) -> None:
            self.avgTimeInQueue: float = None
            self.avgServiceTime: float = None
            self.avgWaitTime: float = None


    # schedule is represented as a nested list. Each inner list represents a time interval.
    # an agent may work during multiple time intervals in a day
    __schedule1 = AgentSchedule([[0 * 3600, 4 * 3600]])  # 8am to 12pm
    __schedule2 = AgentSchedule([[3 * 3600, 7 * 3600]])  # 11am to 3pm
    __schedule3 = AgentSchedule([[5 * 3600, 9 * 3600]])  # 1pm to 5pmwe
    __arrivalRate = [
        27.34, 63.1, 54.7, 44.87, 68.7, 56.79, 16.83, 21.03, 31.55, 13.32, 21.03, 49.07, 52.58, 54.33, 60.29, 22.43, 15.42, 26.64
    ]

    @staticmethod
    def __validateInput(decision:list[int]):
        for d in decision:
            if d < 0:
                raise SimulationException("Invalid decision. Decision cannot be negative!")
            if d > 5:
                raise SimulationException("Invalid decision. Decision cannot be greater than 5!")
            
    @staticmethod
    def __validateArrivalRate():
        if len(CallCenterSimulator.__arrivalRate) != 18:
            raise SimulationException("Invalid arrival rate. Arrival rate must have 18 elements!")
        for rate in CallCenterSimulator.__arrivalRate:
            if rate < 0 or rate > 100:
                raise SimulationException("Invalid arrival rate. Arrival rate should be within [0, 100]!")
            
    @staticmethod            
    def generateServiceTime() -> float:
        return np.max(np.random.exponential(228.98) + 77.020, 2000)
    
    @staticmethod
    def generateInterArrivalTime(systemTime) -> float:
        arrRate = CallCenterSimulator.__arrivalRate[int(systemTime / 1800)]
        if arrRate >= len(CallCenterSimulator.__arrivalRate):
            raise SimulationException("Invalid arrival rate. Arrival rate index out of range!")
        return np.random.exponential(1 / arrRate)

    def __init__(self, decision:list[int]) -> None:
        super().__init__()
        self.__validateInput(decision)
        self.__validateArrivalRate()
        self.__customers = list[Customer]() # records all customers
        self.__endTime = 3600 * 9  # 9 hours
        self.__serviceQueue = pQueue[Customer]()  # priority queues for customers

        # add lv1 agents of different schedules
        lv1Agents = [Agent(CallCenterSimulator.__schedule1, 0) for _ in range(decision[0])]
        lv1Agents.extend([Agent(CallCenterSimulator.__schedule2, 0) for _ in range(decision[1])])
        lv1Agents.extend([Agent(CallCenterSimulator.__schedule3, 0) for _ in range(decision[2])])
        self.__agents = [
            lv1Agents,  # currently include only lv1 agents
            list[Agent](),  # lv2 agents
            list[Agent](),  # lv3 agents
        ]
        
    def shouldStop(self) -> bool:
        return self.systemTime >= self.__endTime and self._eventQueue.empty()

    def getCustomers(self) -> list[Customer]:
        return self.__customers
    
    def getServiceQueue(self) -> pQueue[Customer]:
        return self.__serviceQueue
    
    def getAvailableAgent(self) -> Union[Agent, None]:
        for lv in range(3):
            agentsArr = self.__agents[lv]
            for agent in agentsArr:
                if agent.isAvailable(self.systemTime) and not agent.isBusy:
                    return agent
        return None

    def tryAddEvent(self, event:BaseDESEvent) -> bool:
        if event.time < self.systemTime:
            raise SimulationException(f"Invalid event time. Event time cannot be in the past! Current time: {self.systemTime}, event time: {event.time}")
        if event is Arrival:
            if event.time > self.__endTime:
                return False
            else:
                self._eventQueue.put(event.time, event)
                return True
        if event is ServiceCompletion:
            self._eventQueue.put(event.time, event)
            return True
        raise SimulationException(f"Invalid event. Event type {type(event)} not recognized!")
    
    def simulate(self) -> object:
        initialArrival = Arrival(0, self)
        self.tryAddEvent(initialArrival)
        while not self.shouldStop():
            event: BaseDESEvent = self._eventQueue.get()
            self.systemTime = event.time
            event.execute(self)

        stats = self.IterationStats()
        stats.avgTimeInQueue = np.mean([c.waitTime for c in self.__customers if c.waitTime is not None]),
        stats.avgServiceTime = np.mean([c.serviceTime for c in self.__customers if c.serviceTime is not None]),
        stats.avgWaitTime = np.mean([c.waitTime for c in self.__customers if c.waitTime is not None])
        return stats
    
    def run(self, num_iterations=100) -> SimulationResult:
        stats = [self.simulate() for _ in range(num_iterations)]
        
    

class ServiceCompletion(BaseDESEvent):
    
    def __init__(self, time: float, customer:Customer, agent:Agent) -> None:
        super().__init__(time)
        self.__customer = customer
        self.__agent = agent
    
    def execute(self, system: CallCenterSimulator):
        self.__agent.isBusy = False
        if self.__agent.isAvailable(system.systemTime):
            serviceQueue = system.getServiceQueue()
            if not serviceQueue.empty():
                customer = serviceQueue.get()
                serviceTime = system.generateServiceTime()
                leaveTime = system.systemTime + serviceTime
                serviceEvent = ServiceCompletion(leaveTime, customer, self.__agent)
                system.tryAddEvent(serviceEvent)

    def __str__(self) -> str:
        return f"LeaveEvent(time={self.time}"


class Arrival(BaseDESEvent):

    def __init__(self, time: float, system: CallCenterSimulator) -> None:
        super().__init__(time, system)
    
    def execute(self):

        # next arrival logic
        deltaTime = CallCenterSimulator.generateInterArrivalTime()
        nextArrTime = self.system.systemTime + deltaTime
        nextArrEvent = Arrival(nextArrTime)
        self.system.tryAddEvent(nextArrEvent)

        # current customer logic
        customer = Customer(self.system.systemTime)  # create new customer
        self.system.getCustomers().append(customer)
        priority = customer.priority
        serviceQueue = self.system.getServiceQueue()
        if len(serviceQueue) == 0:
            agent = self.system.getAvailableAgent()
            if agent is not None:
                agent.isBusy = True
                # start service
                serviceDuration = self.system.generateServiceTime()
                serviceEndTime = self.system.systemTime + serviceDuration
                serviceEvent = ServiceCompletion(serviceEndTime, customer, agent)
                self.system.tryAddEvent(serviceEvent)
            else:
                # wait in queue, will be served when an agent is available, corresponding logic in the serviceCompletion event
                serviceQueue.put(priority, customer)
                
    def __str__(self) -> str:
        return f"ArrivalEvent(time={self.time}"
    