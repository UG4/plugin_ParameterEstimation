
import subprocess
import time
import io
import csv
from .evaluator import Evaluator
from .schedulingAdapter import SchedulingAdapter

class UGSubmitQStatSchedulingAdapter(SchedulingAdapter):

    def __init__(self, jobcount, ugsubmitparameters):

        self.jobcount = jobcount
        self.ugsubmitparameters = ugsubmitparameters

    def scheduleJob(self, script_path, ugshell_parameters):
        """Schedules a Job.

        :param ugshell_parameters: command line parameters to pass to ugshell
        :type res: List of Strings; alternating between name of parameter and value
        :return: the ID of the job
        :rtype: String
        """
        callParameters = ["ugsubmit",str(self.jobcount)]

        callParameters += self.ugsubmitparameters
        
        callParameters += ["---","ugshell","-ex", script_path]

        callParameters += ugshell_parameters

        # submit the job and parse the received id
        process = subprocess.Popen(callParameters, stdout=subprocess.PIPE)
        process.wait()

        # to avoid bugs with the used scheduler on cesari
        time.sleep(1)

        for line in io.TextIOWrapper(process.stdout, encoding="UTF-8"):
            if line.startswith("Received job id"):
                return int(line.split(" ")[3])

        raise Evaluator.IncompatibleFormatError("JobID not found in ugsubmit output!")

    def getRunningOrPendingJobs(self):
        """Get a list of running or pending jobs

        :return: the ids of the jobs that are running or pending
        :rtype: List of String
        """

        result = []

        process = subprocess.Popen(["uginfo"], stdout=subprocess.PIPE)
        process.wait()
        lines = io.TextIOWrapper(process.stdout, encoding="UTF-8").readlines()
        while True:
            if len(lines) == 0:
                raise Evaluator.IncompatibleFormatError("JOBID Table not found")
            if "JOBID" not in lines[0]:
                lines.remove(lines[0])
            else:
                break
        
        reader = csv.DictReader(lines, delimiter=" ", skipinitialspace=True)

        for row in reader:
            if "JOBID" not in row:
                raise Evaluator.IncompatibleFormatError("Job table has wrong format! Field JOBID not found.")
            if "STATUS" not in row:
                raise Evaluator.IncompatibleFormatError("Job table has wrong format! Field STATUS not found.")
            jobid = int(row["JOBID"])
            if row["STATE"] == "RUNNING" or row["STATE"] == "PENDING":
                result.append(jobid)

        return result

    def cancelJob(self, jobid):        
        """Cancels a single Job, given a job id.

        :param jobid: id of the job to cancel
        :type res: String
        """

        print("Cancelling " + str(jobid))
        # cancel job using ugcancel
        process2 = subprocess.Popen(["ugcancel",str(jobid)], stdout=subprocess.PIPE)
        process2.wait()
        