import os
import numpy as np
import pickle
import copy
from scipy import stats
from math import floor, log10
from .freesurface_evaluation import FreeSurfaceTimeDependentEvaluation, FreeSurfaceEquilibriumEvaluation
from datetime import datetime

def fexp(f):
    return int(floor(log10(abs(f)))) if f != 0 else 0

def fman(f):
    return f/10**fexp(f)

class Result:

    def __init__(self,filename=None):
        self.iterations = []
        self.logentries = []

        self.currentIteration = {}

        self.metadata = {}

        self.filename = filename

    @property
    def iterationCount(self):
        return len(self.iterations)

    def writeTable(self, file, parameternames, metadata):

        with open(file,"w") as f:
            
            # write table header
            f.write("step" + "\t")
            for p in parameternames:
                f.write(p+"\t")
            for p in metadata:
                f.write(p+"\t")

            f.write("\n")

            i = 0
            for iteration in self.iterations:
                f.write(str(i) + "\t")
                for j in range(len(parameternames)):
                    f.write(str(iteration["parameters"][j]) + "\t")

                for p in metadata:
                    if p in iteration:
                        f.write(str(iteration[p]) + "\t")
                    else:
                        f.write("NaN\t")
                
                f.write("\n")
                i += 1
    
    def writeLatexTable(self, file, parameternames, metadata):

        with open(file,"w") as f:
            
            # write table header
            f.write("\\begin{tabular}{")
            
            count = len(parameternames) + len(metadata)
            f.write("c||")
            for i in range(count-1):
                f.write("c|")
            f.write("c}\\\\\n")

            f.write("step" + " & ")
            for i in range(len(parameternames)):
                p = parameternames[i]
                f.write("$\\beta_"+str(i)+"$ (\\verb|"+p+"|) & ")

            for i in range(len(metadata)-1):
                f.write(metadata[i]+"&")            
            f.write(metadata[-1]+"\\\\\hline\n")

            i = 0
            for iteration in self.iterations:
                f.write(str(i) + " & ")
                for j in range(len(parameternames)):
                    entry = self.metadata["parametermanager"].parameters[j].getTransformedParameter(iteration["parameters"][j])
                    f.write("$" + self.getLatexString(entry) + "$"+ " & ")

                for j in range(len(metadata)):
                    p = metadata[j]
                    if p in iteration:
                        f.write("$" + self.getLatexString(iteration[p]) + "$" )
                    else:
                        f.write("NaN")
                    if j == len(metadata)-1:
                        f.write("\\\\\n")
                    else:
                        f.write(" & ")
                
                i += 1

            f.write("\\end{tabular}")

    
    def writeErrorTable(self, file, parameternames, confidence=0.95):

        with open(file,"w") as f:
            
            # write table header
            f.write("\\begin{tabular}{")
            
            count = len(parameternames)*2
            f.write("c||")
            for i in range(count-1):
                f.write("c|")
            f.write("c}\n")

            f.write("step" + " & ")
            for i in range(len(parameternames)-1):
                p = parameternames[i]
                f.write("$\\beta_"+str(i)+"$ ("+p+") & ")
                f.write("se($\\beta_" + str(i) + "$) & ")
        
            i = len(parameternames)-1
            f.write("$\\beta_"+str(i)+"$ (\\verb|"+parameternames[-1]+"|) & ")
            f.write("se($\\beta_" + str(i) + "$) \\\\\hline\n")
            

            i = 0
            for iteration in self.iterations:
                f.write(str(i) + " & ")
                for j in range(len(parameternames)):
                    entry = self.metadata["parametermanager"].parameters[j].getTransformedParameter(iteration["parameters"][j])
                    error = iteration["errors"][j]
                    if "confidenceinterval" in iteration:
                        interval = iteration["confidenceinterval"][j]
                        f.write("$" + self.getLatexString(entry) + "\\pm" + self.getLatexString(interval) + "$"+ " & ")
                    else:
                        f.write("$" + self.getLatexString(entry) + "$"+ " & ")

                    error = iteration["errors"][j]
                    f.write("$" + self.getLatexString(error) + "$")

                    if j == len(parameternames)-1:
                        f.write("\\\\\n")
                    else:
                        f.write(" & ")
                
                i += 1

            f.write("\\end{tabular}")

    def writeMatrix(self, file, name, symbol, iterations_to_print=[-1]):
        
        with open(file,"w") as f:
            for i in iterations_to_print:

                if i == -1:
                    i = self.iterationCount-1

                data = self.iterations[i][name]

                f.write("$$" + symbol + "^{(" + str(i) + ")} = \\begin{pmatrix}\n")
            
                for x in range(np.shape(data)[0]):
                    for y in range(np.shape(data)[1]):

                        f.write(self.getLatexString(data[x][y]))

                        if(y == np.shape(data)[1]-1):
                            f.write("\\\\\n")
                        else:
                            f.write("&")
                
                f.write("\\end{pmatrix}$$\n")

    def writeSensitivityPlots(self, filename, iteration, parameternames,extended=True):

        if iteration == -1:
            iteration = self.iterationCount-1

        if len(self.iterations) <= iteration or iteration < 0:
            print("Illegal iteration index")
            return

        iterationdata = self.iterations[iteration]
        jacobi = iterationdata["jacobian"]
        p = iterationdata["parameters"]
        m = iterationdata["measurement"]

        if len(parameternames) != jacobi.shape[1]:
            print("Mismatch of parameter count!")
            return

        for i in range(len(parameternames)):
            dg = jacobi[:,i]
            partial = (p[i]/(np.max(m)))*dg
            if isinstance(self.metadata["target"], FreeSurfaceTimeDependentEvaluation):
                partial_series = FreeSurfaceTimeDependentEvaluation.fromNumpyArray(partial, self.metadata["target"])
                
                if extended:
                    partial_series.writeCSVAveragedOverTimesteps(filename + "-" + parameternames[i] + "-over-time.csv")
                    partial_series.writeCSVAveragedOverLocation(filename + "-" + parameternames[i] + "-over-location.csv")
                
                    with open(filename + "-" + parameternames[i] + ".tex","w") as f:                    
                        f.write("\\begin{center}\n")
                        f.write("\\begin{minipage}{0.4\\textwidth}\n")
                        f.write("\t\\begin{tikzpicture}[scale=0.8]\n")
                        f.write("	\\begin{axis}[\n")
                        f.write("	xlabel=Zeit,\n")
                        f.write("	ylabel=$\\frac{\\delta m}{\\delta \\beta_"+ str(i) + "}$,\n")
                        f.write("	legend style={\n")
                        f.write("		at={(0,0)},\n")
                        f.write("		anchor=north,at={(axis description cs:0.5,-0.18)}}]\n")
                        f.write("	\\addplot [thick] table [x={time}, y={value}] {"+filename + "-" + parameternames[i] + "-over-location.csv"+"};\n")
                        f.write("	\\end{axis}\n")
                        f.write("	\\end{tikzpicture}\n")
                        f.write("\\end{minipage}	 \n")
                        f.write("\\begin{minipage}{0.4\\textwidth}\n")
                        f.write("		\\begin{tikzpicture}[scale=0.8]\n")
                        f.write("		\\begin{axis}[\n")
                        f.write("		xlabel=Ort,\n")
                        f.write("		ylabel=$\\frac{\\delta m}{\delta \\beta_"+ str(i) + "}$,\n")
                        f.write("		legend style={\n")
                        f.write("			at={(0,0)},\n")
                        f.write("			anchor=north,at={(axis description cs:0.5,-0.18)}} ]\n")
                        f.write("		\\addplot [thick] table [x={location}, y={value}] {"+filename + "-" + parameternames[i] + "-over-time.csv};\n")
                        f.write("		\\end{axis}\n")
                        f.write("		\\end{tikzpicture}\n")
                        f.write("\\end{minipage}\\\\\n")  
                        f.write("\\end{center}")
                else:
                    partial_series.write3dPlot(filename + "-" + parameternames[i] + ".tex", "$\\frac{\\delta g}{\\delta \\beta_0}$ {[m]}",scale=0.8)
            elif isinstance(self.metadata["target"], FreeSurfaceEquilibriumEvaluation):
                partial_series = FreeSurfaceEquilibriumEvaluation.fromNumpyArray(partial, self.metadata["target"])
                FreeSurfaceEquilibriumEvaluation.writePlots({"Sensitivity":partial_series}, filename + "-" + parameternames[i] + ".tex", "$\\frac{\\delta m}{\delta \\beta_"+ str(i) + "}$ {[m]}")
                
    def plotComparison(self, filename):

        target = self.metadata["target"]
        result = self.iterations[self.iterationCount-1]["measurementEvaluation"]
        start = self.iterations[0]["measurementEvaluation"]

        if isinstance(target, FreeSurfaceEquilibriumEvaluation):
            result = FreeSurfaceEquilibriumEvaluation.fromTimedependentTimeseries(result)
            start = FreeSurfaceEquilibriumEvaluation.fromTimedependentTimeseries(start)
            FreeSurfaceEquilibriumEvaluation.writePlots({"result":result, "target":target, "start":start}, filename) 
        else:
            with open(filename,"w") as f:
                f.write("\\begin{center}\n")
                f.write("\\begin{minipage}{0.3\\textwidth}\n")                    
                f.write(target.write3dPlot(None, scale=0.4)) 
                f.write("\\\ntarget")                     
                f.write("\\end{minipage}	 \n")
                f.write("\\begin{minipage}{0.3\\textwidth}\n")                    
                f.write(start.write3dPlot(None, scale=0.4)) 
                f.write("\\\nstart")                     
                f.write("\\end{minipage}	 \n")
                f.write("\\begin{minipage}{0.3\\textwidth}\n")                 
                f.write(result.write3dPlot(None, scale=0.4))
                f.write("\\\nresult")  
                f.write("\\end{minipage}\\\\\n")  
                f.write("\\end{center}")

    def getLatexString(self, number):
        exp = fexp(number)
        man = fman(number)

        man = round(man, 3)

        if exp >= -1 and exp <= 1:
            return str(round(number,4))
        else:
            return str(man) + "\\cdot 10^{" + str(exp) + "} "

    def addRunMetadata(self, name, value):
        self.metadata[name] = value

    def addEvaluations(self, evaluations, tag=None):
        if "evaluations" not in self.currentIteration:
            self.currentIteration["evaluations"] = []
        self.currentIteration["evaluations"].append((copy.deepcopy(evaluations), tag, self.iterationCount))

    def addMetric(self, name, value):
        self.currentIteration[name] = value
        
    def commitIteration(self):
        self.iterations.append(copy.deepcopy(self.currentIteration))
        self.currentIteration.clear()
        self.save()

    def save(self,filename=None):
        if filename is None:            
            filename = self.filename

        if filename is None:
            return

        with open(filename,"wb") as f:
            pickle.dump(self.__dict__,f)
    
    def log(self, text):

        logtext = "[" + str(datetime.now()) + "] " + text
        print(logtext)
        self.logentries.append(logtext)
        with open(self.filename + "_log","a") as f:
            f.write(logtext + "\n")
                
    def printlog(self):
        for l in self.logentries:
            print(l)

    @classmethod
    def load(cls,filename):
        result = cls()
        with open(filename,"rb") as f:
            result.__dict__.update(pickle.load(f))
        return result
    
    @classmethod
    def loadLegacy(cls,filename):
        result = cls()
        with open(filename,"rb") as f:
            result.iterations = pickle.load(f)
        return result
