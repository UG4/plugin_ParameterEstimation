import numpy as np
import os
from abc import ABC, abstractmethod

class Evaluation(ABC):

    parameters = None
    eval_id = None
    runtime = None

    @abstractmethod
    def getNumpyArray(self):
        pass

    @abstractmethod
    def getNumpyArrayLike(self, target):
        pass

    @classmethod
    @abstractmethod
    def parse(cls, directory, evaluation_id, parameters, eval_id, runtime):
        pass
    
    class IncompatibleFormatError(Exception):
        pass

class ErroredEvaluation(Evaluation):

    def __init__(self, parameters, reason, eval_id=None, runtime=None):
        self.parameters = parameters
        self.eval_id = eval_id
        self.runtime = runtime
        self.reason = reason

    def getNumpyArray(self):
        pass

    def getNumpyArrayLike(self, target: Evaluation):
        pass

    @classmethod
    def parse(cls, directory, evaluation_id, parameters, eval_id, runtime):
        pass
    