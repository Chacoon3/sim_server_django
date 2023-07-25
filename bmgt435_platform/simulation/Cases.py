import datetime as dt
import scipy
import numpy as np
import statsmodels.api as sm
import random as pyr
import pandas as pd
from queue import PriorityQueue as pQueue



class Sampler(object):
    """
    static class, provides a set of interfaces for random number generation
    """

    # enum values
    flag_truncate_minmax = 0
    flag_truncate_uniform = 1
    flag_truncate_self_based = 2


    @staticmethod
    def loglogistic(gamma, beta, alpha):
        return scipy.stats.fisk.rvs(size = 1, loc = gamma, scale = beta, c = alpha)[0]
        

    @staticmethod
    def loglogistic_arr(gamma, beta, alpha, arr_size):
        return scipy.stats.fisk.rvs(size = arr_size, loc = gamma, scale = beta, c = alpha)
    

    @staticmethod
    def logistic(mean, stddev):
        return scipy.stats.logistic.rvs(size = 1, loc = mean, scale = stddev)[0]
    

    @staticmethod
    def logistic_arr(mean, stddev, arr_size):
        return scipy.stats.logistic.rvs(size = arr_size, loc = mean, scale = stddev)
    

    @staticmethod
    def normal(mean, stddev):
        return np.random.normal(size=1, loc=mean, scale=stddev, )[0]


    @staticmethod
    def normal_arr(mean, stddev, arr_size):
        return np.random.normal(size=arr_size, loc=mean, scale=stddev, )
    

    @staticmethod
    def lognorm(mean, stddev):
        """
        mean: the first parameter in @risk plus the value of risk shift, if any
        var: the seccond parameter in @risk
        not recommended for efficiency issue
        """
        return pyr.lognormvariate(mean,stddev)
    

    @staticmethod
    def triangular(left, mode, right, size) -> list | np.ndarray | float:
        return np.random.triangular(left, mode, right, size)
    

    @staticmethod
    def lognorm_arr(mean, stddev, arr_size,):
        '''
        generate truncated random number from log normal
        mean: the first parameter in @risk plus the value of risk shift, if any
        var: the seccond parameter in @risk
        not recommended for efficiency issue
        '''
        return np.array([pyr.lognormvariate(mean, stddev) for i in range(arr_size)])
    
    

    @staticmethod
    def truncate(val, enum_style, lo, hi, rng = None):
        if enum_style == Sampler.flag_truncate_minmax:
            val = min(hi, val)
            val = max(lo, val)
        elif enum_style == Sampler.flag_truncate_uniform:
           if lo > val or hi < val:
               val = np.random.uniform(lo, hi) 
        elif enum_style == Sampler.flag_truncate_self_based:
            if not rng:
                raise Exception("self_based truncation should have a random number generator")
            while lo > val or hi < val:
                val = rng()
        
        return val
    

    @staticmethod
    def __helper_self_based_truncate(val, lo, hi, rng):
        while val < lo or val > hi:
            val = rng()
        return val


    @staticmethod
    def truncate_arr(val_arr, truncate_style, lo, hi, rng = None):
        if truncate_style == Sampler.flag_truncate_minmax:
            val_arr = np.fmin(val_arr, hi)
            val_arr = np.fmax(val_arr, lo)
        elif truncate_style == Sampler.flag_truncate_uniform:
            val_arr = np.where((lo <= val_arr) & (val_arr <= hi), val_arr, np.random.uniform(lo, hi))
        elif truncate_style == Sampler.flag_truncate_self_based:
            if not rng:
                raise Exception("self_based truncation should have a random number generator")
            val_arr = [v if lo <- v and v <= hi else Sampler.__helper_self_based_truncate(v, lo, hi, rng) for v in val_arr]
            val_arr = np.array(val_arr)
            
        return val_arr



class BaseSimResult(object):
    """
    base class of all the simulation object.
    Simulation cases may use subclass of this class to represent the result of simulation.
    """
    def __init__(self) -> None:
        return



class CaseBase(object):
    """
    Base class of all the simulation cases
    """

    _msg_assert_err_ = "Invalid case setting. Simulation cannot execute!"


    _flag_output_basic = 'basic'
    _flag_output_detail = 'detail'


    def __init__(self,) -> None:
        return


    def _assert(self) -> bool:
        """
        called before running to check if the parameter settings of the case is correct.
        should be override for each case
        """
        return True
    
    
    def simulate(self, output_style):
        '''
        the logic of one iteration in this simulation case
        simple_output should decide whether detailed statistics are to be recorded in each iteration
        '''
        return


    def run(self, output_style):
        '''
        run the simulation case with specified number of iterations
        ouutput_style should decide whether detailed or simplified simulation statistics should be returned
        '''
        if not self._assert():
            raise Exception(CaseBase._msg_assert_err_)
        
        return
    

    def get_latest_result(self):
        """
        returns the simulation result of the most recent simulation
        """
        return



class CaseMC(CaseBase):
    """
    base class of Monte Carlo simulation cases
    """
    def __init__(self, num_iterations:int=1, simple_output = True) -> None:
        self._num_iteration = num_iterations
        return


    def set_num_iteration(self, time):
        if time <= 0:
            return
        self._num_iteration = time


    def num_iteration(self):
        return self._num_iteration
    

    def run(self, output_style):
        if not self._assert():
            raise Exception(CaseBase._msg_assert_err_)
        
        counter = self._num_iteration
        while (counter > 0):
            self.simulate(output_style=None)
            counter -=1
        return



class CaseDES(CaseBase):
    """
    base class of all descrete event simulation cases
    """


    def __init__(self,  stopCondition, simple_output = True) -> None:
        self.__pQueue = pQueue()  # event queue
        self.__t = 0    # timer
        self.__shouldStop = stopCondition

    def run(self, output_style):
        if not self._assert():
            raise Exception(CaseBase._msg_assert_err_)
        

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



class FoodCenter(CaseMC):

    
    class Center(object):
        """
        maintain the state of a center
        """

        def __init__(self, policy:tuple[int,int], initial_inventory, name) -> None:
            self.__s_small = policy[0]
            self.__s_big = policy[1]
            self.__inventory = initial_inventory
            self.__name = name


        def s_small(self): return self.__s_small

        
        def s_big(self): return self.__s_big


        def get_inventory(self): return self.__inventory


        def set_inventory(self, val): 
            if val < 0:
                return
            
            self.__inventory = val


        def add_inventory(self, val):
            self.__inventory += val
            return


        def get_name(self):
            return self.__name



    # static members 

    __center_names = ['10', '13', '43', '52', '67', '137']
    __center_weekly_cost = 24000    # weekly fixed cost for a center
    __demand_cov_matrix = None
    __holding_cost_penalty = 11     # multiplier for holding cost
    __min_week_demand = 10
    __max_week_demand = 6000

    
    @staticmethod
    def get_case_info():
        return {
            'case_id': 1,
            'case_name': 'Food Center Simulation',
            'case_description': 'Simulate the inventory management of food centers in Singapore',
            'case_max_trial':5,
        }


    @staticmethod
    def sim_center_demand():
        """
        returns discretized, truncated demand of all the six centers regardless of whether it is chosen, stored in a dict where keys are center ids
        """
        if FoodCenter.__demand_cov_matrix is not np.ndarray:
            FoodCenter.__demand_cov_matrix = pd.read_csv(
                    r'C:\\Users\\Chaconne\\Documents\\学业\\Projects\\RA_Simulation\\app_server\\config\\case_food_center_cov_matrix.csv',
                      index_col='center_id').values
            
        arr_mu = [2329, 2967, 2711, 2153, 1958, 2155]
        arr_key = ['10', '13', '43', '52', '67', '137']
        arr_demand = scipy.stats.multivariate_normal.rvs(mean = arr_mu, cov = FoodCenter.__demand_cov_matrix, size = 1)
        return {
                    k: min(max(FoodCenter.__min_week_demand, round(d)), FoodCenter.__max_week_demand)  
                    for k,d in zip(arr_key, arr_demand)
                }
        

    @staticmethod
    def sim_checkout_price(size:int = 1):
        price = Sampler.triangular(6.7, 29, 76.6, size,)
        price = np.round(price, decimals= 2)
        return price


    def __init__(
            self, 
            num_iterations:int=10, 
            centers:list[str] = [], 
            policies: list[tuple[int,int]] = [],
            num_weeks:int = 8,
            initial_inventory = 0,
            constraint_total_weekly_restock = 7000,
        ) -> None:

        super().__init__(num_iterations=num_iterations)
        self.__centers = centers
        self.__policies = policies
        self.__num_weeks = num_weeks
        self.__initial_inventory = initial_inventory
        self.__constraint_weekly_purchase = constraint_total_weekly_restock


    def _assert(self) -> bool:
        value_valid = self._num_iteration >0 and len(self.__centers) > 0 and len(self.__centers) == len(self.__policies) and self.__num_weeks > 0
        location_valid = all([l in FoodCenter.__center_names for l in self.__centers])
        policy_valid = all([p[0] > 0 and p[1] > p[0] for p in self.__policies])

        value_valid = value_valid and location_valid and policy_valid
        return value_valid


    def simulate(self, output_stype):
        # instantialize centers
        centers = []
        for week_index in range (len(self.__centers)):
            name = self.__centers[week_index]
            policy = self.__policies[week_index]
            centers.append(FoodCenter.Center(policy=policy, initial_inventory= self.__initial_inventory, name=name))


        # define the output data: 
        #       the output data describes one instance of the simulation
        #       a nested dictionary to store the weekly state of each center and thereby yield the aggregation statistics
        history = {
            c.get_name(): {
                'cum_demand': 0,
                'cum_supply': 0,
                'cum_shortage_count': 0,
                'cum_shortage_amount':0,
                'cum_revenue': 0,
                'cum_holding_cost':0,

                'prior_inventory': [],
                'post_inventory': [],
                'demand': [],
                'supply': [],
                'shortage_count': [],
                'shortage_amount':[], 
                'revenue': [],
                'holding_cost':[]
            }
            for c in centers
        }


        output = {
            'perf_metric':float('-inf'),
            'total_revenue': 0,
            'total_shortage_count': 0,
            'total_shortage_amount':0,
            'total_holding_cost':0,
            'total_fixed_cost':0,
            'history':history
        }


        # main logic

        # for every week
        for week_index in range(self.__num_weeks):
        
            # check inventory
            arr_purchase = [center.s_big() - center.get_inventory() if center.get_inventory() < center.s_small() else 0 for center in centers]
            total_purchase = sum(arr_purchase)

            # check if inventory request exceeds the constraint
            if total_purchase > self.__constraint_weekly_purchase:
                # if exceeds the constraint, adjust the original request array proportionally so that the sum equals the constraint
                purchase_ratio = np.array(arr_purchase) / total_purchase
                adjusted_purchase = purchase_ratio * self.__constraint_weekly_purchase
                adjusted_purchase = np.round(adjusted_purchase, decimals= 0).astype(int)
                total_purchase = sum(adjusted_purchase)

                # in case the conversion from float to int leads the adjusted purchase to exceed the constraint
                # reduce the purchase amout of each center till the sum equals the constraint again
                if total_purchase > self.__constraint_weekly_purchase:
                    diff = total_purchase - self.__constraint_weekly_purchase
                    while diff > 0:
                        for i in range(len(adjusted_purchase)):
                            if (adjusted_purchase[i] > 0):
                                if adjusted_purchase[i] >= diff:
                                    adjusted_purchase[i] -= diff
                                    diff = 0
                                else:
                                    diff -= adjusted_purchase[i] 
                                    adjusted_purchase[i] = 0
                            if diff == 0:
                                break
                arr_purchase = adjusted_purchase
            

            # update inventory
            for center, purchase in zip(centers, arr_purchase):
                center.add_inventory(purchase)
            
            # decide the weekly demand at each center
            #center_demand = np.array([self.__dict_center_demand[center.get_name()]() for center in centers])
            center_demand = FoodCenter.sim_center_demand()
            center_demand = [center_demand[center.get_name()] for center in centers]

            # decide the actual number of orders that will be handled by each center
            center_supply = np.array([min(center.get_inventory(), demand) for center, demand in zip(centers, center_demand)])

            # for each center:
            #       decide the observations of checkout price
            #       calculate the weekly revenue
            #       apply shortage penalty
            #       record metrics of interest into output
            for i in range(len(centers)):

                center = centers[i]
                c_name = center.get_name()
                demand = center_demand[i]
                supply = center_supply[i]
                shortage_count = max(0, demand - supply)
                arr_order_price = FoodCenter.sim_checkout_price(size=demand)
                covered_order_price = arr_order_price[:supply]      # orders that are met
                lost_order_price = arr_order_price[supply:]     # orders that are failed to meet
                order_revenue = round(sum(covered_order_price), 2)
                shortage_penalty = round(sum(lost_order_price), 2)

                prior_inv = center.get_inventory()  # this records the inventory level after the weekly purchase
                center.add_inventory(-supply)
                post_inv = center.get_inventory()   # this records the inventory after supplying the demand in the week
                holding_cost = prior_inv * FoodCenter.__holding_cost_penalty

                history[c_name]['cum_demand'] += demand
                history[c_name]['cum_supply'] += supply
                history[c_name]['cum_shortage_count'] += shortage_count
                history[c_name]['cum_shortage_amount'] = round(history[c_name]['cum_shortage_amount'] + shortage_penalty, 2)
                history[c_name]['cum_revenue'] =  round(history[c_name]['cum_revenue'] + order_revenue, 2)
                history[c_name]['cum_holding_cost'] += holding_cost

                if output_stype == self._flag_output_detail:
                    history[c_name]['prior_inventory'].append(prior_inv)
                    history[c_name]['post_inventory'].append(post_inv)
                    history[c_name]['demand'].append(demand)
                    history[c_name]['supply'].append(supply)
                    history[c_name]['shortage_count'].append(shortage_count)
                    history[c_name]['shortage_amount'].append(shortage_penalty)
                    history[c_name]['revenue'].append(order_revenue)
                    history[c_name]['holding_cost'].append(holding_cost)


        # perform aggregation
        output['total_revenue'] = round(sum([
                history[c.get_name()]['cum_revenue'] for c in centers
            ]), 2)
        output['total_shortage_count'] = round(sum([
                history[c.get_name()]['cum_shortage_count'] for c in centers
            ]), 2)
        output['total_shortage_amount'] = round(sum([
                history[c.get_name()]['cum_shortage_amount'] for c in centers
            ]), 2)
        output['total_holding_cost'] = sum([
            history[c.get_name()]['cum_holding_cost'] for c in centers
        ])
        output['total_fixed_cost'] = len(centers) * self.__num_weeks * FoodCenter.__center_weekly_cost
        output['perf_metric'] = round(
                output['total_revenue'] - output['total_shortage_amount'] - output['total_fixed_cost'] - output['total_holding_cost'],
                2
            )
        return output

                

    def run(self, output_style):
        if not self._assert():
            raise Exception(CaseBase._msg_assert_err_)
        
        counter = self._num_iteration
        res = []
        while (counter > 0):
            sim_output = self.simulate(output_stype=output_style)
            res.append(sim_output)
            counter -=1

        return  res