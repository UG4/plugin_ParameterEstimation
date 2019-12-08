from .parameterOutputAdapter import ParameterOutputAdapter
from .parameterManager import ParameterManager
import os

class KeyValueFileParameterOutputAdapter(ParameterOutputAdapter):

    def writeParameters(self, directory: str, evaluation_id: int, parametermanager: ParameterManager, parameter, fixedparameters):
        
        parameterfile = os.path.join(directory, str(evaluation_id) + "_parameters.txt")
        # write the parameter file parsed in lua
        with open(parameterfile,"w") as f:
            for i in range(len(parameter)):
                f.write(parametermanager.parameters[i].name + "=" + str(parameter[i]) + "\n")
            for k in fixedparameters:
                f.write(k + "=" + str(fixedparameters[k]) + "\n")