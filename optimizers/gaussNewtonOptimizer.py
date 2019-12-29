from .optimizer import Optimizer
from UGParameterEstimator import LineSearch, Result
import numpy as np
from scipy import stats

class GaussNewtonOptimizer(Optimizer):
        
    def __init__(self, linesearchmethod: LineSearch, maxiterations = 15, epsilon=1e-4, minreduction=1e-4,max_error_ratio=(0.05,0.95), differencing=Optimizer.Differencing.forward):
        super().__init__(epsilon, differencing)
        self.linesearchmethod = linesearchmethod
        self.maxiterations = maxiterations
        self.minreduction = minreduction
        self.max_error_ratio = max_error_ratio

    def run(self, evaluator, initial_parameters, target, result = Result()):

        guess = initial_parameters

        evaluator.resultobj = result    

        result.addRunMetadata("target", target)
        result.addRunMetadata("epsilon", self.finite_differencing_epsilon)
        result.addRunMetadata("differencing", self.differencing)
        result.addRunMetadata("fixedparameters", evaluator.fixedparameters)
        result.addRunMetadata("parametermanager", evaluator.parametermanager)

        result.log("-- Starting newton method. --")

        targetdata = target.getNumpyArray()

        last_S = -1
        first_S = -1

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

            result.log("[" + str(i) + "]: x=" + str(guess) + ", residual norm S=" + str(S))
          
            # calculate Gauss-Newton step direction (p. 40)
            Q1, R1 = np.linalg.qr(V, mode='reduced')
            w = Q1.transpose().dot(r)
            delta = -np.linalg.solve(R1, w)

            result.log("stepdirection is " + str(delta))

            # approximation of the hessian (X^T * X)^-1 = (R1^T * R1)^-1
            hessian = np.linalg.inv(np.matmul(np.transpose(R1), R1))
            covariance_matrix = variance*hessian
            
            result.addMetric("covariance", covariance_matrix)
            result.addMetric("hessian", hessian)

            # construct correlation matrix (see p. 22 of Bates/Watts)
            R1inv = np.linalg.inv(R1)
            Dinv = np.diag(1/np.sqrt(np.diag(hessian)))
            L = np.matmul(Dinv,R1inv)
            C = np.matmul(L,np.transpose(L))
            result.addMetric("correlation", C)       

            # calculate standard error for the parameters (p.21)
            s = np.sqrt(variance)
            errors = s*np.linalg.norm(R1inv, axis=1)
            result.addMetric("errors", errors)

            if self.max_error_ratio is not None:
                # calculate confidence interval using the errors
                confidenceinterval = stats.t.ppf((1+self.max_error_ratio[1])/2, dof)*errors
                result.addMetric("confidenceinterval", confidenceinterval)


            # cancel the optimization when the reduction of the norm of the residuals is below the threshhold and 
            # the confidence of the calibrated parameters is sufficiently low
            if(S/first_S < self.minreduction and (self.max_error_ratio is None or np.max(np.divide(confidenceinterval, guess)) < self.max_error_ratio[0])):
                result.log("-- Newton method converged. --")
                result.commitIteration()
                break
            
            # do linesearch in the gauss-newton search direction
            nextguess = self.linesearchmethod.doLineSearch(delta, guess, target, V, r, result)

            if(nextguess is None):
                result.log("-- Newton method did not converge. --")
                result.commitIteration()
                result.log(evaluator.getStatistics())
                result.save()
                return result
            
            result.commitIteration()

            guess = nextguess
            last_S = S

        if(i == self.maxiterations-1):
            result.log("-- Newton method did not converge. --")
        
        result.log(evaluator.getStatistics())
        result.save()
        return result