#!/usr/bin/env python3

from UGParameterEstimator import *

# specify the parameters
pm = ParameterManager()
pm.addParameter(DirectParameter("permeability", 1e-10))
pm.addParameter(DirectParameter("porosity", 0.2))

# create the evaluator object, can be ClusterEvaluator for work on ugsubmit/uginfo-Clusters, 
# or LocalEvaluator which will use mpi for parallelism
evaluator = LocalEvaluator(luafile="evaluate.lua", directory="evaluations", 
                        parametermanager=pm, evaluation_type=FreeSurfaceTimeDependentEvaluation, 
                        parameter_output_adapter=KeyValueFileParameterOutputAdapter(), 
                        fixedparameters={}, threadcount=10)

optimizer = GaussNewtonOptimizer(LinearParallelLineSearch(evaluator))

# specify some fixed parameters if needed (could be done in lua, also)
evaluator.fixedparameters["inflow"] = 0.0001
evaluator.fixedparameters["stoptime"] = 10
evaluator.fixedparameters["numberOfMeasurementPoints"] = 9

# this will do a measurement with fixed parameters
with evaluator:
    target = evaluator.evaluate([np.array([1e-11, 0.1])], transform=False)[0]

# try to restore these parameters by calibration
result = Result("example.pkl")
result = optimizer.run(evaluator, pm.getInitialArray(), target, result=result)
