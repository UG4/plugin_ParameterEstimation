import subprocess
import numpy as np
import os
import time
from UGParameterEstimator import *
from .evaluator import Evaluator

class LocalEvaluator(Evaluator):
    def __init__(self,luafile, directory, parametermanager: ParameterManager, evaluation_type: Evaluation, parameter_output_adapter: ParameterOutputAdapter, fixedparameters, threadcount):
        self.directory = directory
        self.parametermanager = parametermanager
        self.luafile = luafile
        self.id = 0
        self.fixedparameters = {"output": "0"}
        self.fixedparameters.update(fixedparameters)
        self.totalevaluationtime = 0
        self.evaluation_type = evaluation_type
        self.parameter_output_adapter = parameter_output_adapter
        self.threadcount = threadcount

        if not os.path.exists(self.directory):
            os.mkdir(self.directory)
            
        filelist = [ f for f in os.listdir(self.directory)]
        for f in filelist:
            os.remove(os.path.join(self.directory, f))

    @property
    def parallelism(self):
        return self.threadcount
        
    def evaluate(self, evaluationlist, transform=True, tag=""):
        
        results = []

        for beta in evaluationlist:

            if transform is True:
                parameters = self.parametermanager.getTransformedParameters(beta)
                if parameters is None:
                    results.append(None)
                    continue
            else:
                parameters = beta
                if np.min(parameters) < 0:
                    results.append(None)
                    continue 
                
            starttime = time.time()

            callParameters = ["mpirun","-n",str(self.threadcount),"ugshell","-ex",self.luafile, "-evaluationId",str(self.id),"-communicationDir",self.directory]

            # assemble the paths
            stdoutfile = os.path.join(self.directory, str(self.id) + "_ug_output.txt")

            # output the parameters however needed for the application
            self.parameter_output_adapter.writeParameters(self.directory, self.id, self.parametermanager, parameters, self.fixedparameters)
                        
            with open(stdoutfile, "w") as outfile:
                subprocess.call(callParameters, stdout=outfile)

            data = self.evaluation_type.parse(self.directory, self.id, parameters, time.time()-starttime)

            self.id += 1
        
            if data is None:
                results.append(None)
                continue

            self.totalevaluationtime += time.time()-starttime
            self.evaluation_count += 1
            self.handleNewEvaluations([data], tag)

            results.append(data)

        return results

    def __enter__(self):
        pass
    
    def __exit__(self, type, value, traceback):
        pass