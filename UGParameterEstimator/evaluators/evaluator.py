import numpy as np
import math
import os
from abc import ABC, abstractmethod
from UGParameterEstimator import ParameterManager, Evaluation, ParameterOutputAdapter, ErroredEvaluation

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
        self.cache.update(evaluations)       
        self.serial_evaluation_count += 1
        self.total_evaluation_count += len(evaluations)
        if self.resultobj is not None:
            self.resultobj.addEvaluations(evaluations, tag)
            self.resultobj.addRunMetadata("evaluator_totalcount", self.total_evaluation_count)
            self.resultobj.addRunMetadata("evaluator_serialcount", self.serial_evaluation_count)
            self.resultobj.addRunMetadata("evaluator_cachehits", self.cached_evaluation_count)

    def checkCache(self, parameters):
        for evaluation in self.cache:
            if evaluation.parameters is None:
                continue
            if np.array_equal(evaluation.parameters, parameters):
                if self.resultobj is not None:
                    self.resultobj.log("Served evaluation " + str(evaluation.eval_id) + " from cache!")
                self.cached_evaluation_count += 1
                return evaluation
        return None

    def reset(self):
        self.cache = set()
        self.cached_evaluation_count = 0
        self.serial_evaluation_count = 0
        self.total_evaluation_count = 0

    def getStatistics(self):        
        string = "Total count of evaluations: " + str(self.total_evaluation_count) + "\n"
        string += "Taken from cache: " + str(self.cached_evaluation_count) + "\n"
        string += "Serial count: " + str(self.serial_evaluation_count)
        return string

    def __str__(self):
        string = "Currently cached Evaluations " + str(len(self.cache)) + "\n" 
        string += self.getStatistics()
        return string

    @classmethod
    def ConstructEvaluator(self,luafile, directory, parametermanager: ParameterManager, evaluation_type: Evaluation, parameter_output_adapter: ParameterOutputAdapter, fixedparameters, parallelism, cliparameters=[]):
        
        import UGParameterEstimator
        if "UGSUBMIT_TYPE" in os.environ:
            print("Detected cluster " + os.environ["UGSUBMIT_TYPE"] + ", using ClusterEvaluator")
            return UGParameterEstimator.ClusterEvaluator(luafile, directory, parametermanager, evaluation_type, parameter_output_adapter, fixedparameters, parallelism, cliparameters)
        else:
            print("No cluster detected, using LocalEvaluator")
            return UGParameterEstimator.LocalEvaluator(luafile, directory, parametermanager, evaluation_type, parameter_output_adapter, fixedparameters, parallelism, cliparameters)