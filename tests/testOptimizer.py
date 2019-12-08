import sys, os
import numpy as np
from UGParameterEstimator import *
from testEvaluator import *
from skopt.plots import plot_evaluations


pm = ParameterManager()
pm.addParameter(DirectParameter("x1", 1.0, 0, 10))
pm.addParameter(DirectParameter("x2", 5.0, 0, 10))

result = Result("results_newton.pkl")
evaluator = TestEvaluator(pm, result)

optimizer = GaussNewtonOptimizer(LinearParallelLineSearch(evaluator))

with evaluator:
    target = evaluator.evaluate([np.array([2.0,3.0])], transform=False, tag="target")[0]

result = optimizer.run(evaluator, pm.getInitialArray(), target, result=result)

print("This took " + str(evaluator.evaluation_count) +  " evaluations.")
evaluator.evaluation_count = 0

result = Result("results_scipy.pkl")


optimizer = ScipyMinimizeOptimizer(pm)
optimizer.run(evaluator, pm.getInitialArray(), target, result=result)


print("This took " + str(evaluator.evaluation_count) +  " evaluations.")
evaluator.evaluation_count = 0
