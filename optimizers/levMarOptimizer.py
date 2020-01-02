from .optimizer import Optimizer
from UGParameterEstimator import LineSearch, Result
import numpy as np
from scipy import stats

class LevMarOptimizer(Optimizer):
        
    def __init__(self, linesearchmethod: LineSearch, maxiterations = 15, initial_lam = 0.1, nu=10, epsilon=1e-3, minreduction=1e-4,max_error_ratio=(0.05,0.95), differencing=Optimizer.Differencing.forward):
        super().__init__(epsilon, differencing)
        self.linesearchmethod = linesearchmethod
        self.maxiterations = maxiterations
        self.minreduction = minreduction
        self.max_error_ratio = max_error_ratio
        self.nu = nu
        self.initial_lam = initial_lam

    def calculateDelta(self, V, r, p, lam):
        # calculate Lev-Mar step direction  (p.7)
        A = V.transpose().dot(V)
        g = V.transpose().dot(r)
        
        AStar = np.array_like(A)
        gStar = np.array_like(g)

        for x in range(p):
            for y in range(p):
                AStar[x,y] = A[x,y] / (np.sqrt(A[x,x])*np.sqrt(A[y,y]))
            gStar[x] = g / np.sqrt(A[x,x])

        M = AStar + lam*np.diag(np.ones(p))
        Q,R = np.linalg.qr(M)
        w = Q.transpose().dot(g)
        deltaStar = -np.linalg.solve(R, w)
        delta = np.array_like(deltaStar)
        for x in range(p):
            delta[x] = deltaStar[x] / np.sqrt(A[x,x])

        return delta

    def run(self, evaluator, initial_parameters, target, result = Result()):

        guess = initial_parameters

        evaluator.resultobj = result    

        result.addRunMetadata("target", target)
        result.addRunMetadata("optimizertype", type(self).__name__)
        result.addRunMetadata("linesearchmethod", type(self.linesearchmethod).__name__)
        result.addRunMetadata("epsilon", self.finite_differencing_epsilon)
        result.addRunMetadata("differencing", self.differencing.value)
        result.addRunMetadata("lambda_init", self.initial_lam)
        result.addRunMetadata("nu", self.nu)
        result.addRunMetadata("fixedparameters", evaluator.fixedparameters)
        result.addRunMetadata("parametermanager", evaluator.parametermanager)

        result.log("-- Starting Levenberg-Marquardt method. --")

        targetdata = target.getNumpyArray()

        last_S = -1
        first_S = -1
        lam = self.initial_lam

        for i in range(self.maxiterations):

            jacobi_result = self.getJacobiMatrix(guess, evaluator, target, result)
            if jacobi_result is None:
                result.log("Error calculating Jacobi matrix, UG run did not finish")
                result.log(evaluator.getStatistics())
                result.save()
                return

            V, measurementEvaluation = jacobi_result
            measurement = measurementEvaluation.getNumpyArrayLike(target)

            r = measurement-targetdata

            S = 0.5*r.dot(r)

            # save the residualnorm S for calculation of the relative reduction
            if first_S == -1:
                first_S = S

            n = len(targetdata)
            p = len(guess)
            dof = n-p

            # calculate s^2 = residual mean square / variance estimate (p.6 Bates/Watts)
            variance = S/dof

            result.addMetric("residuals",r)
            result.addMetric("residualnorm",S)
            result.addMetric("parameters",guess)
            result.addMetric("jacobian", V)
            result.addMetric("variance", variance)
            result.addMetric("measurement", measurement)
            result.addMetric("measurementEvaluation", measurementEvaluation)

            if(last_S != -1):
                result.addMetric("reduction",S/last_S)

            result.log("[" + str(i) + "]: x=" + str(guess) + ", residual norm S=" + str(S) + ", lambda=" + str(lam))
          
            
            pointI = guess + self.calculateDelta(V,r,p,lam/self.nu)
            pointII = guess + self.calculateDelta(V,r,p,lam)
            
            evals = evaluator.evaluate([pointI, pointII])

            result.log("stepdirection is " + str(delta))

            evals = []

            # cancel the optimization when the reduction of the norm of the residuals is below the threshhold
            if (S/first_S < self.minreduction):
                result.log("-- Levenberg-Marquardt method converged. --")
                result.commitIteration()
                break
            
            # do linesearch in the descent direction
            nextguess = self.linesearchmethod.doLineSearch(delta, guess, target, V, r, result)

            if(nextguess is None):
                result.log("-- Levenberg-Marquardt method did not converge. --")
                result.commitIteration()
                result.log(evaluator.getStatistics())
                result.save()
                return result
            
            result.commitIteration()

            guess = nextguess
            last_S = S
            lam *= self.reduction_lam

        if(i == self.maxiterations-1):
            result.log("-- Levenberg-Marquardt method did not converge. --")
        
        result.log(evaluator.getStatistics())
        result.save()
        return result