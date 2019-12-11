from .evaluation import Evaluation, ErroredEvaluation
import numpy as np
import math
import os
import csv

class FreeSurfaceEvaluation(Evaluation):

    data = [[]]
    locations = []
    dimension = -1
    times = []

    @property
    def timeCount(self):
        return len(self.times)

    @property
    def locationCount(self):
        return len(self.locations)

    @property
    def totalCount(self):
        return len(self.times)*len(self.locations)

    def getNumpyArray(self):
        return np.reshape(np.array(self.data),-1)
    
    @staticmethod
    def hasSameLocations(A, B):
        
        # compare the locations
        if A.locationCount != B.locationCount:
            return False
        else:
            for l in range(A.locationCount):
                if A.dimension == 2:
                    if math.fabs(B.locations[l]-A.locations[l]) > 0.001:
                        return False                        
                else:
                    if math.fabs(B.locations[l][0]-A.locations[l][0]) > 0.001 or math.fabs(B.locations[l][1]-A.locations[l][1]) > 0.001:
                        return False                    

        return True  

    @classmethod
    def parse(cls, directory, evaluation_id, parameters, eval_id, runtime):
        raise NotImplementedError("Abstract class FreeSurfaceEvaluation doesn't implement parse()")

    def getNumpyArrayLike(self, target):
        raise NotImplementedError("Abstract class FreeSurfaceEvaluation doesn't implement getNumpyArrayLike()")


class FreeSurfaceEquilibriumEvaluation(FreeSurfaceEvaluation):

    def __init__(self, data, locations, dimension, time=0):
        self.data = data
        self.locations = locations
        self.dimension = dimension
        self.times[0] = time
        
    @classmethod
    def fromCSV(cls, filename, dim):
        data = [[]]
        locations = []
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data[-1].append(float(row["Value"]))
                if dim == 2:
                    locations.append(float(row["X"]))
                elif dim == 3: 
                    locations.append((float(row["X"]), float(row["Y"])))

        return cls(data, locations, dim)
    
    @classmethod
    def fromTimedependentTimeseries(cls, series):       
        #if not series.isInEquilibrium():
        #    raise Exception("Factor of Eqilibrium on this Measurement unsufficient! Please lengthen the simulation.")
        data_reformatted = [series.data[-1]]
        dim = 2
        if hasattr(series, "dimension"):
            dim = series.dimension
        returnval = cls(data_reformatted, series.locations, dim, series.times[-1])

        returnval.parameters = series.parameters

        return returnval
    
    @classmethod
    def fromNumpyArray(cls, data, seriesformat):
        data_reformatted = np.array(data).reshape((seriesformat.timeCount, seriesformat.locationCount)).tolist()
        dim = 2
        if hasattr(seriesformat, "dimension"):
            dim = seriesformat.dimension
        return cls(data_reformatted, seriesformat.locations, dim, seriesformat.times[0])

    @staticmethod
    def writePlots(series, filename, yaxislabel="$m(l,\\vec{\\beta})$ {[m]}"):

        plot = ""
        plot += "\t\\begin{tikzpicture}\n"
        plot += "\t\t\\begin{axis}[\n"                    
        plot += "	xlabel=Ort l {[m]},\n"     
        plot += "	width=10cm,\n"
        plot += "	ylabel={" + yaxislabel + "},\n"
        plot += "	legend style={\n"
        plot += "		anchor=north west,at={(axis description cs:1.01,1)}} ]\n"

        for k in series:
            seriesobject = series[k]

            plot += "\t\t\\addplot+[thick,mark=*]\n"
            plot += "\t\t table [x={location}, y={value}]{ \n"
            plot += "location\t value\n"        

            sortedindices = np.argsort(np.array(seriesobject.locations))
            for l in range(seriesobject.locationCount):
                plot += str(seriesobject.locations[sortedindices[l]]) + "\t" + str(seriesobject.data[0][sortedindices[l]]) + "\n"
            
            plot += "};\n"
                
            plot += "\t\t\\addlegendentry{" + k + "};"


        plot += "\t\t\\end{axis}\n"
        plot += "\t\\end{tikzpicture}\n"

        if(not filename is None):
            with open(filename, "w") as f:
                f.write(plot)

        return plot
    
    def getNumpyArrayLike(self, target):
        raise NotImplementedError("FreeSurfaceEquilibriumEvaluation doesn't implement getNumpyArrayLike()")

class FreeSurfaceTimeDependentEvaluation(FreeSurfaceEvaluation):    

    EQUILIBRIUM_CONSTANT = 10  

    def __init__(self, data, times, locations, dimension, eval_id=-1, parameters=None, runtime=None):
        self.data = data
        self.times = times
        self.locations = locations
        self.dimension = dimension
        self.eval_id = eval_id
        self.parameters = parameters
        self.runtime = runtime

    @classmethod
    def parse(cls, directory, evaluation_id, parameters=None, runtime=None):
        data = []
        times = []
        locations = []
        finished = False
        dimension = -1

        filename = os.path.join(directory, str(evaluation_id) + "_measurement.txt")

        with open(filename) as f:
            for line in f:

                linedata = line.split("\t")

                if dimension == -1:
                    if len(linedata) == 3:
                        dimension = 2
                    elif len(linedata) == 4:
                        dimension = 3
                    elif line == "FINISHED":
                        return cls(data, times, locations, dimension)
                    else:
                        raise Evaluation.IncompatibleFormatError("Could not parse " + filename)

                if(line == "FINISHED"):
                    finished = True
                    break
                elif dimension != len(linedata)-1:
                    raise Evaluation.IncompatibleFormatError("Incorrect number of data points in line " + line + " in file " + filename)

                time = float(linedata[0])
                if(not time in times):
                    times.append(time)
                    data.append([])
                
                if(dimension == 2):
                    location = float(linedata[1])
                    data[-1].append(float(linedata[2]))  
                elif dimension == 3:
                    location = (float(linedata[1]), float(linedata[2]))
                    data[-1].append(float(linedata[3]))  

                if(not location in locations):
                    locations.append(location)
                
        if finished:
            return cls(data, times, locations, dimension, evaluation_id, parameters, runtime)
        else:
            return ErroredEvaluation(parameters, "UG run did not finish.", evaluation_id, runtime)

    @classmethod
    def fromNumpyArray(cls, data, seriesformat):
        data_reformatted = np.array(data).reshape((seriesformat.timeCount, seriesformat.locationCount)).tolist()
        dim = 2
        if hasattr(seriesformat, "dimension"):
            dim = seriesformat.dimension
        return cls(data_reformatted, seriesformat.times, seriesformat.locations, dim)

    def getNumpyArrayLike(self, target: Evaluation):

        if (not isinstance(target, FreeSurfaceEquilibriumEvaluation)) and (not isinstance(target, FreeSurfaceTimeDependentEvaluation)):
            raise Evaluation.IncompatibleFormatError("Target not compatible!")

        if not FreeSurfaceTimeDependentEvaluation.hasSameLocations(self, target):
            print("Target: " + str(target.locations))
            print("this: " + str(self.locations))
            raise Evaluation.IncompatibleFormatError("Not the same locations!")

        if isinstance(target, FreeSurfaceEquilibriumEvaluation):
            return np.array(self.data[-1])

        else:
            array = np.zeros(len(target.times)*len(target.locations))
            for i in range(len(target.times)):
                targettime = target.times[i]

                # find nearest entries in this instances time field
                nearest_lower = 0
                nearest_higher = len(self.times)-1


                while(True):
                    if (nearest_lower +1 == len(self.times)):
                        if(self.times[nearest_lower] == targettime):
                            break
                        else:
                            if(i == len(target.times)-1):
                                break
                            else:
                                raise Evaluation.IncompatibleFormatError("target time " + str(targettime) + " can not be interpolated from this time series.")
                    else:
                        if(self.times[nearest_lower] < targettime and not self.times[nearest_lower+1] > targettime):
                            nearest_lower += 1
                        else:
                            break
                
                if(self.times[nearest_lower] == targettime):
                    array[i*len(target.locations):((i+1)*len(target.locations))] = self.data[nearest_lower]
                    continue
                elif (i == len(target.times)-1) and (nearest_lower +1 == len(self.times)):
                    array[i*len(target.locations):((i+1)*len(target.locations))] = array[(i-1)*len(target.locations):(i*len(target.locations))]
                    continue

                while(True):
                    if(self.times[nearest_higher] > targettime and not self.times[nearest_higher-1] < targettime):
                        nearest_higher -= 1
                    else:
                        break

                higherdata = np.array(self.data[nearest_higher])
                highertime = self.times[nearest_higher]
                lowerdata = np.array(self.data[nearest_lower])
                lowertime = self.times[nearest_lower]

                percentage = ((targettime-lowertime) / (highertime-lowertime))
                interpolated = percentage*higherdata + (1-percentage)*lowerdata

                array[i*len(target.locations):((i+1)*len(target.locations))] = interpolated            

            return array

    def writeCSVAveragedOverLocation(self, filename):    
        with open(filename,"w") as f:
            f.write("time \t value\n")
            for t in range(self.timeCount):
                summed_up = sum(self.data[t])
                average = summed_up/self.locationCount
                f.write(str(self.times[t]) + "\t" + str(average) + "\n")

    def writeCSVAtLocation(self, filename, location):
        if location not in self.locations:
            print("illegal location specified!")
            return

        locindex = self.locations.index(location)
        
        with open(filename,"w") as f:
            f.write("time \t value\n")
            for t in range(self.timeCount):
                value = self.data[t][locindex]
                f.write(str(self.times[t]) + "\t" + str(value) + "\n")        

    def writeCSVAveragedOverTimesteps(self, filename):
        summed_up = np.zeros(self.locationCount)
        for t in range(self.timeCount):
            summed_up += np.array(self.data[t])

        with open(filename,"w") as f:
            f.write("location \t value\n")
            for l in range(self.locationCount):
                f.write(str(self.locations[l]) + "\t" + str(summed_up[l]) + "\n")

    def writeCSVAtTimestep(self, filename,timestep):    

        if timestep == -1:
            timestep = self.timeCount-1

        if(timestep < 0 or timestep >= self.timeCount):
            print("Illegal timestep specified!")
            return

        with open(filename,"w") as f:
            f.write("location \t value\n")
            for l in range(self.locationCount):
                f.write(str(self.locations[l]) + "\t" + str(self.data[timestep][l]) + "\n")

    def writeCSV(self, filename):
        with open(filename, "w") as f:
            f.write("time\tlocation\t value\n")
            for t in range(self.timeCount):
                for l in range(self.locationCount):
                    f.write(str(self.times[t]) + "\t" + str(self.locations[l]) + "\t" + str(self.data[t][l]) + "\n")

    def write3dPlot(self, filename, zlabel="$m(l,t,\\beta)$", scale=1, stride=3):

        if self.dimension != 2:
            raise Evaluation.IncompatibleFormatError("3d plot not available for 3d measurements")

        plot = ""

        if(not filename is None):
            plot += "\\documentclass{standalone}\n"
            plot += "\\usepackage{pgfplots}\n"
            plot += "\\usepackage{tikz}\n"
            plot += "\\begin{document}\n"

        plot += "\t\\begin{tikzpicture}\n"
        plot += "\t\t\\begin{axis}[view/h=45,\n"                    
        plot += "	xlabel=Zeit $t$ {[s]},\n"     
        plot += "	width=10cm,\n"
        plot += "	ylabel=Ort $l$ {[m]},\n"
        plot += "   scale=" + str(scale) + ",\n"
        plot += "	zlabel=]\n"
        plot += "\t\t\\addplot3 [surf,mesh/ordering=y varies,mesh/rows=" + str(self.locationCount) + "]\n"
        plot += "\t\t table { \n"
        plot += "time\tlocation\t value\n"
        for t in range(self.timeCount):
            if t % stride != 0:
                continue
            for l in range(self.locationCount):
                plot += str(self.times[t]) + "\t" + str(self.locations[l]) + "\t" + str(self.data[t][l]) + "\n"
        plot += "};\n"
        plot += "\t\t\\end{axis}\n"
        plot += "\t\\end{tikzpicture}\n"

        if(not filename is None):
            plot += "\\end{document}"
            with open(filename, "w") as f:
                f.write(plot)
            directory = os.path.dirname(filename)
            os.system("pdflatex -interaction=nonstopmode -output-directory=" + directory + " " + filename)

        return plot

    def writePlots(self, filename, num):
        if self.dimension != 2:
            raise NotImplementedError("plot not available for 3d measurements")

        plot = ""
        plot += "\t\\begin{tikzpicture}\n"
        plot += "\t\t\\begin{axis}[\n"                    
        plot += "	xlabel={Ort $l$ {[m]}},\n"     
        plot += "	width=10cm,\n"
        plot += "	ylabel={$m(l,t,\\vec{\\beta})$},\n"
        plot += "	legend style={\n"
        plot += "		anchor=north west,at={(axis description cs:1.01,1)}} ]\n"
        
        idx = np.round(np.linspace(0, len(self.times) - 1, num)).astype(int)
        for t in idx:
            time = self.times[t]
            plot += "\t\t\\addplot+[thick,mark=*]\n"
            plot += "\t\t table [x={location}, y={value}]{ \n"
            plot += "location\t value\n"
            for l in range(self.locationCount):
                plot += str(self.locations[l]) + "\t" + str(self.data[t][l]) + "\n"
            plot += "};\n"
            plot += "\\addlegendentry{t=" + str(time) + "};\n"
        plot += "\t\t\\end{axis}\n"
        plot += "\t\\end{tikzpicture}\n"

        if(not filename is None):
            with open(filename, "w") as f:
                f.write(plot)

        return plot

    def writeDifferentialPlot(self, filename):

        plot = ""
        plot += "\t\\begin{tikzpicture}\n"
        plot += "\t\t\\begin{axis}[\n"                    
        plot += "	xlabel=Zeit {[s]},\n"     
        plot += "	width=10cm,\n"
        plot += "	ylabel=$||\\frac{\\delta m}{\\delta t}||_2$]\n"
        plot += "\t\t\\addplot [thick]\n"
        plot += "\t\t table [x={time}, y={value}]{ \n"
        plot += "time\t value\n"
        for t in range(self.timeCount-1):
            change = np.linalg.norm(np.array(self.data[t])-np.array(self.data[t+1]))
            plot += str(self.times[t]) + "\t" + str(change) + "\n"
        plot += "};\n"
        plot += "\t\t\\end{axis}\n"
        plot += "\t\\end{tikzpicture}\n"

        if(not filename is None):
            with open(filename, "w") as f:
                f.write(plot)

        return plot

    def getFactorOfEquilibrium(self):
        max_change = -float('inf')
        for t in range(self.timeCount-1):
            change = np.linalg.norm(np.array(self.data[t])-np.array(self.data[t+1]))
            change /= self.times[t+1]-self.times[t]

            max_change = max(max_change, change)
            # print("change between timestep " + str(t) + " and " + str(t+1) + " is " + str(change))

        last_change = np.linalg.norm(np.array(self.data[-1])-np.array(self.data[-2]))
        last_change /= self.times[-1]-self.times[-2]

        return max_change/last_change

    def isInEquilibrium(self):
        return self.getFactorOfEquilibrium() > self.EQUILIBRIUM_CONSTANT
