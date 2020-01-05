#!/usr/bin/env python3

import subprocess
import skopt
import numpy as np
import scipy.optimize
import os
import time
from enum import Enum
from UGParameterEstimator import Result, LineSearch, Evaluator, ParameterManager, ErroredEvaluation
from abc import ABC, abstractmethod

class Optimizer(ABC):

    Differencing = Enum("Differencing", "central forward pure_forward pure_central")

    def __init__(self, epsilon, differencing: Differencing):
        self.differencing = differencing
        self.finite_differencing_epsilon = epsilon

        if epsilon < 0:
            epsilon = np.sqrt(np.finfo(np.float).eps)

    def measurementToNumpyArrayConverter(self, evaluations, target):        
        results = []
        for e in evaluations:
            if e is None or isinstance(e, ErroredEvaluation):
                results.append(None)
            else:
                results.append(e.getNumpyArrayLike(target))
        return results

    def getJacobiMatrix(self, point, evaluator, target, result):
        jacobi = []

        neededevaluations = []
        neededevaluations.append(point)

        if(self.differencing == Optimizer.Differencing.forward):
            for i in range(len(point)):
                changed = np.copy(point)
                if changed[i] == 0:
                    changed[i] = self.finite_differencing_epsilon
                else:
                    changed[i] *= 1+self.finite_differencing_epsilon
                neededevaluations.append(changed)
        elif(self.differencing == Optimizer.Differencing.pure_forward):
            for i in range(len(point)):
                changed = np.copy(point)
                changed[i] += self.finite_differencing_epsilon
                neededevaluations.append(changed)
        elif (self.differencing == Optimizer.Differencing.central):
            for i in range(len(point)):
                changedPos = np.copy(point)
                changedNeg = np.copy(point)
                if point[i] == 0:
                    changedPos[i] = self.finite_differencing_epsilon
                    changedNeg[i] = -self.finite_differencing_epsilon
                else:
                    changedNeg[i] *= 1-self.finite_differencing_epsilon
                    changedPos[i] *= 1+self.finite_differencing_epsilon
                neededevaluations.append(changedPos)
                neededevaluations.append(changedNeg)        
        elif (self.differencing == Optimizer.Differencing.pure_central):
            for i in range(len(point)):
                changedPos = np.copy(point)
                changedNeg = np.copy(point)
                changedNeg[i] -= self.finite_differencing_epsilon
                changedPos[i] += self.finite_differencing_epsilon
                neededevaluations.append(changedPos)
                neededevaluations.append(changedNeg)

        with evaluator:            
            evaluations = evaluator.evaluate(neededevaluations, True, "jacobi-matrix")

        result.log("jacobi matrix calculated. evaluations:")
        
        for ev in evaluations:
            if isinstance(ev, ErroredEvaluation):
                result.log("\tid=" + str(ev.eval_id) + ", " + str(ev.reason))
            else:
                result.log("\tid=" + str(ev.eval_id) + ", timeCount=" + str(ev.timeCount))

        for ev in evaluations:
            if isinstance(ev, ErroredEvaluation):
                # At least one measurement failed
                return None
            
        # get the numpy arrays for the evaluation results
        results = self.measurementToNumpyArrayConverter(evaluations, target)
        undisturbed = results[0]

        # calculate the jacobi matrix
        for i in range(len(point)):
            if(self.differencing == Optimizer.Differencing.forward):
                if point[i] == 0:
                    column = (results[i+1]-undisturbed)/(self.finite_differencing_epsilon)
                else:  
                    column = (results[i+1]-undisturbed)/(self.finite_differencing_epsilon*point[i])
            elif (self.differencing == Optimizer.Differencing.pure_forward):
                column = (results[i+1]-undisturbed)/(self.finite_differencing_epsilon)
            elif (self.differencing == Optimizer.Differencing.central):
                if point[i] == 0:
                    column = (results[2*i+1]-results[2*i+2])/(2*self.finite_differencing_epsilon)
                else:
                    column = (results[2*i+1]-results[2*i+2])/(2*self.finite_differencing_epsilon*point[i])            
            elif (self.differencing == Optimizer.Differencing.pure_central):
                column = (results[2*i+1]-results[2*i+2])/(2*self.finite_differencing_epsilon)
            jacobi.append(column)
        
        return (np.array(jacobi).transpose(), evaluations[0])
    
    @abstractmethod
    def run(self, evaluator, initial_parameters, target, result = Result()):
        pass

