-----------------------------------------------------------------
-- include the basic util Methods and other Files
-----------------------------------------------------------------
ug_load_script("solver_util/setup_rsamg.lua")
-- ug_load_script("plugins/Limex/limex_util.lua")
ug_load_script("util/checkpoint_util.lua")

RequiredPlugins({"ConvectionDiffusion"})
--RequiredPlugins({"Biogas"})
RequiredPlugins({"Limex"})

-- assemble output filename
communcationDir = util.GetParam("-communicationDir","./evaluations")
evaluationId = util.GetParam("-evaluationId",0)
outputfilename = communcationDir.."/"..evaluationId.."_measurement.csv"

-----------------------------------------------------------------
-- Assemble reaction and reactor model setup from user input
-----------------------------------------------------------------
ug_load_script (common_scripts.."Assemble_Model_Setup.lua")

-----------------------------------------------------------------
-- Assemble numerical problem
-----------------------------------------------------------------
ug_load_script (common_scripts.."Assemble_Numerics.lua")

ug_load_script(common_scripts.."HomogeneousDistribution.lua")

reactorVolume = Integral(1.0, u, pSettings.expert.geometry.subsets["reactorVolSubset"])
factor_volCorrection = pSettings.reactorSetup.realReactorVolume/reactorVolume

if outputSpecs.debug then
	print("DBG: reactorVol(GEOM) = "..reactorVolume)
	print("DBG: reactorVol(EXP) = "..pSettings.reactorSetup.realReactorVolume)
	print("DBG: volCorrection = "..factor_volCorrection)
end

if extraGasphase then headSpaceVolume = Integral(1.0, u, pSettings.expert.geometry.subsets["gasPhaseSubset"]) end

timeStepPREV = 0

if outputSpecs.debug then
	dbg_feed = io.open("dbg_feeding.txt", "w")
	dbg_feed:write("# [h]\t[g]\n")
	dbg_feed:write("# Time\tAmount")
	FEDAMOUNT = 0.0
end

ug_load_script(common_scripts.."SpecialUserFunctions.lua")

ug_load_script(common_scripts.."Equation_Setup.lua")
ug_load_script(common_scripts.."Boundary_Conditions.lua")

-----------------------------------------------------------------
--  Setup Solver
-----------------------------------------------------------------
if print_info==true then 
print ("Setting up Solver")
end

ug_load_script(common_scripts.."Solver_Setup.lua")

-----------------------------------------------------------------
-- Create measurement file
-----------------------------------------------------------------
file = io.open(outputfilename, "a")
file:write("step,time,value\n")
file:close()

-----------------------------------------------------------------
-- Set initial value
-----------------------------------------------------------------
if print_info==true then 
print("Interpolating Initial Values @time: "..time)
end

ug_load_script (common_scripts.."Initial_Values.lua")

-----------------------------------------------------------------
-- Load Timestep Output routine
-----------------------------------------------------------------
ug_load_script (optimizer_scripts.."TimestepOutputOptimizer.lua")


-----------------------------------------------------------------
-- Perform Timesteps
-----------------------------------------------------------------
	if print_info==true then 
	print("Starting Calculation...")
	end
	
	ug_load_script(common_scripts.."Calculate.lua")

----------------------------------------------------------
-- Callbacks for writing the measured data to file
----------------------------------------------------------
print("Finished")
file = io.open(outputfilename, "a")
file:write("FINISHED,,")
file:close()

----------------------------------------------------------

if print_info then
	print("End of Biogas-MAIN")
end