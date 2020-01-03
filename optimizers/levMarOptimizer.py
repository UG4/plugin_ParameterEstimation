from .optimizer import Optimizer
from UGParameterEstimator import LineSearch, Result
import numpy as np
from scipy import stats

class LevMarOptimizer(Optimizer):
        
    def __init__(self, linesearchmethod: LineSearch, maxiterations = 15, initial_lam = 0.01, nu=10, scaling=False, epsilon=1e-3, minreduction=1e-4,max_error_ratio=(0.05,0.95), differencing=Optimizer.Differencing.forward):
        super().__init__(epsilon, differencing)
        self.linesearchmethod = linesearchmethod
        self.maxiterations = maxiterations
        self.minreduction = minreduction
        self.max_error_ratio = max_error_ratio
        self.nu = nu
        self.initial_lam = initial_lam
        self.scaling = scaling

    def calculateDelta(self, V, r, p, lam):

        scaling = self.scaling

        # calculate Lev-Mar step direction  (p.7)
        A = V.transpose().dot(V)
        g = V.transpose().dot(r)
        
        AStar = np.copy(A)
        gStar = np.copy(g)

        if scaling:
            for x in range(p):
                for y in range(p):
                    AStar[x,y] = A[x,y] / (np.sqrt(A[x,x])*np.sqrt(A[y,y]))
                gStar[x] = g[x] / np.sqrt(A[x,x])
        
        print(AStar)
        M = AStar + lam*np.diag(np.ones(p))
        print(M)
        Q,R = np.linalg.qr(M)
        w = Q.transpose().dot(g)
        deltaStar = -np.linalg.solve(R, w)
        delta = np.copy(deltaStar)
        if scaling:
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

            print(V)

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
          
            
            delta_lower_lam = self.calculateDelta(V,r,p,lam/self.nu)
            delta_prev_lam = self.calculateDelta(V,r,p,lam)
            delta_higher_lam = self.calculateDelta(V,r,p,lam*self.nu)

            result.log("["+str(i) + "]\tStarting line search for lam = " + str(lam/self.nu))
            nextguess_lower_lam, S_lower_lam = self.linesearchmethod.doLineSearch(delta_lower_lam, guess, target, V, r, result)
            result.log("["+str(i) + "]\tStarting line search for lam = " + str(lam))
            nextguess_prev_lam, S_prev_lam = self.linesearchmethod.doLineSearch(delta_prev_lam, guess, target, V, r, result)
            result.log("["+str(i) + "]\tStarting line search for lam = " + str(lam*self.nu))
            nextguess_higher_lam, S_higher_lam = self.linesearchmethod.doLineSearch(delta_higher_lam, guess, target, V, r, result)

            if S_lower_lam is not None and S_lower_lam <= last_S:
                lam = lam/self.nu
                S = S_lower_lam
                nextguess = nextguess_lower_lam
            elif S_lower_lam is not None and S_prev_lam is not None and S_lower_lam > last_S and S_prev_lam <= last_S:
                S = S_prev_lam
                nextguess = nextguess_prev_lam
            elif S_higher_lam is not None and S_higher_lam > last_S:
                lam = lam*self.nu
                S = S_higher_lam
                nextguess = nextguess_higher_lam                
            else:
                for z in range(3):
                    lam = lam*self.nu
                    delta = self.calculateDelta(V,r,p,lam)
                    result.log("["+str(i) + "]\tStarting line search for lam = " + str(lam))
                    nextguess, S = self.linesearchmethod.doLineSearch(delta, guess, target, V, r, result)
                    if S is not None and S < last_S:
                        break
                else:
                    result.log("-- Levenberg-Marquardt method did not converge. --")
                    result.commitIteration()
                    result.log(evaluator.getStatistics())
                    result.save()
                    return result

            result.log("["+str(i) + "]\t best lam was = " + str(lam) + " with f=" + str(S))

            # cancel the optimization when the reduction of the norm of the residuals is below the threshhold
            if (S/first_S < self.minreduction):
                result.log("-- Levenberg-Marquardt method converged. --")
                result.commitIteration()
                break
                        
            result.commitIteration()

            guess = nextguess
            last_S = S

        if(i == self.maxiterations-1):
            result.log("-- Levenberg-Marquardt method did not converge. --")
        
        result.log(evaluator.getStatistics())
        result.save()
        return result