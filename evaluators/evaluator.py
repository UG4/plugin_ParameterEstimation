import numpy as np
import math
from abc import ABC, abstractmethod

class Evaluator(ABC):

    resultobj = None
    evaluation_count = 0
    serial_evaluation_count = 0

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
