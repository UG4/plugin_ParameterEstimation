import sys, os
import numpy as np
from UGParameterEstimator import *
from testEvaluator import *
from skopt.plots import plot_evaluations


pm = ParameterManager()
pm.addParameter(DirectParameter("x1", -1.2, -5, 10))
pm.addParameter(DirectParameter("x2", 1, 0, 10))

result = Result("results_newton.pkl")
evaluator = TestEvaluator(pm, result)

optimizer = GainedLevMarOptimizer()

with evaluator:
    target = evaluator.evaluate([np.array([1.0,1.0])], transform=False, tag="target")[0]

result = optimizer.run(evaluator, pm.getInitialArray(), target, result=result)

print(evaluator)
evaluator.reset()

# optimizer = GaussNewtonOptimizer(LinearParallelLineSearch(evaluator, 1))

# with evaluator:
#     target = evaluator.evaluate([np.array([2.0,3.0])], transform=False, tag="target")[0]

# result = optimizer.run(evaluator, pm.getInitialArray(), target, result=result)

# print(evaluator)
# evaluator.reset()

# optimizer = GradientDescentOptimizer(LinearParallelLineSearch(evaluator))

# with evaluator:
#     target = evaluator.evaluate([np.array([2.0,3.0])], transform=False, tag="target")[0]

# result = optimizer.run(evaluator, pm.getInitialArray(), target, result=result)

# print(evaluator)