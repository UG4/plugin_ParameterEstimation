--	Vorlage Benutzer-Input
--	Autor: Rebecca Wittum

communcationDir = util.GetParam("-communicationDir", "./evaluations")
evaluationId = util.GetParam("-evaluationId", 0)

local p = util.Parameters:fromfile(communcationDir.."/"..evaluationId.."_parameters.json")

problem = {
-----------------------------------------------------------------	
--	Specifications for REACTOR OPERATIONAL SETUP
-----------------------------------------------------------------
	reactorSetup = {
		operatingTemperature = p.operatingTemperature,		--in Kelvin!
		reactorType = "CSTR",				--options: CSTR, Downflow
		realReactorVolume = p.realReactorVolume		-- volume of actual reactor in L ()
	},
-----------------------------------------------------------------
--	Setup for REACTION MODEL
-----------------------------------------------------------------
	reactionSetup = {
		activeReactions = {	"simpleTwoStage"} -- standard Options: simpleTwoStage, all (more in advanced/expert mode)
	},

-----------------------------------------------------------------
--	NUMERICAL Specifications for SOLVING
-----------------------------------------------------------------
	numericalSetup = {
		sim_starttime = 0,
		sim_endtime = 30,			-- in hours
	},

-----------------------------------------------------------------
--	OUTPUT Specifications
-----------------------------------------------------------------
	outputSpecs = {
		customSetting = {
			cDigestate = true,
			biogas = true,
			developer = true,
			debug = true,
			vtk = false,
		},
	},


	-----------------------------------------------------------------
	--	CHECKPOINTING Specifications
	-----------------------------------------------------------------
	checkpoint = {
		doReadCheckpoint = false,
		--checkpointDir = "../startNoCheckpoint/"
	},

-----------------------------------------------------------------
--	STARTING VALUES
-----------------------------------------------------------------
initialValues = {
	pH = 8.06,
	drymass = 0.0906,
	analysis = {
		["Carbohydrates"] = p.initialCarbonhydrates,
		["Lipids"] = 0.8,
		["Proteins"] = 0.97,
		["MS"] = 0.004,
		["LCFA"] = 0.003,
		["AA"] = 0.001,
		["Lignin"] = 113.0,
		["Acetic"] = p.initialAcetic,-- 1.50,		-- concentration [g/L]
		["Propionic"] = 0.003,
		["Butyric"] = 0.0025,
		["Valeric"] = 0.0007,
		["Methane"] = 0.062,
		["Carbondioxide"] = 0.875,
		["Hydrogen"] = 4.23*1E-9,

		-- starting to include:
		["Nitrogen"] = 2902.92*1E-3,--]]	-- value of NH4-N in g/L
		["MO_acetoM"] = 1.8,		-- concentration [g/L]
		["MO_hydroM"] = 3.1,		-- concentration [g/L]
		["MO_Propionic"] = 1.1,
		["MO_ButyricValeric"] = 1.9,
		["MO_AcidoMS"] = 6.8,
		["MO_AcidoLCFA"] = 1.33,
		["MO_AcidoAA"] = 0.99,
	},
},
-----------------------------------------------------------------
--	Specifications for FEEDING PROCEDURE
-----------------------------------------------------------------
feeding = {
	--dbg_feedingcontig = true,
	drymass = 0.3649,
	volatile = 0.973,			-- volatile solids [% of drymass]
	stoidisintegration = {
		["Proteins"] = 0.077697841726619,
		["Lipids"] = 0.03186022610483,
		["Carbohydrates"] = p.feedingCarbonhydrates -- 0.65927235354573,-- 0.39527235354573,
	},
	
	analysis = {
		["Acetic"] = 10713.49*1E-3,		-- concentration [g/L FM]
		["Propionic"] = 745.28*1E-3,
		["Butyric"] = 443.93*1E-3,
		["Valeric"] = 35.06*1E-3,
	},
	timetable = {	-- Pairs with time of feeding [hours] and fed amount [grams]: {time, amount}							
		{ 0,	243	},
		{ 24,	243	},
		{ 48,	243	},
		{ 72,	243	},
		{ 96,	243	},
		{ 120,	243	},
		{ 144,	243	},
		{ 168,	243	},
		{ 192,	243	},
		{ 216,	243	},
		{ 240,	10*243	},
		{ 264,	10*243	},
		{ 288,	10*243	},
		{ 312,	10*243	},
		{ 336,	10*243	},
		{ 360,	243	},
		{ 384,	243	},
		{ 408,	243	},
		{ 432,	243	},
		{ 456,	243	},
		{ 480,	243	},
		{ 504,	243	},
		{ 528,	243	},
		{ 552,	243	},
		{ 576,	243	},
		{ 600,	243	},
	},
	
},
	
-----------------------------------------------------------------
--	ADVANCED/EXPERT SETTING OPTIONS
-----------------------------------------------------------------
	expert = {
	-----------------------------------------------------------------
	--	Specifications for REACTOR GEOMETRY
	-----------------------------------------------------------------
		geometry = {
			grid_name = "TestGeom2D.ugx",
			subsets = {
				["reactorVolSubset"] = "Inner",
				["gasPhaseSubset"] = "Head",
				["reactorUpperBnd"] = "Top",
				["reactorLowerBnd"] = "Bot",
				["reactorLeftBnd"] = "SideA",
				["reactorRightBnd"] = "SideB"
			},
			setup_dim = 2,
			reactorHeight = 1.0,		-- Height of fermenter content subset (in dm)
			headHeight = 0.1,			-- Height of headspace subset (in dm)
			reactorWidth = 1.0,		-- Width of reactor (in dm)
			yTop = 1.0,					-- y value of "Top" interface in geometry (in dm)
			
			numPreRefs = 1,
			numRefs = 3,
		},
		
		timestep = {
			dtStart = 0.2,
			dtMax = 1,
			dtMin = 0.00001,
		},
		
		reactionSetup = {
			thermodynModell = true,
			inhibitionTerms = {
				inhibitionAmmonia = false,
				limitedTrace = {
					["Nitrogen"] = false,},
				limitedMOSpace = false,
				competitiveAcidUptake = false,
				inhibitionPH = false,
			},
		},
		
	},
	
} --End of problem description
