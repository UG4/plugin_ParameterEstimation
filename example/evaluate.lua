
PrintBuildConfiguration()
ug_load_script("d3f_app/d3f_util.lua")

params = {
        numAnisoLvls            = util.GetParamNumber("-numAnisoLvls", 5),
        numRefs                         = util.GetParamNumber("-numRefs", 5),
        baseLvl                         = util.GetParamNumber("-baseLvl", 0),
        firstRedistProcs        = util.GetParamNumber("-firstRedistProcs", 64),
        redistProcs             = util.GetParamNumber("-redistProcs", 256),
        partitioner                     = util.GetParam("-partitioner", "dynamicBisection"), -- options are "dynamicBisection", "staticBisection", "parmetis"
        qualityRedistLevelOffset        = util.GetParamNumber("-redistLevelOffset", 5),
		qualityThreshold        = util.GetParamNumber("-qualityThreshold", 0.5),
		evaluationId = util.GetParam("-evaluationId",0),
		evaluationDir = util.GetParam("-communicationDir","."),
}

-- assembling the file names from the given information: directory and id
measurementFile = params.evaluationDir.."/"..params.evaluationId.."_measurement"
parameterFile = params.evaluationDir.."/"..params.evaluationId.."_parameters.txt"

-- reading the parameters from file
--
-- can be used as calibrationparams.porosity or the like
-- in the lua file from here on
--
calibrationparams = {}
file = io.open(parameterFile, "r")
if file == nil then
	print("No parameter file found! Using default params.")
else
	file:close()
	for line in io.lines(parameterFile) do
		index = string.find(line, "=")
		name = string.sub(line, 1, index-1)
		value = string.sub(line, index+1)
		calibrationparams[name] = tonumber(value)
	end
end

function initial_lsf (x,y,t) return y-0.1 end

function calculateMeasurementPoints(points,a,b)
	result = {}
	diff = (b-a)/(points+1)
	pos = a+diff
	for i = 0,points-1,1 do
		table.insert(result, {pos})
		pos = pos + diff
	end
	return result
end


problem = 
{ 
	-- The domain specific setup
	domain = 
	{
		dim = 2,
		grid = "testbox-triangles-reoriented.ugx",
		numRefs = 5,
		numPreRefs = 0,
	},

                balancer = {
                        qualityThreshold = params.qualityThreshold, -- parmetis seems to fail when executed on 65536 procs.
                                                                        -- note that one can still simulate on 65536 procs either by using
                                                                        -- a bisection partitioner or by avoiding redistribution on
                                                                        -- 65536 processes with parmetis by using a low qualityThreshold
                                                                        -- (e.g. 0.5, default is 0.9)
                        partitioner = {
                                type = params.partitioner,
                                verbose = false,
                                enableZCuts = false, -- zCuts are disabled by default but are enabled again through hints in the proc-hierarchy for non-aniso-levels
                                clusteredSiblings = false
                        },

                        partitionPostProcessor =
                                params.partitioner == "parmetis" and "clusterElementStacks"
                                                                                                  or "smoothPartitionBounds",

                        hierarchy = {
                                type = "standard",
                                maxRedistProcs = params.redistProcs,
                                minElemsPerProcPerLevel = 800,
                                qualityRedistLevelOffset = params.qualityRedistLevelOffset,

                                {
                                        upperLvl = 0,
                                        maxRedistProcs = params.firstRedistProcs
                                },

                                {
                                        upperLvl = 2,
                                        maxRedistProcs = 16
                                },
                        },
                },


	free_surface =
    {
			init_lsf = "initial_lsf",
			-- fs_height_subsets = "TopEdge",

			-- Technical parameters:
			LSFOutflowSubsets = "LeftEdge,RightEdge",
			LSFDirichletSubsets = "BottomEdge,TopEdge",
			NumEikonalSteps = 16, -- number of steps for the computation of the SDF and the extension
			InitNumEikonalSteps = 64, -- the same but for the initialization
			measure_height =
			{
				output_file = measurementFile,
				measurement_points = calculateMeasurementPoints(calibrationparams.numberOfMeasurementPoints, 0, 1),
				binary_output = true,
				print_measurement = true
			},
			zero_init_nv = true,
			reinit_sdf_rate = 20,
			antideriv_src = true,
			debugOutput = true
	},

	-- The density-driven-flow setup

	flow = 
	{
		type = "haline",
		cmp = {"c", "p"},
		
		gravity = -9.81,            -- [ m s^{-2}�] ("standard", "no" or numeric value)	
		density = 					
		{	"linear", 				-- density function ["const", "linear", "ideal"]
			min = 997,				-- [ kg m^{-3} ] 
			max = 998,				-- [ kg m^{-3} ]
		},	
		
		viscosity = 
		{	"const",				-- viscosity function ["const", "linear", "real"] 
			min = 1e-3,				-- [ kg m^{-3} ] 
			max = 1.5e-3,			-- [ kg m^{-3} ]
			brine_max = 0.001		
		},
		
		diffusion		= 1.e-9,
		alphaL			= 0,
		alphaT			= 0,

		upwind 		= "partial",	-- no, partial, full 
		boussinesq	= true,		-- true, false

		porosity 		=  0.1,			-- this cant do anything, as all subsets are defined below?
		permeability 	=  1.0-12,

		{
			subset                  = {"Body"},

			-- this is how you can use the parameters in code
			porosity                =  calibrationparams.porosity,
			permeability    =  calibrationparams.permeability 
		},
		
		initial = 
		{
			{ cmp = "c", value = 0.0 },
			{ cmp = "p", value = 0.0 },		
		},
		
		boundary = 
		{
			natural = "noflux",
			
			{ cmp = "p", type = "level", bnd = "TopEdge", value = 0.0 },
		},
		
		source = 
		{
			{ point = {0.1, 0.05}, params = { calibrationparams.inflow, 0} }
		}	
	},
	
	solver =
	{
		type = "newton",
		lineSearch = {			   		-- ["standard", "none"]
			type = "standard",
			maxSteps		= 4,		-- maximum number of line search steps
			lambdaStart		= 1,		-- start value for scaling parameter
			lambdaReduce	= 0.5,		-- reduction factor for scaling parameter
			acceptBest 		= true,		-- check for best solution if true
			checkAll		= false		-- check all maxSteps steps if true 
		},

		convCheck = {
			type		= "standard",
			iterations	= 10,			-- number of iterations
			absolute	= 1e-8,			-- absolut value of defact to be reached; usually 1e-6 - 1e-9
			reduction	= 1e-6,		-- reduction factor of defect to be reached; usually 1e-6 - 1e-7
			verbose		= true			-- print convergence rates if true
		},
		
		linSolver =
		{
			type = "bicgstab",			-- linear solver type ["bicgstab", "cg", "linear"]
			precond = 
			{	
				type 		= "gmg",	-- preconditioner ["gmg", "ilu", "ilut", "jac", "gs", "sgs"]
				smoother 	= "ilu",	-- gmg-smoother ["ilu", "ilut", "jac", "gs", "sgs"]
				cycle		= "V",		-- gmg-cycle ["V", "F", "W"]
				preSmooth	= 3,		-- number presmoothing steps
				postSmooth 	= 3,		-- number postsmoothing steps
				rap			= false,	-- comutes RAP-product instead of assembling if true 
				baseLevel	= 0,		-- gmg - baselevel
				
			},
			convCheck = {
				type		= "standard",
				iterations	= 100,		-- number of iterations
				absolute	= 5e-9,		-- absolut value of defact to be reached; usually 1e-8 - 1e-10 (must be stricter / less than in newton section)
				reduction	= 1e-6,		-- reduction factor of defect to be reached; usually 1e-7 - 1e-8 (must be stricter / less than in newton section)
				verbose		= true,		-- print convergence rates if true
			}
		}
	},
	
	time = 
	{
		control	= "prescribed",
		start 	= 0.0,		-- [s]  start time point
		stop	= calibrationparams.stoptime,		-- [s]  end time point
	  	dt      = 0.2,            -- [s]  initial time step 50 steps = 1 month = 2.628e6 s
		dtmin	= 0.2*0.01,		-- [s]  minimal time step
		dtmax	= 2,		-- [s]  maximal time step
		dtred	= 0.5,		-- [1]  reduction factor for time step
		tol 	= 1e-2,
	},
	
	output = 
	{
		freq	= 1, 			-- prints every x timesteps
		binary 	= true,			-- format for vtk file
		{
			file = "vtk",		-- name of vtk file
			type = "vtk",
	        data = {"c", "p", "q", "lsf", "nv", "nv_ext", "sdf", "lsf_cfl"},
		}

	}
} 

if calibrationparams.output ~= 1 then
	problem.output = nil
end

-- invoke the solution process
util.d3f.solve(problem);
