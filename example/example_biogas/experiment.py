#!/usr/bin/env python3

# import from plugins folder
# please make sure the enivorment variable UG4_ROOT points to your UG4 directory!
import sys
import os
sys.path.append(os.path.join(os.environ["UG4_ROOT"], "plugins", "ParameterEstimation"))
from UGParameterEstimator import *

# specify the parameters
pm = ParameterManager()

# direct parameter: no transformation from parameter used in optimizer to parameter in lua
# the specified value is the initial value used in the optimization
# lower and upper bounds can be supplied as third and fourth argument
pm.addParameter(DirectParameter("operatingTemperature", 280))  # 311.15 K = 38 C
# pm.addParameter(DirectParameter("initialCarbonhydrates", 2.7))  # 2.7
pm.addParameter(DirectParameter("feedingCarbonhydrates", 2.6))  # 0.6
# add parameter acetic
# pm.addParameter(DirectParameter("initialAcetic", 0.0))  # 1.50 g/L

# create the evaluator object. this will create a LocalEvaluator, which uses MPI for parallelism > 1, if no UGSUBMIT was found,
# or an ClusterEvaluator using UGSUBMIT.
evaluator = Evaluator.ConstructEvaluator(
    luafile="Biogas.lua",                   # the lua file to execute for every evaluation
    cliparameters=["-p", "Parameter.lua"],  # additional command line parameters
    directory="evaluations",                # the folder used for data exchange
    parametermanager=pm,                    # the parameters defined above
    evaluation_type=GenericEvaluation,      # the type the evaluations should be parsed as.
    parameter_output_adapter=UG4ParameterOutputAdapter(),       # the adapter to use to write the parameters
    threadcount=1)                          # threads to use locally or when using UGSUBMIT

# create the optimizer
optimizer = GaussNewtonOptimizer(LogarithmicParallelLineSearch(evaluator))

# specify some fixed parameters if needed (could be done in lua, also)
# evaluator.fixedparameters["operatingTemperature"] = 299
evaluator.fixedparameters["realReactorVolume"] = 34.5
evaluator.fixedparameters["initialCarbonhydrates"] = 2.7
evaluator.fixedparameters["initialAcetic"] = 1.5

# parameter to be converged to in line 347 of TimestepOutputOptimizer.lua

# this will do a measurement with fixed parameters
with evaluator:
    target = evaluator.evaluate([np.array([311.15, 0.65927235354573])], transform=False)[0]

# try to restore these parameters by calibration
# store the calibration process and logging in example.pkl
result = Result("example.pkl")
result = optimizer.run(evaluator, pm.getInitialArray(), target, result=result)
