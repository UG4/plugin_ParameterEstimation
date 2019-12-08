import numpy as np
import math
from abc import ABC, abstractmethod
from .evaluation import ErroredEvaluation

class LineSearch(ABC):

    def __init__(self, evaluator):
        self.evaluator = evaluator

    def measurementToNumpyArrayConverter(self, evaluations, target):        
        results = []
        for e in evaluations:
            if e is None or isinstance(e, ErroredEvaluation):
                results.append(None)
            else:
                results.append(e.getNumpyArrayLike(target))
        return results

    @abstractmethod
    def doLineSearch(self, stepdirection, guess, target, J, r, result):
        pass

class LinearParallelLineSearch(LineSearch):

    c = 1e-4                    # c for the wolfe lower bound  
    gamma = 0.5                 # the factor to shrink the observation window in each iteration
    max_iterations = 1         # number of maximum iterations of the line search
    parallel_evaluations = 10   # number of parallel evaluations during the parallel line search

    def __init__(self, evaluator, max_iterations = 1, parallel_evaluations = 10):
        super().__init__(evaluator)
        self.max_iterations = max_iterations
        self.parallel_evaluations = parallel_evaluations


    def doLineSearch(self, stepdirection, guess, target, J, r, result):

        # calculate the gradient at the current point
        grad = J.transpose().dot(r)   

        low = 0                     # current lowest value of the search window
        top = 1                     # current highest value of the search window
        l = 0                       # current interation   
        
        while True:  
            alphas = np.linspace(low,top,num=self.parallel_evaluations)
            evaluations = []
            for i in range(self.parallel_evaluations):           
                evaluations.append(guess+alphas[i]*stepdirection)                         

            with self.evaluator:
                nextevaluations = self.evaluator.evaluate(evaluations, True, "linesearch")

            nextfunctionvalues = self.measurementToNumpyArrayConverter(nextevaluations, target)

            allNone = True
            minnorm = float("inf")
            minindex = -1

            # find the evaluation with lowest residualnorm, and check if all evaluations returned none, i.e. did not finish in UG
            for i in range(self.parallel_evaluations):
                if(nextevaluations[i] is None or isinstance(nextevaluations[i], ErroredEvaluation)):
                    result.log("\t\talpha_" + str(i)+ " = " + str(alphas[i])+" did not finish")
                    continue

                allNone = False

                residualnorm = np.linalg.norm(nextfunctionvalues[i]-target.getNumpyArray())                
               
                result.log("\t\talpha_" + str(i) + " = " + str(alphas[i]) + ", evalid=" + str(nextevaluations[i].eval_id) + ", residual = " + str(residualnorm))  
            
                if(residualnorm  < minnorm):
                    minnorm = residualnorm
                    minindex = i
            
            if(allNone):
                result.log("\t ["+str(l)+"]: no run finished.")
                return None
                
            minindex_alpha = alphas[minindex]

            continue_override = False

            if minindex == self.parallel_evaluations-1:
                continue_override = True
                next_low = top
                next_top = top + (top-low)/2
            elif minindex == 0:
                continue_override = True
                if low == 0:
                    next_low = 0
                    next_top = top/self.parallel_evaluations
                else:
                    next_low = max(0, low - (top-low)/2)
                    next_top = next_low + (top-low)/2
            else:
                next_low = minindex_alpha - (top-low)/4
                next_top = minindex_alpha + (top-low)/4
            
            lowerbound = np.linalg.norm(r) + self.c * minindex_alpha * grad.transpose().dot(stepdirection)
            result.log("\t ["+str(l)+"]: min_alpha = " + str(minindex_alpha) + ", next interval = [" + str(next_low) + ", " + str(next_top) + "], new residualnorm: " + str(minnorm) + ", wolfe lower bound: " + str(lowerbound))
            l += 1


            # do not continue if all iterations reached
            if l == self.max_iterations:
                continue_override = False
                if minindex_alpha == 0:
                    return None

            if(minnorm < lowerbound and not continue_override):
                result.addMetric("alpha",minindex_alpha)
                return guess+minindex_alpha*stepdirection

            low = next_low
            top = next_top
                
            if l == self.max_iterations:
                return guess+minindex_alpha*stepdirection

class LogarithmicParallelLineSearch(LineSearch):
    
    start = -5                # the factor to shrink the observation window in each iteration
    parallel_evaluations = 10   # number of parallel evaluations during the parallel line search
    c = 1e-4 

    def doLineSearch(self, stepdirection, guess, target, J, r, result):

        # calculate the gradient at the current point
        grad = J.transpose().dot(r)   

        evaluations = []
        alphas = np.logspace(self.start, 0, base=2, num=self.parallel_evaluations)
        for i in range(self.parallel_evaluations):          
            evaluations.append(guess+alphas[i]*stepdirection)                         

        with self.evaluator:
            nextevaluations = self.evaluator.evaluate(evaluations, True, "linesearch")

        nextfunctionvalues = self.measurementToNumpyArrayConverter(nextevaluations, target)

        allNone = True
        minnorm = float("inf")
        minindex = -1

        # find the evaluation with lowest residualnorm, and check if all evaluations returned none, i.e. did not finish in UG
        for i in range(self.parallel_evaluations):
            if(nextevaluations[i] is None or isinstance(nextevaluations[i], ErroredEvaluation)):
                result.log("\t\talpha_" + str(i)+ " = " + str(alphas[i]) + " did not finish")
                continue

            allNone = False

            residualnorm = np.linalg.norm(nextfunctionvalues[i]-target.getNumpyArray())

            result.log("\t\talpha_" + str(i) + " = " + str(alphas[i]) + ", evalid=" + str(nextevaluations[i].eval_id) + ", residual = " + str(residualnorm))  
            
            if(residualnorm  < minnorm):
                minnorm = residualnorm
                minindex = i
        
        if(allNone):            
            result.log("\tno run finished.")
            return None
            
        else:
            minindex_alpha = alphas[minindex]

            lowerbound = np.linalg.norm(r) + self.c * minindex_alpha * grad.transpose().dot(stepdirection)
            if minnorm < lowerbound:                
                result.addMetric("alpha",minindex_alpha)
                return guess+minindex_alpha*stepdirection
            else:
                return None
            
class BacktrackingLineSearch(LineSearch):

    # parameters
    c = 1e-4
    rho = 0.5
    max_iterations = 15

    def doLineSearch(self, stepdirection, guess, target, J, r, result):

        # do backtracking line search
        grad = J.transpose().dot(r)   
        alpha = 1
        l = 0

        while True:                 
            nextguess = guess+alpha*stepdirection
            with self.evaluator:            
                nextevaluation = self.evaluator.evaluate([nextguess], True, "linesearch")

            if nextevaluation is None or isinstance(nextevaluation, ErroredEvaluation):
                return None
            
            nextfunctionvalue = self.measurementToNumpyArrayConverter(nextevaluation, target)[0]
            nextresidualnorm = np.linalg.norm(nextfunctionvalue-target.getNumpyArray())

            # wolfe bound
            lowerbound = np.linalg.norm(r) + self.c * alpha * grad.transpose().dot(stepdirection)

            result.log("\t\t ["+str(l)+"]: alpha = " + str(alpha) + ", new residualnorm: " + str(nextresidualnorm) + ", wolfe lower bound: " + str(lowerbound))
            l += 1

            result.addMetric("alpha",alpha)

            if(nextresidualnorm <= lowerbound):
                return nextguess
            alpha = alpha * self.rho

            if(l == self.max_iterations):
                return None