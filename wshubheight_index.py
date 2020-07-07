import pandas as pd
import numpy as np
import glob
import csv
import sys

polygon=sys.argv[1]
year=int(sys.argv[2])
monthlydata_new={}
for m in range(12):
    monthlydata_new[m]=[]
dailydata_new={}
for d in range(365):
    dailydata_new[d]=[]

otherinfo=[]
dateinfo=[]
n=0
for name in glob.glob('wind_nrel\\'+polygon+'\\*'+str(year)+'.csv'):
    n+=1
    if n%500==0:
        print(str(n))
    with open(name,'r') as readfile:
        reader=csv.reader(readfile,lineterminator='\n')
        try:
            next(reader)
            next(reader)
            next(reader)
            next(reader)
        except StopIteration:
            print(name)
        
        hourlydata=[]
        if n==1:
            for row in reader:
                otherinfo.append(row[:4])
                if float(row[5])<3.5 or float(row[5])>25:
                    hourlydata.append(0)
                elif float(row[5])>=14:
                    hourlydata.append(14**3)
                else:
                    hourlydata.append(float(row[-1])**3)
        else:
            for row in reader:
                if float(row[5])<3.5 or float(row[5])>25:
                    hourlydata.append(0)
                elif float(row[5])>=14:
                    hourlydata.append(14**3)
                else:
                    hourlydata.append(float(row[-1])**3)

    dailydata=[]
    cumhour=0
    for (a,b) in zip(otherinfo,hourlydata):
        if int(a[-1])<23:
            cumhour+=b
        else:
            cumhour+=b
            if sys.argv[3]=='index':
                dailydata.append((cumhour/24)**(1/3))
            elif sys.argv[3]=='energy':
                dailydata.append(cumhour/24)
            else:
                print('Need the index or energy command')
            if n==1:
                dateinfo.append(a[:-1])
            cumhour=0


    for d in range(365):
        dailydata_new[d].append(dailydata[d])


    monthlydata=pd.DataFrame(np.zeros(12),index=[1,2,3,4,5,6,7,8,9,10,11,12],columns=[year])
    for (a,b) in zip(dateinfo,dailydata):
        monthlydata.loc[int(a[1]),int(a[0])]+=b

    for m in range(12):
        monthlydata_new[m].append(monthlydata.loc[m+1,year])

dailyindex=[]
for d in range(365):
    dailyindex.append(np.mean(dailydata_new[d]))

monthlyindex=pd.DataFrame(np.zeros(12),index=[1,2,3,4,5,6,7,8,9,10,11,12],columns=[year])
for (a,b) in zip(dateinfo,dailyindex):
    monthlyindex.loc[int(a[1]),int(a[0])]+=b

with open('dbfiles/'+polygon+'_maxminavgindex_'+str(year)+'.csv','w') as writefile:
    writer=csv.writer(writefile,lineterminator='\n')
    writer.writerow(['year','month','max','min','avg'])
    for m in range(12):
        writer.writerow([year,m+1]+[max(monthlydata_new[m]),min(monthlydata_new[m]),monthlyindex.loc[m+1,year]])