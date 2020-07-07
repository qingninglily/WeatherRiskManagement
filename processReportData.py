from getReportData import getReportData
import pandas as pd
import numpy as np
import scipy.stats
import sys
from datetime import datetime

def processReportData(sitename):
	reportdata = getReportData(sitename)

	FirstDCsize=int(reportdata["sysinfo"]["DC size"])
	Degradation=reportdata["sysinfo"]["Yearly Module Degradation"]
	degradation=float(Degradation.strip("%").strip("-"))/100
	
	fulldatamonths=reportdata["fulldatamonths"]
	fulldatapoints=reportdata["fulldatapoints"]
	recentdatamonths=reportdata["recentdatamonths"]
	altusbaseline=reportdata['altusbaseline']
	percentup=reportdata['percentUp']
	
	tmy=reportdata["tmy"]
	production=reportdata["production"]
	startdate=reportdata['sysinfo']["Analysis Start Date"]
	Maturity=int(reportdata['sysinfo']['Maturity'])

	POA=reportdata["sysinfo"]['POA (kWh/m^d2)']#Baseline POA
	POAfactor=float(reportdata['sysinfo']['P50 POA factor']) #one number: 1.14
	P50_POA=float(reportdata['sysinfo']['P50 POA'])#1590.3
	PRratio=float(reportdata['sysinfo']['Performance Ratio'].strip('%'))/100#81.61%
	NetOutput=reportdata['sysinfo']['Net Output (mWh)']
	P50_GHI=float(reportdata['sysinfo']['P50 GHI'])
	firstmonth=reportdata["fulldatamonths"][11]
	firstfulldatamonth=reportdata["fulldatamonths"][0]
	firstrecentdatamonth=reportdata["recentdatamonths"][0]

#1.2 Irradaince table
	monthlyibmdata={}
	monthlynreldata={}
	monthlyalsodata={}
	for i in range(1,13):
		monthlyibmdata[i]=[]
		monthlynreldata[i]=[]
		monthlyalsodata[i]=[]

	for (t,d) in zip(fulldatamonths,fulldatapoints):
		if t=='1/2019':
			break
		month=int(t.split('/')[0])
		if 'ibm' in d.keys():
			monthlyibmdata[month].append(d["ibm"])
		if 'nrel' in d.keys():
			monthlynreldata[month].append(d['nrel'])
		if 'also' in d.keys():
			monthlyalsodata[month].append(d['also'])

	ibmavgmonth=[np.mean(value) for value in monthlyibmdata.values()]
	nrelavgmonth=[np.mean(value) for value in monthlynreldata.values()]
	ibmstdmonth=[np.std(value) for value in monthlyibmdata.values()]
	nrelstdmonth=[np.std(value) for value in monthlynreldata.values()]
	alsoavgmonth=[(np.mean(value) if len(value) > 0 else 0) for value in monthlyalsodata.values()]
	
	Irradiance={'InvestmentBaseline':altusbaseline,'NSRDB Average':nrelavgmonth,'TWC (IBM) Average)':ibmavgmonth,'TMY':tmy}

#1.3 Base Year Scenario
#1.3.1 Investment Irradiance Baseline Scenario
	poabaseline=[]
	netprodbaseline=[]
	for i in range(1,13):
		poabaseline.append(float(POA[str(i)]))
		netprodbaseline.append(float(NetOutput[str(i)]))

	poafactor=[]
	PR=[]
	MonthlyOutputContribution_baseline=[]
	for (base,p,noutput) in zip(altusbaseline,poabaseline,netprodbaseline):
		poafactor.append(p/float(base))
		PR.append(noutput/(p*FirstDCsize/1000))
		PRpercent=['{:.2%}'.format(i) for i in PR]
		MonthlyOutputContribution_baseline.append('{:.2%}'.format(noutput/np.sum(netprodbaseline)))

	BaselineScenario={'poabaseline':poabaseline,'poafactor':poafactor,'netprodbaseline':netprodbaseline,'PR':PRpercent,'MonthlyOutputContribution_baseline':MonthlyOutputContribution_baseline}

#1.3.2NSRDB Avgerage Scenario
	poanrel=[a*b for (a,b) in zip(nrelavgmonth,poafactor)]
	netprodnrel=[c*d*FirstDCsize/1000 for (c,d) in zip(poanrel,PR)]
	PRrationrel=[a/(FirstDCsize*b/1000) for (a,b) in zip(netprodnrel,poanrel)]
	PRnrelpercent=['{:.2%}'.format(i) for i in PRrationrel]
	MonthlyOutputContribution_nrel=['{:.2%}'.format(i/np.sum(netprodnrel)) for i in netprodnrel]

	NRELScenario={'poanrel':poanrel,'netprodibm':netprodnrel,'PRrationrel':PRnrelpercent,'MonthlyOutputContribution_nrel':MonthlyOutputContribution_nrel}

#1.3.3TWC(IBM) Average Scenario
	poaibm=[a*b for (a,b) in zip(ibmavgmonth,poafactor)]
	netprodibm=[c*d*FirstDCsize/1000 for (c,d) in zip(poaibm,PR)]	
	PRratioibm=[a/(FirstDCsize*b/1000) for (a,b) in zip(netprodibm,poaibm)]
	PRibmpercent=['{:.2%}'.format(i) for i in PRratioibm]
	MonthlyOutputContribution_ibm=['{:.2%}'.format(i/np.sum(netprodibm)) for i in netprodibm]

	IBMScenario={'poaibm':poaibm,'netprodibm':netprodibm,'PRratioibm':PRibmpercent,'MonthlyOutputContribution_ibm':MonthlyOutputContribution_ibm}

#1.3.4 TMY Scenario
	poatmy=[a*b for (a,b) in zip(tmy,poafactor)]
	netprodtmy=[c*d*FirstDCsize/1000 for (c,d) in zip(poatmy,PR)]	
	PRratiotmy=[a/(FirstDCsize*b/1000) for (a,b) in zip(netprodtmy,poatmy)]
	PRtmypercent=['{:.2%}'.format(i) for i in PRratiotmy]
	MonthlyOutputContribution_tmy=['{:.2%}'.format(i/np.sum(netprodtmy)) for i in netprodtmy]

	TMYScenario={'poatmy':poatmy,'netprodtmy':netprodtmy,'PRratiotmy':PRtmypercent,'MonthlyOutputContribution_tmy':MonthlyOutputContribution_tmy}

#1.3.5 Weather Station (Also) Scenario
	poaalso=[a*b for (a,b) in zip(alsoavgmonth,poafactor)]
	netprodalso=[c*d*FirstDCsize/1000 for (c,d) in zip(poaalso,PR)]
	npasum = np.sum(netprodalso) if np.sum(netprodalso) != 0 else 1
	PRratioalso=[(a/(FirstDCsize*b/1000) if b != 0 else 0) for (a,b) in zip(netprodalso,poaalso)]
	PRalsopercent=['{:.2%}'.format(i) for i in PRratioalso]
	MonthlyOutputContribution_also=['{:.2%}'.format(i/npasum) for i in netprodalso]

	AlsoScenario={'poaalso':poaalso,'netprodalso':netprodalso,'PRratioalso':PRalsopercent,'MonthlyOutputContribution_also':MonthlyOutputContribution_also}

#1.4 Lifetime Production table
	AdjustedDCsize=[]
	for i in range(Maturity+1):
		AdjustedDCsize.append(FirstDCsize*((1-degradation)**i))
	startyear=int(datetime.strptime(startdate,"%m/%d/%Y").year)
	endyear=startyear+Maturity
	DCsizeDict={a:b for (a,b) in zip(range(startyear,endyear+1),AdjustedDCsize)}
	AdjustedNominalProd=[i*P50_POA/1000 for i in AdjustedDCsize]
	AdjustedYearlyInvBaselineProd=[PRratio*i for i in AdjustedNominalProd]
	AdjustedInvBaselineProdDict={a:b for (a,b) in zip(range(startyear,endyear+1),AdjustedYearlyInvBaselineProd)}
	Year=range(startyear,endyear+1)
	YearOperation=range(Maturity+1)
	LifetimeProdTable={'Year':Year,'YearOperation':YearOperation,'AdjustedDCsize':DCsizeDict,'AdjustedNominalProd':AdjustedNominalProd,'AdjustedYearlyInvBaselineProd':AdjustedYearlyInvBaselineProd}

#2 PED Irradiance Baseline Analysis
#2.1 Monthly Irradiance
	# Get full datasets for nrel and ibm
	nrelfulldatapoints=[]
	ibmfulldatapoints=[]
	for (point,d) in zip(fulldatapoints,fulldatamonths):
		if d=='1/2019':
			break
		if 'ibm' in point.keys():
			ibmfulldatapoints.append(point["ibm"])
		if 'nrel' in point.keys():
			nrelfulldatapoints.append(point["nrel"])

	#Get the PED Calibration and Monthly standard deviation in percentage for each month
	PED_Calibration=[]
	MonthlyStDev=[]
	nrelirrweight=reportdata["sysinfo"]["GHI Weights"]["NSRDB Irradiance Weight"]
	ibmirrweight=reportdata["sysinfo"]["GHI Weights"]["TWC (IBM) Irradiance Weight"]
	tmyirrweight=reportdata["sysinfo"]["GHI Weights"]["TMY Irradiance Weight"]
	nrelstdweight=reportdata["sysinfo"]["StDev Weights"]["NSRDB Standard Deviation Weight"]
	ibmstdweight=reportdata["sysinfo"]["StDev Weights"]["TWC (IBM) Standard Deviation Weight"]
	tmystdweight=reportdata["sysinfo"]["StDev Weights"]["TMY Standard Deviation Weight"]
	modeluncertainty=reportdata["sysinfo"]["Source Data Model Uncertainty"]

	for (NREL,IBM,TMY) in zip(nrelavgmonth,ibmavgmonth,tmy):
		PED_Calibration.append(NREL*nrelirrweight+IBM*ibmirrweight+TMY*tmyirrweight)
	for (NREL,IBM,calibration,baseline) in zip(nrelstdmonth,ibmstdmonth,PED_Calibration,altusbaseline):
		std=np.sqrt((NREL*nrelstdweight+IBM*ibmstdweight)**2+(baseline*modeluncertainty)**2)/calibration
		MonthlyStDev.append("{:.2%}".format(std))

	Monthly_Irradiance={"InvIrrBaseline":altusbaseline,"PED_Calibration":PED_Calibration,"MonthlyStDev":MonthlyStDev}

#2.2 PED Irradiance Analysis Summary
	#Calculate the 12 months straight rolling numbers and then get the Standard Deviation
	nrelmonthrolling=[]
	ibmmonthrolling=[]
	nrelmonthsum=0
	ibmmonthsum=0
	for i in range(0,len(nrelfulldatapoints)-11):
		for r in range(i,i+12):
			nrelmonthsum+=nrelfulldatapoints[r]
		nrelmonthrolling+=[nrelmonthsum]
		nrelmonthsum=0
	for i in range(0,len(ibmfulldatapoints)-11):
		for r in range(i,i+12):
			ibmmonthsum+=ibmfulldatapoints[r]
		ibmmonthrolling+=[ibmmonthsum]
		ibmmonthsum=0

	monthrolling=[]
	nrelweight=1
	ibmweight=1
	for c in range(max(len(nrelmonthrolling),len(ibmmonthrolling))):
		if c<len(nrelmonthrolling):
			monthrolling.append(nrelmonthrolling[c]*nrelweight)
		else:
			monthrolling.append(ibmmonthrolling[c]*ibmweight)
	
	#Calculate the PED calibrated Irradiance
	PED_Calibrated=np.sum(PED_Calibration)	

	#Get the Standard deviation in percentge with PED calibrated irradiance
	PED_StDev=np.sqrt((np.std(nrelmonthrolling)*nrelstdweight+np.std(ibmmonthrolling)*ibmstdweight)**2+(PED_Calibrated*modeluncertainty)**2)
	StDev="{:.2%}".format(PED_StDev/PED_Calibrated)
	#Get the min and max year of irradiance
	MinCalendarYearIrr=np.min([np.min(nrelmonthrolling),np.min(ibmmonthrolling)])
	MaxCalendarYearIrr=np.max([np.max(nrelmonthrolling),np.max(ibmmonthrolling)])
	#Sum up the monthly Altus baseline
	sumaltusbaseline=np.sum(altusbaseline)
	#Get the left and right side of possibility
	left=scipy.stats.norm(loc=PED_Calibrated,scale=PED_StDev).cdf(sumaltusbaseline)
	leftpossibility="{:.2%}".format(left)
	rightpossibility="{:.2%}".format(1-left)
	#Put all above things into analysis summary arrary
	PED_Irradiance_Analysis_Summary={"PED_Calibrated":PED_Calibrated,"PED_StDev":PED_StDev,"StDev":StDev,"MinCalendarYearIrr":MinCalendarYearIrr,"MaxCalendarYearIrr":MaxCalendarYearIrr,"sumaltusbaseline":sumaltusbaseline,"leftpossibility":leftpossibility,"rightpossibility":rightpossibility}

#3 Irradiance Analysis
# 3.1 Irradiance Table
#Get weather station Irradiance
	alsofulldatapoints=[]
	for point in fulldatapoints:
		try:
			alsofulldatapoints.append(point["also"])
		except KeyError:
			pass
#Get PED Calibrated Irradiance
	IrradianceTable={}
	WeatherStationIrr=[]
	PEDcalibratedIrr=[]
	InvIrrBaseline=[]
	PEDBaseline=[]

	monlens=[31,28,31,30,31,30,31,31,30,31,30,31]
	startmon=int(startdate.split('/')[0])
	startday=int(startdate.split('/')[1])
	adjust=(monlens[startmon-1]-startday+1)/monlens[startmon-1]

	yearlybaseline={}
	yearlyweather={}
	yearlycalibrated={}	
	yearlypedcalibration={}
	firstyear=int(recentdatamonths[0].split('/')[1])
	lastyear=int(recentdatamonths[-1].split('/')[1])
	for i in range(firstyear,lastyear+1):
		yearlybaseline[i]=[]
		yearlyweather[i]=[]
		yearlycalibrated[i]=[]
		yearlypedcalibration[i]=[]
	recentyears=[]

	n=0
	for (d,full) in zip(fulldatamonths,fulldatapoints):
		if d in recentdatamonths:		
			n+=1
			mon=int(d.split('/')[0])	
			year=int(d.split('/')[1])
			if year not in recentyears:
				recentyears.append(year)
			if n==1:	
				yearlypedcalibration[year].append(PED_Calibration[mon-1]*adjust)
				yearlybaseline[year].append(altusbaseline[mon-1]*adjust)
			else:	
				yearlypedcalibration[year].append(PED_Calibration[mon-1])
				yearlybaseline[year].append(altusbaseline[mon-1])
			try:
				if n==1:
					yearlyweather[year].append(full['also']*adjust)
				else:
					yearlyweather[year].append(full['also'])
			except KeyError:
				yearlyweather[year].append(0)
			try:
				if n==1:
					yearlycalibrated[year].append(full['ibm']*adjust)
				else:
					yearlycalibrated[year].append(full['ibm'])
			except KeyError:
				yearlycalibrated[year].append(0)

	for i in list(yearlybaseline.values()):	
		InvIrrBaseline+=i
	for i in list(yearlycalibrated.values()):
		PEDcalibratedIrr+=i
	for i in list(yearlyweather.values()):
		WeatherStationIrr+=i
	for i in list(yearlypedcalibration.values()):
		PEDBaseline+=i

	yearlysumbaseline=[np.sum(i) for i in list(yearlybaseline.values())]
	yearlysumweather=[np.sum(i) for i in list(yearlyweather.values())]
	yearlysumcalibrated=[np.sum(i) for i in list(yearlycalibrated.values())]
	yearlysumpedcalibration=[np.sum(i) for i in list(yearlypedcalibration.values())]

	IrradianceTable={"recentyears":recentyears,"yearlysumbaseline":yearlysumbaseline,"yearlysumpedcalibration":yearlysumpedcalibration,"yearlysumweather":yearlysumweather,"yearlysumcalibrated":yearlysumcalibrated,"InvIrrBaseline":InvIrrBaseline,"PEDBaseline":PEDBaseline,"WeatherStationIrr":WeatherStationIrr,"PEDcalibratedIrr":PEDcalibratedIrr}
	
#3.2 Cumulative Irradiance Comparison
	cumbaseline=0
	cumcalibrated=0
	cumPED_versus_cumaltusbaseline=[]	

	for base,calibrated in list(zip(InvIrrBaseline,PEDcalibratedIrr)):
		cumbaseline+=base
		cumcalibrated+=calibrated
		cumPED_versus_cumaltusbaseline+=["{:.0%}".format(cumcalibrated/cumbaseline)]

#4 Production analysis
#4.1 production table
	InvProdBaseline=[]
	ActualProd=production
	PED_CalibratedProd=[]
	WeatherStationProd=[]
	DCsize=FirstDCsize
	AdjustedProd=[]
	Missing=[]

	YearlyAdjustedProd={}
	YearlyMissing={}
	totalbase={}
	totalactual={}
	totalped={}
	totalweather={}
	for i in range(firstyear,lastyear+1):
		totalbase[i]=[]
		totalactual[i]=[]
		totalped[i]=[]
		totalweather[i]=[]
		YearlyAdjustedProd[i]=[]
		YearlyMissing[i]=[]

	n=0
	for (t,calibratedprod,actual,weatherstation,up) in zip(recentdatamonths,PEDcalibratedIrr,production,WeatherStationIrr,percentup):
		n+=1
		mon=int(t.split('/')[0])
		year=int(t.split('/')[1])
		if n==1:
			totalbase[year].append(DCsizeDict[year]*altusbaseline[mon-1]*poafactor[mon-1]*PR[mon-1]*adjust)
		else:
			totalbase[year].append(DCsizeDict[year]*altusbaseline[mon-1]*poafactor[mon-1]*PR[mon-1])
		b=DCsizeDict[year]*calibratedprod*poafactor[mon-1]*PRratioibm[mon-1]
		totalped[year].append(b)
		totalweather[year].append(DCsizeDict[year]*weatherstation*poafactor[mon-1]*PRratioalso[mon-1])
		totalactual[year].append(actual)
		YearlyAdjustedProd[year].append(actual+(1-up)*b)
		YearlyMissing[year].append((1-up)*b)

	for i in list(totalbase.values()):
		InvProdBaseline+=i
	for i in list(totalped.values()):
		PED_CalibratedProd+=i
	for i in list(totalweather.values()):
		WeatherStationProd+=i
	for i in list(YearlyAdjustedProd.values()):
		AdjustedProd+=i
	for i in list(YearlyMissing.values()):
		Missing+=i

	sumbase=[np.sum(i) for i in list(totalbase.values())]
	sumactual=[np.sum(i) for i in list(totalactual.values())]	
	sumped=[np.sum(i) for i in list(totalped.values())]	
	sumweather=[np.sum(i) for i in list(totalweather.values())]
	sumadjustedprod=[np.sum(i) for i in list(YearlyAdjustedProd.values())]
	summissing=[np.sum(i) for i in list(YearlyMissing.values())]

	Production_Analysis={"recentyears":recentyears,"sumbase":sumbase,"sumactual":sumactual,"summissing":summissing,"sumped":sumped,"sumweather":sumweather,"sumadjustedprod":sumadjustedprod,"InvProdBaseline":InvProdBaseline,"ActualProd":ActualProd,"Missing":Missing,"PED_CalibratedProd":PED_CalibratedProd,"WeatherStationProd":WeatherStationProd,"AdjustedProd":AdjustedProd}
	#print('totalbase',totalbase)

#4.2 Cumulative Production Analysis
	Actual_vs_BaselineProd=[]
	Actual_vs_CalibratedProd=[]
	CalibratedProd_vs_BaselineProd=[]
	MonthlyActual_Predictive=[]
	AdjustedActual_vs_Predictive=[]
	AdjustedActual_vs_Baseline=[]

	cumactual=0
	cumbaseline=0
	cumcalibrated=0
	cumadjustedprod=0
	prodposition=[]
	for (d,actualprod,baselineprod,pedcalibratedprod,adjustedprod) in zip(recentdatamonths,ActualProd,InvProdBaseline,PED_CalibratedProd,AdjustedProd):
		cumactual+=actualprod
		cumbaseline+=baselineprod
		cumcalibrated+=pedcalibratedprod
		cumadjustedprod+=adjustedprod
		prodposition.append(cumactual-cumbaseline)
		Actual_vs_BaselineProd.append('{:.1%}'.format((cumactual/cumbaseline)-1))
		Actual_vs_CalibratedProd.append('{:.0%}'.format((cumactual/cumcalibrated)-1))
		CalibratedProd_vs_BaselineProd.append('{:.1%}'.format((cumcalibrated/cumbaseline)-1))	
		AdjustedActual_vs_Baseline.append('{:.1%}'.format((cumadjustedprod/cumbaseline)-1))
		if pedcalibratedprod==0:
			MonthlyActual_Predictive.append('0%')
			AdjustedActual_vs_Predictive.append('0%')
		else:
			MonthlyActual_Predictive.append('{:.0%}'.format(actualprod/pedcalibratedprod))
			AdjustedActual_vs_Predictive.append('{:.0%}'.format(adjustedprod/pedcalibratedprod))

	YearlyActual_Predictive=['{:.0%}'.format(a/b) for (a,b) in zip(sumactual,sumped)]
	YearlyAdjustedActual_Predictive=['{:.0%}'.format(a/b) for (a,b) in zip(sumadjustedprod,sumped)]

	Cumulative_Production_Analysis={"Actual_vs_BaselineProd":Actual_vs_BaselineProd,"Actual_vs_CalibratedProd":Actual_vs_CalibratedProd,"CalibratedProd_vs_BaselineProd":CalibratedProd_vs_BaselineProd}

#5 Current Position
#5.1 Production Position
	start=datetime.strptime(startdate,"%m/%d/%Y").date()
	end=start.replace(start.year+Maturity)
	#today=datetime(2018,12,31).date()
	daysdiff=(end-today).days
	Inv_Maturity=round(daysdiff/365,1)
	
	strtoday=str(today.month)+'/'+str(today.year)
	ProdPosition=0
	for (i,n) in zip(recentdatamonths,prodposition):
		if i==strtoday:
			ProdPosition+=n
			break
		else:
			pass

	TotalEstLostProd=np.sum(summissing)
	
	startindex=today.year+1-start.year
	RemainingBaseline=[]	
	AvgProdPerUnit=[]
	for i in range(startindex,Maturity+1):
		RemainingBaseline.append(AdjustedYearlyInvBaselineProd[i])	
		AvgProdPerUnit.append(POAfactor*PRratio*AdjustedDCsize[i])

	AvgMonthProdPosition=ProdPosition/((np.mean(RemainingBaseline)*1000)/12)
	CurrentPosition={"Inv_Maturity":str(Inv_Maturity)+'y',"ProdPosition":ProdPosition,"TotalEstLostProd":TotalEstLostProd,"AvgMonthProdPosition":AvgMonthProdPosition}
	
#5.2Prodcution Position Relative to Investment Production Baseline

	PPUI=ProdPosition/np.mean(AvgProdPerUnit)

	years=[1]+[i*5 for i in range(1,int(Inv_Maturity//5)+1)]
	
	PPM=[]
	Baseline=[]
	for i in range(startyear+1,endyear+1):
		Baseline.append(AdjustedInvBaselineProdDict[i]*1000)
	CumNormProbITM_PEDCalibratedIrr=[]
	CumNormProbITM_InvBaseline=[]
	for i in years+[Inv_Maturity]:
		
			#totalbaseline+=[DCsizeDict[int(today.year)+i]*altusbaseline[mon]*poafactor[mon]*PR[mon]]
		PPM.append('{:.0%}'.format((np.mean(Baseline)*i+ProdPosition)/(np.mean(Baseline)*i)))	
		
#5.2.1 calibrating the cumulative peobability of reaching at least PPM of 1
		ReqTotalIrrPPM=P50_GHI*i-PPUI
		SumTotalPEDAvgIrr=PED_Calibrated*i
		CumPEDStDev=np.sqrt((PED_StDev**2)*i)
#5.2.2 Cumulative Probability	
		CumNormProbITM_PEDCalibratedIrr.append('{:.0%}'.format(1-scipy.stats.norm(loc=SumTotalPEDAvgIrr,scale=CumPEDStDev).cdf(ReqTotalIrrPPM)))
		CumNormProbITM_InvBaseline.append('{:.0%}'.format(1-scipy.stats.norm(loc=P50_GHI*i,scale=CumPEDStDev).cdf(ReqTotalIrrPPM)))

	PPIM=PPM.pop(-1)
	PEDCalibratedIrr_Maturity=CumNormProbITM_PEDCalibratedIrr.pop(-1)
	InvBaseline_Maturity=CumNormProbITM_InvBaseline.pop(-1)
	years=[str(i)+'y' for i in years]
	Inv_Maturity=str(Inv_Maturity)+'y'
	ProdPosition_RelativeTo_InvProdBaseline={"Inv_Maturity":Inv_Maturity,"PPIM":PPIM,"years":years,"PPM":PPM}
	CumNormProbReachinghundredPPM={"Inv_Maturity":Inv_Maturity,"PEDCalibratedIrr_Maturity":PEDCalibratedIrr_Maturity,"InvBaseline_Maturity":InvBaseline_Maturity,"years":years,"CumNormProbITM_PEDCalibratedIrr":CumNormProbITM_PEDCalibratedIrr,"CumNormProbITM_InvBaseline":CumNormProbITM_InvBaseline}


#System Availability
	recentdatayears=list(range(firstyear,lastyear+1))
	MaxOperationalDays=pd.Series(np.zeros(lastyear-firstyear+1),index=range(firstyear,lastyear+1))
	SystemClosureDays=pd.Series(np.zeros(lastyear-firstyear+1),index=range(firstyear,lastyear+1))
	NotFullOperationDays=pd.Series(np.zeros(lastyear-firstyear+1),index=range(firstyear,lastyear+1))
	MonthlyHundredUpTime=[]
	for m,d,p,t in list(zip(reportdata["recentdatamonths"],reportdata["totalDays"],reportdata["partialDown"],reportdata["totallyDown"])):
		Year=int(m.split('/')[1])
		MaxOperationalDays.loc[Year]+=d
		SystemClosureDays.loc[Year]+=t
		NotFullOperationDays.loc[Year]+=p+t
		if d==0:
			MonthlyHundredUpTime.append("0%")
		else:
			MonthlyHundredUpTime.append("{:.0%}".format((d-p-t)/d))

	FullOperationPercent=['{:.0%}'.format((totaldays-notfulloper)/totaldays) for (totaldays,notfulloper) in zip(MaxOperationalDays,NotFullOperationDays)]
	SystemAvailability={"recentdatayears":recentdatayears,"MaxOperationalDays":list(MaxOperationalDays),"SystemClosureDays":list(SystemClosureDays),"NotFullOperationDays":list(NotFullOperationDays),"FullOperationPercent":FullOperationPercent}

#Actual_vs_Predictive Est Prod
	Actual_vs_Predictive_EstProd={"recentdatamonths":recentdatamonths,"MonthlyActual_Predictive":MonthlyActual_Predictive,"MonthlyHundredUpTime":MonthlyHundredUpTime,"recentdatayears":recentdatayears,"YearlyActual_Predictive":YearlyActual_Predictive,"AdjustedActual_vs_Predictive":AdjustedActual_vs_Predictive,"YearlyAdjustedActual_Predictive":YearlyAdjustedActual_Predictive,"AdjustedActual_vs_Baseline":AdjustedActual_vs_Baseline,"YearlyHundredUpTime":FullOperationPercent}

	
	return {"sysinfo":reportdata["sysinfo"],"Irradiance":Irradiance,"BselineScenario":BaselineScenario,"NRELScenario":NRELScenario,"IBMScenario":IBMScenario,"TMYScenario":TMYScenario,"AlsoScenario":AlsoScenario,"LifetimeProdTable":LifetimeProdTable,"Monthly_Irradiance":Monthly_Irradiance,"firstmonth":firstmonth,"firstfulldatamonth":firstfulldatamonth,"firstrecentdatamonth":firstrecentdatamonth,"monthrolling":monthrolling,"PED_Irradiance_Analysis_Summary":PED_Irradiance_Analysis_Summary,"IrradianceTable":IrradianceTable,"cumPED_versus_cumaltusbaseline":cumPED_versus_cumaltusbaseline,"Production_Analysis":Production_Analysis,"Cumulative_Production_Analysis":Cumulative_Production_Analysis,"CurrentPosition":CurrentPosition,"ProdPosition_RelativeTo_InvProdBaseline":ProdPosition_RelativeTo_InvProdBaseline,"CumNormProbReachinghundredPPM":CumNormProbReachinghundredPPM,"SystemAvailability":SystemAvailability,"Actual_vs_Predictive_EstProd":Actual_vs_Predictive_EstProd}

if __name__ == "__main__":
	print(processReportData(sys.argv[1]))

