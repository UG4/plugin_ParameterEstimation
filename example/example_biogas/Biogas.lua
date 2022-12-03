--###########################################################################
--#	Script um Biogasmodell für ein zu spefizifierendes Problem auszuführen	#
--#	Autor: Rebecca Wittum													#
--###########################################################################

ug_load_script("ug_util.lua") 

local pfile = util.GetParam ("-p"			,	"")
local sfile = util.GetParam ("-s"			,	"")

evaluationId = util.GetParam("-evaluationId", 0)
communicationDir = util.GetParam("-communicationDir", "./evaluations")

if (pfile == "") and (sfile == "") then
	print("ERROR: Missing Specification of User Input File.")
	print("HINT:\tCall Biogas.lua with -p \"MyProblemSpecification.lua\" to run a simulation")
	print("\tCall Biogas.lua with -s \"MyStoichiometryInput.lua\" to compute substrate disintegration stoichiometry coefficients")
	exit()
end
local pFileLoaded = false
if (pfile ~= "") then
	ug_load_script(pfile)
	print("LOADED "..pfile)
	pFileLoaded = true
end
if (sfile ~= "") then
	ug_load_script(sfile)
	if (not stoiInfo) then
		print("ERROR: No specification of \"stoiInfo\" given in Input file "..sfile)
		exit()
	end
	stoi = SimpleStoiFromBatch()
	ws = WeenderSoest()
	for purpose, info in pairs (stoiInfo) do
		if info.type == "batch" then
			if (not info.values) then
				print("ERROR: No specification of \"stoiInfo."..purpose..".values\" given in Input file "..sfile)
				exit()
			end
			stoi:clear()
			--stoi:setHenryCoeff(0.02755)
			stoi:setDryMassSub(info.values.drymass)
			stoi:setGrammSub(info.values.fedsubstrate)
			stoi:setNLMethane(info.values.producedMethane)
			
			calculatedStoi = {
				simple = true,
				["Acetic"] = stoi:getAceticStoi()
			}	
		elseif info.type == "fodderanalysis" then
			if (not info.values) then
				print("ERROR: No specification of \"stoiInfo."..purpose..".values\" given in Input file "..sfile)
				exit()
			end
			ws:clear()
			ws:setDryMass(info.values.drymass)
			ws:setVolatileSolids(info.values.volatile)
			ws:setRawProtein(info.values.rprotein)
			ws:setRawFibre(info.values.rfibre)
			ws:setRawLipids(info.values.rlipid)
			ws:setNDF(info.values.ndf)
			ws:setADF(info.values.adf)
			ws:setADL(info.values.adl)	
			if info.values.starch then
				ws:setStarch(info.values.starch)
				if info.values.sugar then
					ws:setSugar(info.values.sugar)
				end
			end
			if info.values.degrLvl then
				ws:setDegradationLevel(info.values.degrLvl)
			else
				ws:setDegradationLevel(0.6)
			end
			
			calculatedStoi = {
					simple = false,
					["Proteins"] = ws:getProteins(),
					["Lipids"] = ws:getLipids(),
					["Carbohydrates"] = ws:getCarbohydrates(), 
			}
		else
			print("ERROR: Specification of \"stoiInfo."..purpose..".type\" unknown or missing in Input file "..sfile)
			exit()
		end
		if pFileLoaded then
			if (purpose == "feeding") then
				if problem.feeding then
					problem.feeding.stoidisintegration = calculatedStoi
					problem.feeding.drymass = info.values.drymass
				else
					print("No feeding procedure specified in "..pfile)
					exit()
				end
			elseif (purpose == "inoculum") then
				if not problem.initialValues then
					problem.initialValues = {}
				end
				problem.initialValues.stoidisintegration = calculatedStoi
				problem.initialValues.drymass = info.values.drymass
			end
		else
			print("No problem description given.")
			print("given value for dry mass: "..info.values.drymass)
			print("Calculated stoichiometry for "..purpose, calculatedStoi)
		end
	end
	if not pFileLoaded then
		exit()
	end
end
-----------------------------------------------------------------
-- define Home-Directories
-----------------------------------------------------------------
ug4_home			=	ug_get_root_path().."/"
app_home			=	ug4_home.."apps/biogas_app/"
common_scripts		= 	app_home.."scripts/"
optimizer_scripts	= 	ug4_home.."plugins/ParameterEstimation/example/example_biogas/"
geom_home			= 	app_home.."geometry/"

-----------------------------------------------------------------
-- Execute main script
-----------------------------------------------------------------
print("Start of Biogas-MAIN")
ug_load_script(optimizer_scripts.."MainOptimizer.lua")