import subprocess
import os
import io
import time
import csv
from shutil import copyfile
from UGParameterEstimator import ParameterManager, Evaluation, ParameterOutputAdapter, ErroredEvaluation
from .evaluator import Evaluator

class ClusterEvaluator(Evaluator):

    def __init__(self, luafilename, directory, parametermanager: ParameterManager, evaluation_type: Evaluation, parameter_output_adapter: ParameterOutputAdapter, fixedparameters, jobcount):
        self.directory = directory
        self.parametermanager = parametermanager
        self.id = 0
        self.fixedparameters =  {"output": 0}
        self.fixedparameters.update(fixedparameters)
        self.evaluation_type = evaluation_type
        self.parameter_output_adapter = parameter_output_adapter
        self.jobcount = jobcount
        self.jobids = []
        self.luafilename = luafilename
        
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

        filelist = [ f for f in os.listdir(self.directory)]
        for f in filelist:
            os.remove(os.path.join(self.directory, f))

    @property
    def parallelism(self):
        return self.jobcount

    def evaluate(self, evaluationlist, transform=True, tag=""):
        
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

            callParameters = ["ugsubmit",str(self.jobcount),"---","ugshell","-ex",absolute_script_path, "-evaluationId",str(self.id),"-communicationDir",absolute_directory_path]

            evaluationids[j] = self.id

            # output the parameters however needed for the application
            self.parameter_output_adapter.writeParameters(self.directory, self.id, self.parametermanager, beta[j], self.fixedparameters)
            
            self.id += 1

            # submit the job and parse the received id
            process = subprocess.Popen(callParameters, stdout=subprocess.PIPE)
            process.wait()

            for line in io.TextIOWrapper(process.stdout, encoding="UTF-8"):
                if line.startswith("Received job id"):
                    self.jobids[j] = int(line.split(" ")[3])

            # to avoid bugs with the used scheduler on cesari
            time.sleep(1)

        while(True):

            # wait until all jobs are finished
            # for this, call uginfo and parse the output
            process = subprocess.Popen(["uginfo"], stdout=subprocess.PIPE)
            process.wait()
            lines = io.TextIOWrapper(process.stdout, encoding="UTF-8").readlines()
            while True:
                if "JOBID" not in lines[0]:
                    lines.remove(lines[0])
                else:
                    break
            
            reader = csv.DictReader(lines, delimiter=" ", skipinitialspace=True)

            # are all of our jobs finished?
            finished = True

            for row in reader:
                jobid = int(row["JOBID"])
                if((jobid in self.jobids) and (row["STATE"] == "RUNNING" or row["STATE"] == "PENDING")):
                    finished = False
                    break

            if finished:
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
            copyfile("jobid." + str(self.jobids[i]) + "/job.output", stdoutfile)

            results[i] = data

        self.handleNewEvaluations(results, tag)
        self.jobids.clear()

        return results

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):

        # make sure all (of our) jobs are cancelled or finished when the evaluation is finished

        if(not self.jobids):
            return None

        # call uginfo to find out which jobs are still running
        process = subprocess.Popen(["uginfo"], stdout=subprocess.PIPE)
        process.wait()
        lines = io.TextIOWrapper(process.stdout,encoding="UTF-8").readlines()
        while True:
            if "JOBID" not in lines[0]:
                lines.remove(lines[0])
            else:
                break
        
        reader = csv.DictReader(lines, delimiter=" ", skipinitialspace=True)

        for row in reader:
            jobid = int(row["JOBID"])
            if jobid in self.jobids:
                print("Cancelling " + str(jobid))

                # cancel them using ugcancel
                process2 = subprocess.Popen(["ugcancel",str(jobid)], stdout=subprocess.PIPE)
                process2.wait()
