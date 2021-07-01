from abc import ABC, abstractmethod

class SchedulingAdapter(ABC):

    @abstractmethod
    def scheduleJob(self, script_path, ugshell_parameters) -> str:
        """Schedules a Job.

        :param ugshell_parameters: command line parameters to pass to ugshell
        :type res: List of Strings; alternating between name of parameter and value
        :return: the ID of the job
        :rtype: String
        """
        pass

    def cancelJobs(self, jobids):
        """Cancels Jobs, given a list of ids.

        :param jobid: ids of the jobs to cancel
        :type res: List of Strings
        """
        running_or_pending = self.getRunningOrPendingJobs()
        running_or_pending = list(set(running_or_pending).intersection(jobids))

        for jobid in running_or_pending:
            self.cancelJob(jobid)

    @abstractmethod
    def cancelJob(self, jobid):        
        """Cancels a single Job, given a job id.

        :param jobid: id of the job to cancel
        :type res: String
        """
        pass
    
    @abstractmethod
    def getRunningOrPendingJobs(self) -> list(str):
        """Get a list of running or pending jobs

        :return: the ids of the jobs that are running or pending
        :rtype: List of String
        """
        pass
    
    def anyStillPendingOrRunning(self, jobids) -> bool:
        """Returns true if any of the jobs with ids in jobids are still running or waiting to be scheduled.

        :param jobid: ids of the jobs to get the status of
        :type res: List of Strings
        :return: true, if a job is still pending or running
        :rtype: Boolean
        """
        running_or_pending = self.getRunningOrPendingJobs()
        running_or_pending = list(set(running_or_pending).intersection(jobids))
        return len(running_or_pending) > 0