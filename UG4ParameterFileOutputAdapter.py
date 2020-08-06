from .parameterOutputAdapter import ParameterOutputAdapter
from .parameterManager import ParameterManager
import json
import os

# Writes the Parameters to calibrate and all fixed parameters to a JSON file understandable by UG4
# This means the parameters can be referenced in Lua files by using "@ParameterName" 
class UG4ParameterFileOutputAdapter(ParameterOutputAdapter):

    def writeParameters(self, directory: str, evaluation_id: int, parametermanager: ParameterManager, parameter, fixedparameters):
        
        parameterfile = os.path.join(directory, str(evaluation_id) + "_parameters.json")

        parameterlist = []
        for i in range(len(parameter)):
            parameter = { "uid":  "@" + parametermanager.parameters[i].name,
                        "type": "const",
                        "value": parameter[i]}
            parameterlist.append(parameter)

        for k in fixedparameters:
            parameter = { "uid":  "@" + k,
                        "type": "const",
                        "value": fixedparameters[k]}
            parameterlist.append(parameter)

        # write the parameter file parsed in lua
        with open(parameterfile,"w") as f:
            json.dump(parameterlist, f)