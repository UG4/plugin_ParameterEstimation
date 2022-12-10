-----------------------------------------------------------------
-- Define some helpful functions for writing output interface
-----------------------------------------------------------------
outFileKeys = {}
function createFileDesc(fname, id)
	kEntry = {
		name = fname,
		idtitle = id,
		counter = 1
	}
	kEntry.iof = io.open(kEntry.name, "w")
	return kEntry
end	
function writeCSVOutputXTime(kEntry)
	outFileKeys[kEntry.idtitle] = {
		filename = kEntry.name,
		keys = {
			type = "CSV",
			delimiter = "\t",
			comment = "#",
			x = {["Time"] = {col = kEntry.counter, unit = "[h]"}},
			y = {},
		}
	}
	kEntry.counter = kEntry.counter+1
	kEntry.iof:write("# Time [h]")
end
function writeOutputY(kEntry, yname, yunit)
	outFileKeys[kEntry.idtitle].keys.y[yname] = {col = kEntry.counter, unit =yunit}
	kEntry.counter = kEntry.counter +1
	kEntry.iof:write("\t"..yname.." "..yunit)
end
-----------------------------------------------------------------
-- Output VTK
-----------------------------------------------------------------
if outputSpecs.vtk then
	out = VTKOutput()
	if limex then
		out:print("LimexSol", u, 0, time)
	else
		out:set_binary(false)
		out:print(filename, u, 0, time)
	end
end
-----------------------------------------------------------------
-- Output with LUA in TXT
-----------------------------------------------------------------
myDataForCheckpoint = {}

allFiles = {}
if outputSpecs.cDigestate then
	allFiles.dFile = createFileDesc("digestateConcentrations.txt", "digestateConcentration")
	writeCSVOutputXTime(allFiles.dFile)
	
	digestateKey = io.open("digConc_key", "w")
	digestateKey:write("t\t=\t"..1)
end
if outputSpecs.developer then
	allFiles.cFile = createFileDesc("subMO_mass.txt", "allMass")
	writeCSVOutputXTime(allFiles.cFile)
	allFiles.valveFile = createFileDesc("valveGasFlow.txt", "valveFlow")
	writeCSVOutputXTime(allFiles.valveFile)
	
	outputKey = io.open("subMO_RR_key", "w")
	outputKey:write("Time\t=\t"..1)
end
if outputSpecs.biogas then
	allFiles.gFile = createFileDesc("gas_Volfraction.txt", "gasComposition")
	writeCSVOutputXTime(allFiles.gFile)
	
	allFiles.vProdFile = createFileDesc("producedNormVolumeCumulative.txt", "NormvolumeCumulative")
	writeCSVOutputXTime(allFiles.vProdFile)

	gasFlowPrevious = {}
end
if pSettings.reactorSetup.reactorType == "Downflow" then
	allFiles.outflowFile = createFileDesc("outflow.txt", "outflow")
	writeCSVOutputXTime(allFiles.outflowFile)
	writeOutputY(allFiles.outflowFile, "All Liquid", "[L/h]")
end
	allFiles.rStateFile = createFileDesc("reactorState.txt", "reactorState")
	writeCSVOutputXTime(allFiles.rStateFile)	
	
	writeOutputY(allFiles.rStateFile, "FOS", "[g/L]")
	writeOutputY(allFiles.rStateFile, "COD", "[g/L]")
	writeOutputY(allFiles.rStateFile, "pH", "[1]")

if outputSpecs.debug then
	allFiles.oFile = createFileDesc("dbg_avgEqValues.txt", "avgEqValues")
	writeCSVOutputXTime(allFiles.oFile)

	allFiles.nFile = createFileDesc("dbg_nitrogenRates.txt", "nitrogen")
	writeCSVOutputXTime(allFiles.nFile)
	
	allFiles.vProdHFile = createFileDesc("producedNormVolumeHourly.txt", "vProdHourly")
	writeCSVOutputXTime(allFiles.vProdHFile)
	
	volProdPrevious = {}

	allFiles.rrFile = createFileDesc("dbg_reactionrates.txt", "reactionRates")
	writeCSVOutputXTime(allFiles.rrFile)
	allFiles.gammaFile = createFileDesc("dbg_gamma.txt", "gammaValues")
	writeCSVOutputXTime(allFiles.gammaFile)
	
	allFiles.dbg_phContribution = createFileDesc("dbg_phContribution.txt", "dbg_phContribution")
	allFiles.dbg_phContribution.iof:write("Hions_Offset = "..Integral(Hions_Offset, u, pSettings.expert.geometry.subsets["reactorVolSubset"])/reactorVolume)
	writeCSVOutputXTime(allFiles.dbg_phContribution)

	allFiles.dbg_pP = io.open("partialPressures.txt", "w")
	allFiles.dbg_pP:write("# [h]\t[kPa]\n")
	allFiles.dbg_pP:write("# Time\t")
	
	allFiles.dbg_DensityFile = io.open("dbg_density.txt", "w")
	allFiles.dbg_DensityFile:write("# [h]\t[g/L]\n")
	allFiles.dbg_DensityFile:write("# Time\t")
	
	allFiles.codFile = io.open("reactorCODcontent.txt", "w")
	allFiles.codFile:write("# [h]\t[gCOD]\t[gCOD/L]\n")
	allFiles.codFile:write("# Time\tLiquid COD\tLiquid COD conc\tTotal COD\tTotal COD conc\tCOD Content only Inert (Lignin)\tCOD concentration only Inert (Lignin)")
	
	if outputSpecs.developer == false then
		allFiles.outputKey = io.open("subMO_RR_key", "w")
		allFiles.outputKey:write("Time\t=\t"..1)
	end
end

-- Preparing output files:
	local counterC = 2
	local counterR = 2
	local counterD = 2
	
	for sname, props in pairs (Eq_Subs_MOs) do
		if outputSpecs.developer then
			writeOutputY(allFiles.cFile, sname, "[g]")
			
			outputKey:write("\n"..sname.."\t=\t"..counterC)
			counterC = counterC+1
		end
		
		if outputSpecs.cDigestate then
			writeOutputY(allFiles.dFile, sname, "[g/L]")
			
			digestateKey:write("\n"..sname.."\t=\t"..counterD)
			counterD = counterD + 1
		end
		
		if outputSpecs.debug then
			writeOutputY(allFiles.oFile, sname, "[1]")
			if TraceContent["Nitrogen"][sname] then
				writeOutputY(allFiles.nFile, sname, "[g/L]")
			end
			if avg_phContribution[sname] then
				writeOutputY(allFiles.dbg_phContribution, sname, "-")
			end
		end
		
		if pSettings.reactorSetup.reactorType == "Downflow" then
			if Phase[sname] == "liquid" then
				if dbg_activateONEfct then
					writeOutputY(allFiles.outflowFile, sname, "[g/L]")
				else
					writeOutputY(allFiles.outflowFile, sname, "multiply by gridHeight at LowerBnd to get g/L!")
				end
			end
		end

		if (Phase[sname] == "gas" and extraGasphase) then 
			if outputSpecs.biogas then
				writeOutputY(allFiles.gFile, sname, "[vol%]")
				writeOutputY(allFiles.vProdFile, sname, "[NL]")
				gasFlowPrevious[sname] = 0
				if pSettings.checkpoint.doReadCheckpoint then
					gasFlowPrevious[sname] = checkpointAdditionalData.gasFlowPrevious[sname]
				end
			end
			if outputSpecs.developer then
				writeOutputY(allFiles.cFile, sname.."_gas", "[g]")
				writeOutputY(allFiles.cFile, sname.."_sum", "[g]")
				writeOutputY(allFiles.valveFile, sname, "[g/L/h]")

				outputKey:write("\n"..sname.."_gas\t=\t"..counterC)
				outputKey:write("\n"..sname.."_sum\t=\t"..counterC+1)
				counterC = counterC + 2
			end
			if outputSpecs.debug then
				writeOutputY(allFiles.oFile, sname.."_gas", "[1]")
				writeOutputY(allFiles.vProdHFile, sname, "[NL]")
				allFiles.dbg_pP:write(sname.."\t")
				volProdPrevious[sname] = 1000*Integral(props.startVal*Henry_Coeff_Inv[sname], u, pSettings.expert.geometry.subsets["gasPhaseSubset"])*factor_volCorrection/MolarMass[sname]*normFaktor
				if pSettings.checkpoint.doReadCheckpoint then
					volProdPrevious[sname] = checkpointAdditionalData.volProdPrevious[sname]
				end
			end	
		end
	end

	if outputSpecs.biogas then
		writeOutputY(allFiles.vProdFile, "Sum", "[NL]")
	end
	if outputSpecs.debug then
		for sname, props in pairs (Eq_Traces) do
			writeOutputY(allFiles.dFile, sname, "[g/L]")
			writeOutputY(allFiles.nFile, sname, "[g/L]")
			writeOutputY(allFiles.nFile, "SUM", "[g/L]")
			if avg_phContribution[sname] then
				writeOutputY(allFiles.dbg_phContribution, sname, "-")
			end
			digestateKey:write("\n"..sname.."\t=\t"..counterD)
			counterD = counterD + 1
			if sname == "Nitrogen" then
				writeOutputY(allFiles.dFile, "NH4N", "[g/L]")
				digestateKey:write("\n".."NH4N\t=\t"..counterD)
				counterD = counterD + 1
			end
		end
		writeOutputY(allFiles.dbg_phContribution, "Water", "-")
		writeOutputY(allFiles.dbg_phContribution, "Hions", "-")
		writeOutputY(allFiles.oFile, "Phi", "[1]")
		writeOutputY(allFiles.vProdHFile, "Sum", "[NL]")
		allFiles.dbg_pP:write("Sum\t")
		allFiles.dbg_DensityFile:write("rho_l\trho_s\t")
		
		for rname, props in pairs (Reaktionen) do
			writeOutputY(allFiles.rrFile, rname, "[g/h]")
			writeOutputY(allFiles.gammaFile, rname, "[]")
			outputKey:write("\n"..rname.."\t=\t"..counterR)
			counterR = counterR + 1
		end
		outputKey:close()
		digestateKey:close()
	end
-- Write keys for Outputfiles
outputkeyfile = io.open("outputFiles.lua", "w")
outputkeyfile:write("outputFiles = "..table.tostring( outFileKeys ) )
outputkeyfile:close()

-- Define function
function ComputeQuantities(u, step, time, dt)
	-- compute current factor for dissolved CO2 fraction
	avgCO2Factor=Integral(HEq:value()/((10^(-Dissociation.acids["Carbondioxide"])+HEq:value())), u, pSettings.expert.geometry.subsets["reactorVolSubset"])/reactorVolume
	
	if (step ==1 and outputSpecs.debug) then
		allFiles.gammaFile.iof:write("\n # Keq")
		for rname, props in pairs (Reaktionen) do
			if props.equiK then
				allFiles.gammaFile.iof:write("\t"..props.equiK)
			else
				allFiles.gammaFile.iof:write("\t -")
			end
		end
	end

	for filename, desc in pairs (allFiles) do
		if allFiles[filename] and allFiles[filename].iof then
			allFiles[filename].iof:write("\n"..time)
		elseif allFiles[filename] then
			allFiles[filename]:write("\n"..time)
		end
	end
	normVols = {}
	normVols["sum"]=0	
	normVolsHourly = {}
	normVolsHourly["sum"]=0
	partialP = {}
	partialP["sum"]=0
	fos = 0.0
	codLiq = 0.0
	codSum = 0.0
	inSum = 0.0

	if pSettings.reactorSetup.reactorType == "Downflow" then
		local gradPressure = IntegrateNormalGradientOnManifold(u, "p_l", pSettings.expert.geometry.subsets["reactorLowerBnd"], pSettings.expert.geometry.subsets["reactorVolSubset"])/areaBOT
		--IntegralNormalComponentOnManifold(p_lEq:gradient(), u, pSettings.expert.geometry.subsets["reactorLowerBnd"], pSettings.expert.geometry.subsets["reactorVolSubset"])
		outflowALL = permeability_l/viscosity_l * (gradPressure-Density["Water"]*gravitation)*factor_volCorrection*areaBOT
		allFiles.outflowFile.iof:write("\t"..outflowALL)
		if dbg_activateONEfct then
			local oneValGrad = IntegrateNormalGradientOnManifold(u, "one", pSettings.expert.geometry.subsets["reactorLowerBnd"], pSettings.expert.geometry.subsets["reactorVolSubset"])/areaBOT
			gridHeightAtBot = 1.0/oneValGrad
		else
			gridHeightAtBot = 1.0
		end
	end

	for sname, props in pairs (Eq_Subs_MOs) do
		prdc = Integral(props.conc, u, pSettings.expert.geometry.subsets["reactorVolSubset"])
		
		
		if outputSpecs.cDigestate then
			allFiles.dFile.iof:write("\t"..prdc/reactorVolume)
			if TraceContent["Nitrogen"][sname] then
				inSum = inSum +  prdc/reactorVolume*TraceContent["Nitrogen"][sname]
			end
		end
		
		prdc = prdc*factor_volCorrection
		prdo = Integral(props.eqname:value(), u, pSettings.expert.geometry.subsets["reactorVolSubset"])/reactorVolume
		
		if outputSpecs.developer then
			allFiles.cFile.iof:write("\t"..prdc)
		end
		if outputSpecs.debug then
			allFiles.oFile.iof:write("\t"..prdo)
			if avg_phContribution[sname] then
				allFiles.dbg_phContribution.iof:write("\t"..Integral(avg_phContribution[sname], u, pSettings.expert.geometry.subsets["reactorVolSubset"])/reactorVolume)
			end
			if TraceContent["Nitrogen"][sname] then
				allFiles.nFile.iof:write("\t"..prdc/reactorVolume/factor_volCorrection*TraceContent["Nitrogen"][sname])
			end
		end
		
		if pSettings.reactorSetup.reactorType == "Downflow" then
			if Phase[sname] == "liquid" then
				local outflowLiquid = IntegralNormalComponentOnManifold(props.eqname:gradient(), u, pSettings.expert.geometry.subsets["reactorLowerBnd"], pSettings.expert.geometry.subsets["reactorVolSubset"])/areaBOT*gridHeightAtBot*Density["Water"]
				allFiles.outflowFile.iof:write("\t"..math.abs(outflowLiquid))
			end
		end
		
		codSum = codSum + prdc*COD[sname]
		if(Phase[sname] ~= "solid") then
			codLiq = codLiq + prdc*COD[sname]
		end
		if OutputTag[sname] == "acid" then
			fos = fos + prdc*AceticEquivalentFactor[sname]
		end
		
		if (Phase[sname] == "gas" and extraGasphase) then
			prdcgas = Integral(props.peqname:value()*Henry_Coeff_Inv[sname], u, pSettings.expert.geometry.subsets["gasPhaseSubset"])*factor_volCorrection
			prdogas = Integral(props.peqname:value()*Henry_Coeff_Inv[sname], u, pSettings.expert.geometry.subsets["gasPhaseSubset"])/headSpaceVolume
			prdFlowGas = - Integral(props.rate_valve, u, pSettings.expert.geometry.subsets["gasPhaseSubset"])

			if outputSpecs.developer then
				allFiles.cFile.iof:write("\t"..prdcgas)
				allFiles.cFile.iof:write("\t"..prdc+prdcgas)
				allFiles.valveFile.iof:write("\t"..prdFlowGas/headSpaceVolume)
			end
			if outputSpecs.debug then
				allFiles.oFile.iof:write("\t"..prdogas)
			end
			
			normVols[sname] = 1000*prdcgas/MolarMass[sname]*normFaktor -- Faktor 1000 für Umrechung von m^3 in L
			
			if outputSpecs.biogas then
				normVols[sname] = normVols[sname] + prdFlowGas*dt/MolarMass[sname]*normFaktor*1000*factor_volCorrection + gasFlowPrevious[sname]
				allFiles.vProdFile.iof:write("\t"..normVols[sname])
				gasFlowPrevious[sname] = gasFlowPrevious[sname] + prdFlowGas*dt/MolarMass[sname]*normFaktor*1000*factor_volCorrection
				if sname == "Methane" then
					outputfilename = util.GetParam("-communicationDir").."/"..evaluationId.."_measurement.csv"
					file = io.open(outputfilename, "a")
					file:write(step..","..time..","..normVols[sname].."\n")
					file:close()
				end
			end
			normVols["sum"] = normVols["sum"] + normVols[sname]

			if outputSpecs.debug then
				normVolsHourly[sname] = (normVols[sname]-volProdPrevious[sname])/dt
				normVolsHourly["sum"] = normVolsHourly["sum"] + normVolsHourly[sname] 
				volProdPrevious[sname]=normVols[sname] --reset previous volProd for next timestep
				partialP[sname] = gasConstant*operatingTemperature/MolarMass[sname]*prdcgas/headSpaceVolume/factor_volCorrection
				partialP["sum"] = partialP["sum"] + partialP[sname]
				
				allFiles.vProdHFile.iof:write("\t"..normVolsHourly[sname])
				allFiles.dbg_pP:write("\t"..partialP[sname])
			end
		end
	end

	if outputSpecs.biogas then
		myDataForCheckpoint.gasFlowPrevious = gasFlowPrevious
		myDataForCheckpoint.volProdPrevious = volProdPrevious
	end

	allFiles.rStateFile.iof:write("\t"..fos/pSettings.reactorSetup.realReactorVolume.."\t"..codLiq/pSettings.reactorSetup.realReactorVolume)
	avgPHvalue = -math.log10(Integral(HEq:value(), u, pSettings.expert.geometry.subsets["reactorVolSubset"])/reactorVolume)
	allFiles.rStateFile.iof:write("\t"..avgPHvalue)
	if outputSpecs.biogas then
		for sname, props in pairs (Eq_Subs_MOs) do
			if (Phase[sname] == "gas" and extraGasphase) then
				allFiles.gFile.iof:write("\t"..normVols[sname]/normVols["sum"]*100)
			end
		end
		allFiles.vProdFile.iof:write("\t"..normVols["sum"])
	end
	
	if outputSpecs.debug then
		prdoPHI = Integral(phiEq:value(), u, pSettings.expert.geometry.subsets["reactorVolSubset"])/reactorVolume
		allFiles.oFile.iof:write("\t"..prdoPHI)
	
		for sname, props in pairs (Eq_Traces) do
			prdc = Integral(props.eqname:value(), u, pSettings.expert.geometry.subsets["reactorVolSubset"])
			allFiles.dFile.iof:write("\t"..prdc/reactorVolume)
			inSum = inSum +  prdc/reactorVolume
			allFiles.nFile.iof:write("\t"..prdc/reactorVolume.."\t"..inSum)
			print("Sum of all inorganic nitrogen is "..inSum)
			if avg_phContribution[sname] then
				allFiles.dbg_phContribution.iof:write("\t"..Integral(avg_phContribution[sname], u, pSettings.expert.geometry.subsets["reactorVolSubset"])/reactorVolume)
			end
			if sname == "Nitrogen" then
				local nh4n = props.eqname:value()*HEq:value()/(10^(-Dissociation.bases["Nitrogen"])+HEq:value())
				prdc = Integral(nh4n, u, pSettings.expert.geometry.subsets["reactorVolSubset"])
				allFiles.dFile.iof:write("\t"..prdc/reactorVolume)
			end
		end
		allFiles.dbg_phContribution.iof:write("\t"..Integral(avg_phContribution["Water"], u, pSettings.expert.geometry.subsets["reactorVolSubset"])/reactorVolume)
		allFiles.dbg_phContribution.iof:write("\t"..Integral(HEq:value(), u, pSettings.expert.geometry.subsets["reactorVolSubset"])/reactorVolume)

		dbgdensityL = Integral(rho_l, u, pSettings.expert.geometry.subsets["reactorVolSubset"])/reactorVolume
		dbgdensityS = Integral(rho_s, u, pSettings.expert.geometry.subsets["reactorVolSubset"])/reactorVolume
		allFiles.dbg_DensityFile:write("\t"..dbgdensityL.."\t"..dbgdensityS)
		
		allFiles.codFile:write("\t"..codLiq.."\t"..codLiq/pSettings.reactorSetup.realReactorVolume.."\t"..codSum.."\t"..codSum/pSettings.reactorSetup.realReactorVolume)
		if Eq_Subs_MOs["Lignin"] then codInert = COD["Lignin"]*Integral(Eq_Subs_MOs["Lignin"].conc, u, pSettings.expert.geometry.subsets["reactorVolSubset"])*factor_volCorrection
		allFiles.codFile:write("\t"..codInert.."\t"..codInert/pSettings.reactorSetup.realReactorVolume) end
	
		allFiles.vProdHFile.iof:write("\t"..normVolsHourly["sum"])
		allFiles.dbg_pP:write("\t"..partialP["sum"])
		for sname, props in pairs (Reaktionen) do
			intrate = Integral(props.rate, u, pSettings.expert.geometry.subsets["reactorVolSubset"])*factor_volCorrection
			allFiles.rrFile.iof:write("\t"..intrate)
			if props.gamma then 
				intgamma = Integral(props.gamma, u, pSettings.expert.geometry.subsets["reactorVolSubset"])/reactorVolume	
			else
				intgamma = 0
			end
			allFiles.gammaFile.iof:write("\t"..intgamma)
		end
		if FEDAMOUNT ~= 0 then
			dbg_feed:write("\n"..time.."\t"..FEDAMOUNT)
		end
	end
end
