from .optimizer import Optimizer
from UGParameterEstimator import ParameterManager, Result, ErroredEvaluation
import numpy as np
import scipy

class ScipyNonlinearLeastSquaresOptimizer(Optimizer):

    def __init__(self, parametermanager: ParameterManager, epsilon=1e-3, differencing=Optimizer.Differencing.forward):
        super().__init__(epsilon, differencing)
        self.parametermanager = parametermanager

    def run(self, evaluator, initial_parameters, target, result = Result()):

        guess = initial_parameters
        

        result.addRunMetadata("target", target)
        result.addRunMetadata("fixedparameters", evaluator.fixedparameters)
        result.addRunMetadata("parametermanager", evaluator.parametermanager)

        result.log("-- Starting scipy optimization. --")

        targetdata = target.getNumpyArray()


        # assemble bounds
        bounds = ([],[])

        for p in self.parametermanager.parameters:

            if p.maximumValue is None:
                bounds[1].append(np.inf)
            else:
                bounds[1].append(p.optimizationSpaceUpperBound/(1+self.finite_differencing_epsilon))
            
            if p.minimumValue is None:
                bounds[0].append(-np.inf)
            else:
                bounds[0].append(p.optimizationSpaceLowerBound)


        # define the callbacks for scipy
        def scipy_fun(x):
            evaluation = evaluator.evaluate([x], True, "function-evaluation")[0]
            if evaluation is None or isinstance(evaluation, ErroredEvaluation):
                result.log("Got a None-Evaluation")
                exit()
            return evaluation.getNumpyArrayLike(target)-targetdata

        def jac_fun(x):
            jacobi_result = self.getJacobiMatrix(x, evaluator, target, result)
            if jacobi_result is None:
                result.log("Error calculating Jacobi matrix, UG run did not finish")
                return

            V, measurementEvaluation = jacobi_result
            return V

        scipy_result = scipy.optimize.least_squares(scipy_fun, guess, jac=jac_fun, bounds=bounds)

        print("point is " + str(scipy_result.x))
        print("cost is " + str(scipy_result.cost))

        result.save()

        return result

    

class ScipyMinimizeOptimizer(Optimizer):

    # opt_method must be one of "L-BFGS-B", "SLSQP" or "TNC"
    def __init__(self, parametermanager, opt_method="SLSQP", epsilon=1e-3, differencing=Optimizer.Differencing.forward):
        super().__init__(epsilon, differencing)
        self.parametermanager = parametermanager
        self.opt_method = opt_method

    def run(self, evaluator, initial_parameters, target, result = Result()):

        guess = initial_parameters

        result.addRunMetadata("target", target)
        result.addRunMetadata("fixedparameters", evaluator.fixedparameters)
        result.addRunMetadata("parametermanager", self.parametermanager)

        result.log("-- Starting scipy optimization. --")

        targetdata = target.getNumpyArray()


        iteration_count = [0]
        last_S = [-1]


        # assemble bounds
        upper = []
        lower = []

        for p in self.parametermanager.parameters:
            
            if p.maximumValue is None:
                upper.append(np.inf)
            else:
                # this is needed to still have some space to do the finite differencing for the jacobi matrix
                upper.append(p.optimizationSpaceUpperBound/(1+self.finite_differencing_epsilon))
            
            if p.minimumValue is None:
                lower.append(-np.inf)
            else:
                lower.append(p.optimizationSpaceLowerBound)

        bounds = scipy.optimize.Bounds(lower, upper)

        # define the callbacks for scipy
        def scipy_function(x):
            result.log("\tEvaluating cost function at x=" + str(x))
            evaluation = evaluator.evaluate([x], True, "function-evaluation")[0]
            if evaluation is None or isinstance(evaluation, ErroredEvaluation):
                result.log("Got a None-Evaluation")
                exit()
            measurement = evaluation.getNumpyArrayLike(target)
            r = measurement-targetdata
            S = 0.5*r.dot(r)
            
            result.addMetric("parameters", x)
            result.addMetric("residualnorm",S)
            result.addMetric("measurement", measurement)
            result.addMetric("measurementEvaluation", evaluation)
            result.addMetric("residuals",r)

            if(last_S[0] != -1):
                result.addMetric("reduction",S/last_S[0])

            last_S[0] = S
            return S

        def scipy_jacobi(x):
            result.log("\tEvaluating jacobi matrix at at x=" + str(x))
            jacobi_result = self.getJacobiMatrix(x, evaluator, target, result)
            if jacobi_result is None:
                result.log("Error calculating Jacobi matrix, UG run did not finish")
                return

            V, measurementEvaluation = jacobi_result
            result.addMetric("jacobian", V)
            V = V.transpose()
            measurement = measurementEvaluation.getNumpyArrayLike(target)
            r = (measurement-targetdata)
            grad = V.dot(r)
            return grad

        def scipy_callback(xk):

            iteration_count[0] += 1

            result.log("[" + str(iteration_count[0]) + "]: parameters=" + str(xk))

            result.commitIteration()
            return False

        scipy_result = scipy.optimize.minimize( fun=scipy_function, x0=guess, jac=scipy_jacobi, 
                                                bounds=bounds, callback=scipy_callback, method=self.opt_method)

        result.log("result is " + str(scipy_result))

        result.save()

        return result
