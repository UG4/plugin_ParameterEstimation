import subprocess
import numpy as np
import os
import math
import time
from UGParameterEstimator import FreeSurfaceTimeDependentEvaluation, ParameterManager, Evaluator, Result, ErroredEvaluation

class TestEvaluator(Evaluator):
    def __init__(self, parametermanager: ParameterManager, resultobj: Result, function="rosenbrock"):
        self.parametermanager = parametermanager
        self.fixedparameters = {}
        self.id = 1
        self.function = function
        self.resultobj = resultobj

    @property
    def parallelism(self):
        return 8

    def evaluate(self, evaluationlist, transform=True, tag=""):
        
        results = []

        for beta in evaluationlist:

            if transform:
                x = self.parametermanager.getTransformedParameters(beta)
            else:
                x = beta

            if x is None:
                results.append(ErroredEvaluation(beta, reason="Infeasible parameters"))
                continue

            res = self.checkCache(x)
            
            if res is not None:
                results.append(res)
                continue
    
            if self.function == "rosenbrock":
                entry = [10*(x[1]-x[0]**2), 1-x[0]]

                data = FreeSurfaceTimeDependentEvaluation(entry,[1], [1,2], 2, self.id, x)
            self.id += 1
        
            results.append(data)


        self.handleNewEvaluations(results, tag)
        return results

    def __enter__(self):
        pass
    
    def __exit__(self, type, value, traceback):
        pass