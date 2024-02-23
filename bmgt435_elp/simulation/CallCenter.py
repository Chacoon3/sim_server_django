import io
import numpy as np
import pandas as pd
from .Core import SimulationException, SimulationResult, BaseDiscreteEventSimulator, BaseDESEvent, AppPriorityQueue
from typing import Union

"""
Implementation guidline:

- Use events to change the state of the system
- Use abstract data type to store the state of the system
"""


class Customer:
    __id = -1
    __priorityCumDist = [0.03, 0.06, 0.57, 0.98, 1.  ]

    @staticmethod
    def __determineOfferType() -> int:
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
        self.__offerType = Customer.__determineOfferType()
        self.__serviceType = Customer.__determineServiceType()
        self.__arrivalTime: float = arrTime
        self.__serviceTime: float = None
        self.__exitTime:float = None
        self.__enqueueTime:float = None
        self.__serviceStartTime:float = None

    @property
    def id(self) -> int:
        return self.__id
    
    @property
    def offerType(self) -> int:
        """
        categorical variable representing the type of offer the customer is interested in.
        related to the priority according to which the customer will be served.
        """
        return self.__offerType
    
    @property
    def arrivalTime(self) -> float:
        return self.__arrivalTime
    
    @arrivalTime.setter
    def arrivalTime(self, value:float):
        if value < 0:
            raise SimulationException("Invalid arrival time. Arrival time cannot be negative!")
        self.__arrivalTime = value
    
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
    def serviceStartTime(self) -> Union[float, None]:
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
    def serviceTime(self) -> Union[float, None]:
        return self.__serviceTime
    
    @serviceTime.setter
    def serviceTime(self, value:float):
        if value < 0:
            raise SimulationException("Invalid service time. Service time cannot be negative!")
        self.__serviceTime = value
    
    @property
    def serviceType(self) -> int:
        return self.__serviceType


class AgentSchedule:
    """
    nested list to store the schedule of an agent. Each inner list represents a time interval.
    """

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

    def __init__(self, schedule:AgentSchedule, level:int) -> None:
        Agent.__id += 1
        self.__id = Agent.__id
        self.__level = level
        self.__schedule = schedule
        self.__isBusy = False
        self.__totalServiceTime: float = 0.0

    @property
    def id(self) -> int:
        return self.__id
    
    @property
    def level(self) -> int:
        return self.__level
    
    @property
    def schedule(self):
        return self.__schedule
    
    @property
    def totalServiceTime(self) -> float:
        """
        total time the agent has served customers.
        """
        return self.__totalServiceTime

    @totalServiceTime.setter
    def totalServiceTime(self, value:float):
        if value < 0 or value < self.__totalServiceTime:
            raise SimulationException("Invalid total service time. Total service time cannot be negative!")
        self.__totalServiceTime = value

    @property
    def totalScheduleTime(self) -> float:
        """
        total time the agent has been scheduled to work.
        """
        return sum([s[1] - s[0] for s in self.__schedule.schedule])
        
    def isOnSchedule(self, time:float) -> bool:
        """
        tells if the agent is on schedule at the given time.
        """
        for s in self.__schedule.schedule:
            if s[0] <= time < s[1]:
                return True
        return False
    
    @property
    def isBusy(self) -> bool:
        """
        tells if the agent is currently serving a customer.
        """
        return self.__isBusy

    @isBusy.setter
    def isBusy(self, value:bool):
        self.__isBusy = value
    
    
class CallCenterResult(SimulationResult):
    
    def __init__(self, score: float, aggregated_data: pd.DataFrame = None, iteration_data: list = None) -> None:
        super().__init__(score, aggregated_data, iteration_data)

    def asFileStream(self) -> io.BytesIO:
        raise NotImplementedError()
    
    def asDict(self) -> dict:
        raise NotImplementedError()


class CallCenterSimulator(BaseDiscreteEventSimulator):
    """
    systemTime: float, refers to the current time in the simulation, measured by seconds, starting at 0.
    """

    class IterationStats:
        """
        statistics collected from one iteration of the simulation
        """
        def __init__(self) -> None:
            self.maxTimeInQueue: float = None
            self.avgTimeInQueue: float = None

            self.maxServiceTime: float = None
            self.avgServiceTime: float = None

            self.maxWaitTime: float = None
            self.avgWaitTime: float = None

            self.qualityOfService: float = None
            self.agentUtilizationRate: float = None

            self.customerArrived: int = None
            self.customerServed: int = None


    # schedule is represented as a nested list. Each inner list represents a time interval.
    # an agent may work during multiple time intervals in a day
    __schedule1 = AgentSchedule([[0 * 3600, 4 * 3600]])  # 8am to 12pm
    __schedule2 = AgentSchedule([[3 * 3600, 7 * 3600]])  # 11am to 3pm
    __schedule3 = AgentSchedule([[5 * 3600, 9 * 3600]])  # 1pm to 5pmwe
    __arrivalRateWeightBySlot = [
        0.0391, 0.0901, 0.0781, 0.0641, 0.0981, 0.0811, 0.024, 0.03, 0.0451, 0.019, 0.03, 0.0701, 0.0751, 0.0776, 0.0861,
        0.032, 0.026, 0.0381
    ]   # the weight of arrival rate for each 30 minutes time slot. 
        # should be multiplied by the estimated total dailly arrivals to get the arrival rate for each slot
    __estimatedDailyTotalArrivals: float = 534
    __timeSlotLengthInSec: float = 1800  # 30 minutes
    __lv1AgentsCount: int = 15

    @staticmethod
    def __validateInput(decision:list[int]):
        for d in decision:
            if d < 0:
                raise SimulationException("Invalid decision. Decision cannot be negative!")
            if d > 10:
                raise SimulationException("Invalid decision. Decision cannot be greater than 5!")
        if sum(decision) > CallCenterSimulator.__lv1AgentsCount:
            raise SimulationException(f"Invalid decision. Total number of agents cannot be greater than {CallCenterSimulator.__lv1AgentsCount}!")
            
    @staticmethod
    def __validateArrivalRate():
        if len(CallCenterSimulator.__arrivalRateWeightBySlot) != 18:
            raise SimulationException("Invalid arrival rate. Arrival rate must have 18 elements!")
        for rate in CallCenterSimulator.__arrivalRateWeightBySlot:
            if rate < 0 or rate > 100:
                raise SimulationException("Invalid arrival rate. Arrival rate should be within [0, 100]!")
            
    @staticmethod            
    def generateServiceTime() -> float:
        return min(np.random.exponential(228.98) + 77.020, 2000) # truncating with 2000 seconds
    
    @staticmethod
    def generateInterArrivalTime(currentTime: float) -> float:
        slotLength = CallCenterSimulator.__timeSlotLengthInSec
        timeSlot = int(currentTime // slotLength)
        if timeSlot < 0 or timeSlot > len(CallCenterSimulator.__arrivalRateWeightBySlot):
            raise SimulationException(f"Invalid arrival rate. Arrival rate index out of range! systime: {currentTime}")
        arrRate = CallCenterSimulator.__arrivalRateWeightBySlot[timeSlot] * CallCenterSimulator.__estimatedDailyTotalArrivals 
        return np.random.exponential(slotLength / arrRate) # time conversion from half hour to seconds

    def __init__(self, decision:list[int]) -> None:
        super().__init__()
        self.__validateInput(decision)
        self.__validateArrivalRate()
        self.__customers = list[Customer]() # records all customers
        self.__endTime = 3600 * 9  # 9 hours
        self.__customerQueue = AppPriorityQueue()  # priority queues for customers

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
        return self._eventQueue.empty() or self.systemTime >= self.__endTime

    @property
    def customers(self) -> list[Customer]:
        return self.__customers
    
    def logCustomer(self, customer:Customer):
        self.__customers.append(customer)
    
    @property
    def customerQueue(self) -> AppPriorityQueue:
        return self.__customerQueue
    
    
    def getIdelAgent(self) -> Union[Agent, None]:
        for lv in range(3):
            agentsArr = self.__agents[lv]
            for agent in agentsArr:
                if agent.isOnSchedule(self.systemTime) and not agent.isBusy:
                    return agent
        return None


    def addEvent(self, event:BaseDESEvent):
        if event.time < self.systemTime:
            raise SimulationException(f"Invalid event time. Event time cannot be in the past! Current time: {self.systemTime}, event time: {event.time}")
        eventType = type(event)
        if eventType == Arrival or eventType == ServiceCompletion or eventType == AgentOnSchedule:
            self._eventQueue.add(event.time, event)
        else:
            raise SimulationException(f"Invalid event. Event type {type(event)} not recognized!")
        
    @property
    def endTime(self) -> float:
        return self.__endTime    

    def qualityOfService(self, x: float) -> float:
        """
        one of the two performance measures described in the original paper
        """
        totalCalls = len(self.__customers)
        qualifiedCalls = len([c for c in self.__customers if c.waitTime is not None and c.waitTime <= x])
        return round(qualifiedCalls / totalCalls * 100, 4)


    def agentUtilizationRate(self) -> float:
        """
        one of the two performance measures described in the original paper
        """
        totalServiceTime = sum([a.totalServiceTime for a in self.__agents[0]])
        totalScheduleTime = sum([a.totalScheduleTime for a in self.__agents[0]])
        return round(totalServiceTime / totalScheduleTime * 100, 4)
    

    def reset(self):
        self._eventQueue.clear()
        self.__customerQueue.clear()
        self.__customers.clear()
        self._time = 0


    def simulate(self) -> IterationStats:
        # create initial arrival
        initialArrival = Arrival(0, self)
        self.addEvent(initialArrival)

        # assign on schedule events to agents who start working at a later time
        for agents in self.__agents:
            for agent in agents:
                startTimes = [interval[0] for interval in agent.schedule.schedule]
                for t in startTimes:
                    if t > 0:
                        agentOnSchedule = AgentOnSchedule(t, agent, self)
                        self.addEvent(agentOnSchedule)

        while not self.shouldStop():
            event: BaseDESEvent = self._eventQueue.get()
            self.systemTime = event.time
            event.execute()

        # output iteration stats
        stats = self.IterationStats()
        stats.maxTimeInQueue = np.max([c.waitTime for c in self.__customers if c.waitTime is not None]),
        stats.avgTimeInQueue = np.mean([c.waitTime for c in self.__customers if c.waitTime is not None]),

        stats.maxServiceTime = np.max([c.serviceTime for c in self.__customers if c.serviceTime is not None]),
        stats.avgServiceTime = np.mean([c.serviceTime for c in self.__customers if c.serviceTime is not None]),

        stats.maxWaitTime = np.max([c.waitTime for c in self.__customers if c.waitTime is not None]),
        stats.avgWaitTime = np.mean([c.waitTime for c in self.__customers if c.waitTime is not None])

        stats.qualityOfService = self.qualityOfService(300)
        stats.agentUtilizationRate = self.agentUtilizationRate()

        stats.customerArrived = len(self.__customers)
        stats.customerServed = len([c for c in self.__customers if c.serviceTime is not None])

        self.reset()    # reset the state of the instance so that next iteration can be executed without errors
        return stats
  
   
    def run(self, num_iterations=100) -> SimulationResult:
        iterationStats = [self.simulate() for _ in range(num_iterations)]

        # generate aggregated statistics
        avgQualityOfService = np.mean([s.qualityOfService for s in iterationStats])

        avgAgentUtilizationRate = np.mean([s.agentUtilizationRate for s in iterationStats])

        avgMaxTimeInQueue = np.mean([s.maxTimeInQueue for s in iterationStats])
        avgAvgTimeInQueue = np.mean([s.avgTimeInQueue for s in iterationStats])

        avgMaxServiceTime = np.mean([s.maxServiceTime for s in iterationStats])
        avgAvgServiceTime = np.mean([s.avgServiceTime for s in iterationStats])

        avgMaxWaitTime = np.mean([s.maxWaitTime for s in iterationStats])
        avgAvgWaitTime = np.mean([s.avgWaitTime for s in iterationStats])
        
        avgCustomerArrived = np.mean([s.customerArrived for s in iterationStats])
        avgCustomerServed = np.mean([s.customerServed for s in iterationStats])

        summary = dict(
            avgQualityOfService=avgQualityOfService,
            avgAgentUtilizationRate=avgAgentUtilizationRate,
            avgMaxTimeInQueue=avgMaxTimeInQueue,
            avgAvgTimeInQueue=avgAvgTimeInQueue,
            avgMaxServiceTime=avgMaxServiceTime,
            avgAvgServiceTime=avgAvgServiceTime,
            avgMaxWaitTime=avgMaxWaitTime,
            avgAvgWaitTime=avgAvgWaitTime,
            avgCustomerArrived=avgCustomerArrived,
            avgCustomerServed=avgCustomerServed
        )

        score = avgQualityOfService * 0.5 + avgAgentUtilizationRate * 0.5

        return CallCenterResult(score, summary, iterationStats)
        

def _serveCustomerHelper(customer:Customer, agent:Agent, system:CallCenterSimulator):
    """
    helper function to execute serving logic. used in multiple events
    """

    # start service
    customer.serviceStartTime = system.systemTime
    serviceTime = system.generateServiceTime()
    leaveTime = system.systemTime + serviceTime
    serviceEvent = ServiceCompletion(leaveTime, serviceTime, customer, agent, system)
    system.addEvent(serviceEvent)
    agent.isBusy = True


class AgentOnSchedule(BaseDESEvent):
    def __init__(self, time: float, agent:Agent, system: CallCenterSimulator) -> None:
        super().__init__(time)
        self.__agent: Agent = agent
        self.__system: CallCenterSimulator = system

    def execute(self):
        agent = self.__agent

        if not agent.isOnSchedule(self.time):
            raise SimulationException(f"Logic error. Agent {agent.id} (level {agent.level}) is not on schedule at time {self.time}!")

        if agent.isBusy:    # this means the agent is currently serving a customer.
            return
        
        serviceQueue = self.__system.customerQueue
        if not serviceQueue.empty():
            customer = serviceQueue.get()
            _serveCustomerHelper(customer, agent, self.__system)
        

class ServiceCompletion(BaseDESEvent):
    
    def __init__(self, time: float, serviceTimeLength:float, customer:Customer, agent:Agent, system: CallCenterSimulator) -> None:
        super().__init__(time)
        self.__customer: Customer = customer
        self.__agent: Agent = agent
        self.__system: CallCenterSimulator = system
        self.__serviceTime = serviceTimeLength
    
    def execute(self):
        # customer logic
        self.__customer.serviceTime = self.__serviceTime
        self.__customer.exitTime = self.time
        
        # agent logic. serve next customer only when the agent is on schedule
        self.__agent.isBusy = False
        self.__agent.totalServiceTime += self.__serviceTime
        if self.time < self.__system.endTime and self.__agent.isOnSchedule(self.time):
            serviceQueue = self.__system.customerQueue
            if not serviceQueue.empty():
                customer: Customer = serviceQueue.get()
                _serveCustomerHelper(customer, self.__agent, self.__system)


class Arrival(BaseDESEvent):

    def __init__(self, time: float, system: CallCenterSimulator) -> None:
        super().__init__(time)
        self.__system: CallCenterSimulator = system
    
    def execute(self):

        # next arrival logic
        deltaTime = CallCenterSimulator.generateInterArrivalTime(self.time)
        nextArrTime = self.__system.systemTime + deltaTime
        if nextArrTime < self.__system.endTime:
            nextArrEvent = Arrival(nextArrTime, self.__system)
            self.__system.addEvent(nextArrEvent)

        # current customer logic
        customer = Customer(self.time)  # create new customer who arrives at the current time
        self.__system.logCustomer(customer)
        offerType = customer.offerType
        customerQueue = self.__system.customerQueue
        customer.enqueueTime = self.time  # in this case the incoming call is immediately enqueued
        if len(customerQueue) == 0:
            agent = self.__system.getIdelAgent()
            if agent:
                # start service
                _serveCustomerHelper(customer, agent, self.__system)
            else:
                # wait in queue
                customerQueue.add(offerType, customer)