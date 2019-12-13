import numpy as np
import math
from abc import ABC, abstractmethod

class Evaluator(ABC):

    resultobj = None
    total_evaluation_count = 0
    serial_evaluation_count = 0
    cached_evaluation_count = 0
    cache = set()

    @property
    @abstractmethod
    def parallelism(self):
        pass

    @abstractmethod    
    def evaluate(self, evaluationlist, transform, tag):
        pass

    def setResultObject(self, res):
        self.resultobj = res
    
    def handleNewEvaluations(self, evaluations, tag):
        if self.resultobj is not None:
            self.resultobj.addEvaluations(evaluations, tag)
        self.cache.update(evaluations)       
        self.serial_evaluation_count += 1
        self.total_evaluation_count += len(evaluations)

    def checkCache(self, parameters):
        for evaluation in self.cache:
            if np.allclose(evaluation.parameters, parameters, rtol=1e-8):
                if self.resultobj is not None:
                    self.resultobj.log("Served evaluation from cache!")
                self.cached_evaluation_count += 1
                return evaluation                
        return None 

    def reset(self):
        self.cache = set()
        self.cached_evaluation_count = 0
        self.serial_evaluation_count = 0
        self.total_evaluation_count = 0

    def __str__(self):
        string = "Evaluator. Currently cached Evaluations " + str(len(self.cache)) + "\n" 
        string += "Total count of evaluations: " + str(self.total_evaluation_count) + "\n"
        string += "Taken from cache: " + str(self.cached_evaluation_count) + "\n"
        string += "Serial count: " + str(self.serial_evaluation_count)

        return string