import subprocess
import numpy as np
import os
import time
from UGParameterEstimator import ParameterManager, Evaluation, ParameterOutputAdapter, ErroredEvaluation
from .evaluator import Evaluator

class LocalEvaluator(Evaluator):    
    """Evaluator for usage on PCs without UGSUBMIT.

    Implements the Evaluator AbcstractBaseClass.
    Can use MPI for local speedup, if threadcount > 1 is passed.
    Output of UG4 is redirected into a separate <id>_ug_output.txt file.

    """
    def __init__(self,luafile, directory, parametermanager: ParameterManager, evaluation_type: Evaluation, parameter_output_adapter: ParameterOutputAdapter, fixedparameters={}, threadcount=10, cliparameters = []):
        """Class constructor

        :param luafilename: path to the luafile to call for every evaluation
        :type luafilename: string
        :param directory: directory to use for exchanging data with UG4
        :type directory: string
        :param parametermanager: ParameterManager to transform the parameters/get parameter information
        :type parametermanager: ParameterManager
        :param evaluation_type: TYPE the evaluation shoould be parsed as.
        :type evaluation_type: type implementing Evaluation
        :param parameter_output_adapter: output adapter to write the parameters
        :type parameter_output_adapter: ParameterOutputAdapter
        :param fixedparameters: optional dictionary of fixed parameters to pass
        :type fixedparameters: dictionary<string, string|number>, optional
        :param threadcount: optional maximum number of parallel jobs to submit in UGSUBMIT, defaults to 10
        :type threadcount: int, optional
        :param cliparameters: list of command line parameters to append to subprocess call. use separate entries
                for places that would normally require a space.
        :type cliparameters: list of strings, optional
        """
        self.directory = directory
        self.parametermanager = parametermanager
        self.luafile = luafile
        self.id = 0
        self.fixedparameters = {"output": 0}
        self.fixedparameters.update(fixedparameters)
        self.totalevaluationtime = 0
        self.evaluation_type = evaluation_type
        self.parameter_output_adapter = parameter_output_adapter
        self.threadcount = threadcount
        self.cliparameters = cliparameters

        if not os.path.exists(self.directory):
            os.mkdir(self.directory)
            
        filelist = [ f for f in os.listdir(self.directory)]
        for f in filelist:
            os.remove(os.path.join(self.directory, f))

    @property
    def parallelism(self):
        """Returns the parallelism of the evaluator. here it is one, as only one evaluation is handled in parallel.

        :return: parallelism of the evaluator
        :rtype:  int
        """
        return 1
        
    def evaluate(self, evaluationlist, transform=True, tag=""):
        """Evaluates the parameters given in evaluationlist using UG4, and the adapters set in the constructor.

        :param evaluationlist: parametersets to evaluate
        :type evaluationlist: list of numpy arrays
        :param transform: wether to transform the parameters with parametermanager set in this object, defaults to true
        :type transform: boolean, optional
        :param tag: tag-string attached to all produced evaluations for analysis purposes
        :type tag: string
        :return: list of parsed evaluation objects with the type given in the constructor, or ErroredEvaluation
        :rtype: list of Evaluation
        """        
        results = []

        for beta in evaluationlist:

            if transform is True:
                parameters = self.parametermanager.getTransformedParameters(beta)
                if parameters is None:
                    results.append(ErroredEvaluation(None, reason="Infeasible parameters"))
                    continue
            else:
                parameters = beta

            res = self.checkCache(parameters)

            if res is not None:
                results.append(res)
                continue
                
            starttime = time.time()

            if(self.threadcount > 1):
                callParameters = ["mpirun","-n",str(self.threadcount),"ugshell","-ex",self.luafile, "-evaluationId",str(self.id),"-communicationDir",self.directory]
            else:
                callParameters = ["ugshell","-ex",self.luafile, "-evaluationId",str(self.id),"-communicationDir",self.directory]

            callParameters += self.cliparameters

            # assemble the paths
            stdoutfile = os.path.join(self.directory, str(self.id) + "_ug_output.txt")

            # output the parameters however needed for the application
            self.parameter_output_adapter.writeParameters(self.directory, self.id, self.parametermanager, parameters, self.fixedparameters)
                        
            # call!
            with open(stdoutfile, "w") as outfile:
                subprocess.call(callParameters, stdout=outfile)

            # parse the data, using the provided evaluation type
            data = self.evaluation_type.parse(self.directory, self.id, parameters, time.time()-starttime)

            self.id += 1
        
            if data is None:
                results.append(ErroredEvaluation(parameters, reason="Error while parsing."))
                continue

            self.totalevaluationtime += time.time()-starttime
            self.handleNewEvaluations([data], tag)

            results.append(data)

        return results
    
    def __exit__(self, type, value, traceback):
        # todo: cancel local process?
        pass