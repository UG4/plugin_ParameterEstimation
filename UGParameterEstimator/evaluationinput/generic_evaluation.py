from .evaluation import Evaluation, ErroredEvaluation
import numpy as np
import math
import os
import json

class GenericEvaluation(Evaluation):
    """Class implementing a parser for evaluations containing only one
    scalar value at multiple timesteps, stored in the following json format:

    .. code-block:: json

        {
            "metadata": {
                "finished": true
            },
            "data": [
                {
                    "time": 0.1,
                    "value": 0.35
                },
                {
                    "time": 0.2,
                    "value": 0.34
                }
                ....
            ]
        }

    """

    data = []
    times = []

    def __init__(self, data, times, eval_id=-1, parameters=None, runtime=None):
        """ Class constructor

        :param data: 1d array of numbers representing the measured for each timestep
        :type data: list of numbers
        :param times: the times measured (in simulation time)
        :type times: list of numbers
        :param eval_id: id of the evaluation this data resulted from
        :type eval_id: int, optional
        :param parameters: (transformed) parameters of the evaluation this data resulted from
        :type parameters: numpy array, optional
        :param runtime: runtime of the evaluation this data resulted from, in seconds
        :type runtime: int, optional
        """ 
        self.data = data
        self.times = times
        self.eval_id = eval_id
        self.parameters = parameters
        self.runtime = runtime

    @property
    def timeCount(self):
        """Returns the number of measurements stored in this object

        :return: Number of measurements stored in this object
        :rtype: Integer
        """
        return len(self.times)

    def getNumpyArray(self):        
        """Returns stored measurements as a 1d numpy array

        :return: stored measurements as a 1d numpy array
        :rtype: numpy array, 1d
        """
        return np.array(self.data)

    
    def getNumpyArrayLike(self, target):
        """Used to interpolate between different evaluations, when timestamps might differ because
        of the used time control schemes.

        :param target: Evaluation whichs format should be matched and interpolated to
        :type target: Evaluation
        :raises IncompatibleFormatError: When the two Evaluations can not be interpolated between
        :return: the data of this evaulation, interpolated to the targets format
        :rtype: numpy array
        """
        
        if not isinstance(target, GenericEvaluation):
            raise Evaluation.IncompatibleFormatError("Target not compatible!")

        array = np.zeros(target.timeCount)
        for i in range(target.timeCount):
            targettime = target.times[i]

            # find nearest entries in this instances time list
            nearest_lower = 0

            # first, find the time with the maximum index lower or equal to targettime
            while True:
                if self.times[nearest_lower] == targettime:
                    # found a perfect match!
                    array[i] = self.data[nearest_lower]
                    break

                if nearest_lower == self.timeCount-1:
                    # at the edge...
                    array[i] = self.data[nearest_lower]
                    break

                if self.times[nearest_lower] < targettime:
                    if self.times[nearest_lower+1] > targettime:
                        # found it
                        # interpolate
                        higherdata = np.array(self.data[nearest_lower+1])
                        highertime = self.times[nearest_lower+1]
                        lowerdata = np.array(self.data[nearest_lower])
                        lowertime = self.times[nearest_lower]

                        percentage = ((targettime-lowertime) / (highertime-lowertime))
                        interpolated = percentage*higherdata + (1-percentage)*lowerdata

                        array[i] = interpolated
                        break
                    else:
                        nearest_lower += 1

                # if we are here, self.times[nearest_lower] > targettime....
                if nearest_lower == 0:
                    array[i] = self.data[nearest_lower]
                    break
                    
        return array
    
    @classmethod
    def fromJSON(cls, filename,  evaluation_id=-1, parameters=None, runtime=None):
        """Parses this evaluation from the json format described

        :param filename: file to parse
        :type filename: string
        :param evaluation_id: id of the evaluation this data resulted from
        :type evaluation_id: int, optional
        :param parameters: (transformed) parameters of the evaluation this data resulted from
        :type parameters: numpy array, optional
        :param runtime: runtime of the evaluation this data resulted from, in seconds
        :type runtime: int, optional
        :return: the parsed evaluation, or ErroredEvaluation if an error occurred.
        :rtype: Evaluation
        """
        # parse the file
        parsedjson = {}
        with open(filename) as jsonfile:
            try:
                parsedjson = json.load(jsonfile)
            except json.JSONDecodeError as exception:
                return ErroredEvaluation(parameters, "Error parsing json file: " + exception.msg, evaluation_id, runtime)
        
        # check correct format
        if("data" not in parsedjson
            or "metadata" not in parsedjson
            or "finished" not in parsedjson["metadata"]):
            return ErroredEvaluation(parameters, "Evaluation json is malformed.", evaluation_id, runtime)

        # check that the evaluation did finish correctly
        if not parsedjson["metadata"]["finished"]:
            return ErroredEvaluation(parameters, "Evaluation did not finish correctly", evaluation_id, runtime)
        
        parsedevaluation = cls([], [], evaluation_id, parameters, runtime)

        # parse data into internal arrays
        for element in parsedjson["data"]:
            if "value" not in element or "time" not in element:
                return ErroredEvaluation(parameters, "Malformed data entry!", evaluation_id, runtime)
            parsedevaluation.data.append(element["value"])
            parsedevaluation.times.append(element["time"])

        return parsedevaluation


    @classmethod
    def parse(cls, directory, evaluation_id, parameters=None, runtime=None):
        """Factory method, parses the evaluation with a given id from the given folder.
        Sets the parameters and runtime as metaobjects for later analysis.

        :param directory: directory to read the evaluation from
        :type directory: string
        :param evaluation_id: id of the evaluation to find the correct file fron directory
        :type evaluation_id: int
        :param parameters: the (transformed) parameters of this evaluation
        :type parameters: numpy array
        :param runtime: runtime of the evaluation, in seconds
        :type runtime: int
        :return: Parsed Evaluation
        :rtype: Evaluation
        """

        # construct filename
        filenameJson = os.path.join(directory, str(evaluation_id) + "_measurement.json")

        if not os.path.isfile(filenameJson):
            return ErroredEvaluation(parameters, "No measurement file found.", evaluation_id, runtime)
        
        return GenericEvaluation.fromJSON(filenameJson, evaluation_id, parameters, runtime)

        