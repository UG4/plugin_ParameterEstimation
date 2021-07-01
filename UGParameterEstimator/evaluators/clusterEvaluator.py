import subprocess
import os
import io
import time
import csv
from shutil import copyfile
from UGParameterEstimator import ParameterManager, Evaluation, ParameterOutputAdapter, ErroredEvaluation
from .evaluator import Evaluator
from .schedulingAdapter import SchedulingAdapter
from .ugsubmitSlurmSchedulingAdapter import UGSubmitSlurmSchedulingAdapter

class ClusterEvaluator(Evaluator):
    """Evaluator for Clusters supporting UGSUBMIT.

    Implements the Evaluator AbcstractBaseClass.
    Calls UGSUBMIT and UGINFO using the subprocess module to schedule tasks and get infos about them.

    Implements a handler to catch unexpected program interruption while evaluating (for example, if the user
    cancels the operation). In this case, all open jobs will be cancelled.

    Output of UG4 is redirected into a separate <id>_ug_output.txt file.

    """
    def __init__(self, luafilename, directory, parametermanager: ParameterManager, evaluation_type, parameter_output_adapter: ParameterOutputAdapter, scheduling_adapter: SchedulingAdapter, fixedparameters={}, cliparameters = []):
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
        :param scheduling_adapter: scheduling adapter to allow for usage on multiple different job scheduling systems
        :type scheduling_adapter: SchedulingAdapter
        :param fixedparameters: optional dictionary of fixed parameters to pass
        :type fixedparameters: dictionary<string, string|number>, optional
        :param threadcount: optional maximum number of threads per job in UGSUBMIT, defaults to 10
        :type threadcount: int, optional
        :param cliparameters: list of command line parameters to append to subprocess call. use separate entries
                for places that would normally require a space.
        :type cliparameters: list of strings, optional

        """
        self.directory = directory
        self.parametermanager = parametermanager
        self.id = 0
        self.fixedparameters =  {"output": 0}
        self.fixedparameters.update(fixedparameters)
        self.evaluation_type = evaluation_type
        self.parameter_output_adapter = parameter_output_adapter
        
        self.jobids = []
        self.luafilename = luafilename
        self.cliparameters = cliparameters
        self.scheduling_adapter = scheduling_adapter
        
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

        filelist = [ f for f in os.listdir(self.directory)]
        for f in filelist:
            os.remove(os.path.join(self.directory, f))

    @property
    def parallelism(self):        
        """Returns the parallelism of the evaluator

        :return: parallelism of the evaluator
        :rtype:  int
        """
        return self.threadcount

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
        results = [None] * len(evaluationlist)
        self.jobids = [None] * len(evaluationlist)
        evaluationids = [None] * len(evaluationlist)
        beta = [None] * len(evaluationlist)
        starttimes = [None] * len(evaluationlist)

        for j in range(len(evaluationlist)):

            beta_j = evaluationlist[j]

            if transform:
                beta[j] = self.parametermanager.getTransformedParameters(beta_j)
                if beta[j] is None:
                    results[j] = ErroredEvaluation(None, reason="Infeasible parameters")
            else:
                beta[j] = beta_j

            if results[j] is None:
                results[j] = self.checkCache(beta[j])

        for j in range(len(evaluationlist)):

            if results[j] is not None:                
                continue

            starttimes[j] = time.time()

            absolute_directory_path = os.getcwd() + "/" + self.directory
            absolute_script_path = os.getcwd() + "/" + self.luafilename

            if not os.path.isfile(absolute_script_path):
                print("Luafile not found! " + absolute_script_path)
                exit()
            if not os.path.exists(absolute_directory_path):
                print("Exchange directory not found! " + absolute_directory_path)
                exit()
            
            parameters = ["-evaluationId",str(self.id),"-communicationDir",absolute_directory_path]
            parameters += self.cliparameters

            evaluationids[j] = self.id 
            self.id += 1 

            # output the parameters however needed for the application
            self.parameter_output_adapter.writeParameters(self.directory, self.id, self.parametermanager, beta[j], self.fixedparameters)
            self.jobids[j] = self.schedulingAdapter.scheduleJob()         

        while(True):

            jobs_running_or_pending = self.scheduling_adapter.anyStillPendingOrRunning(self.jobids)

            if not jobs_running_or_pending:
                break

            time.sleep(5)


        # now we can parse the measurement files
        for i in range(len(evaluationlist)):

            if results[i] is not None:
                continue

            # parse the result
            data = self.evaluation_type.parse(self.directory, evaluationids[i], beta[i], time.time()-starttimes[i])

            # preserve the association between the ugoutput and th einternal avaluation id.
            # this allows for better debugging
            stdoutfile = os.path.join(self.directory, str(evaluationids[i]) + "_ug_output.txt")
            try:
                copyfile("jobid." + str(self.jobids[i]) + "/job.output", stdoutfile)
            except:
                print("Could not copy job output. Was it moved?")

            results[i] = data

        self.handleNewEvaluations(results, tag)
        self.jobids.clear()

        return results

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):

        # make sure all (of our) jobs are cancelled or finished when the evaluation is finished

        if not self.jobids:
            return None

        self.scheduling_adapter.cancelJobs(self.jobids)