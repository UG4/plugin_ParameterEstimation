import subprocess
import numpy as np
import os
import math
import time
from UGParameterEstimator import FreeSurfaceTimeDependentEvaluation, ParameterManager, Evaluator, Result

class TestEvaluator(Evaluator):
    def __init__(self, parametermanager: ParameterManager, resultobj: Result):
        self.parametermanager = parametermanager
        self.fixedparameters = {}
        self.id = 1
        self.resultobj = resultobj

    @property
    def parallelism(self):
        return 8

    def evaluate(self, evaluationlist, transform=True, tag=""):
        
        results = []

        for beta in evaluationlist:

            entry = []

            if transform:
                transformed = self.parametermanager.getTransformedParameters(beta)
            else:
                transformed = beta

            if transformed is None:
                results.append(None)
                continue

            for x in [1,2,3]:                

                entry.append([transformed[0]*math.pow(x,2), 5*transformed[1]*x, math.pow(2,transformed[1])])

            data = FreeSurfaceTimeDependentEvaluation(entry,[1,2,3], [1,2,3], 2, self.id, transformed)
            self.id += 1
            self.evaluation_count += 1
        
            results.append(data)


        self.handleNewEvaluations(results, tag)
        return results

    def __enter__(self):
        pass
    
    def __exit__(self, type, value, traceback):
        pass