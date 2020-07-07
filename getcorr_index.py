import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import csv
import glob
import sys

polygon=sys.argv[1]
year=int(sys.argv[2])
def main():
    lats=[]
    lngs=[]
    sites=[]
    otherinfo=[]
    avgyear=[]
    n=0
    for name in glob.glob('wind_nrel\\'+polygon+'\\*'+str(year)+'.csv'):
        hourlydata=[]
        with open(name,'r') as readfile:
            reader=csv.reader(readfile, lineterminator='\n')
            next(reader)
            lng=float(next(reader)[1])
            lngs.append(lng)
            lat=float(next(reader)[1])
            lats.append(lat)
            sites.append([lng,lat])
            next(reader)
            hourlydata=[]
            n+=1
            if n%500==0:
                print(str(n))
            if n==1:
                for row in reader:
                    otherinfo.append([row[0],row[1],row[2],row[3]])
                    if float(row[5])<3.5 or float(row[5])>25:
                        hourlydata.append(0)
                    elif float(row[5])>=14:
                        hourlydata.append(14**3)
                    else:
                        hourlydata.append(float(row[5])**3)
            else:
                for row in reader:
                    if float(row[5])<3.5 or float(row[5])>25:
                        hourlydata.append(0)
                    elif float(row[5])>=14:
                        hourlydata.append(14**3)
                    else:
                        hourlydata.append(float(row[5])**3)
    
    
        dailydata=[]
        cumhour=0
        for (a,b) in zip(otherinfo,hourlydata):
            if int(a[-1])<23:
                cumhour+=b
            else:
                cumhour+=b
                dailydata.append((cumhour/24)**(1/3))
                cumhour=0

        avgyear.append(np.mean(dailydata))



    grid_x,grid_y=np.mgrid[np.min(lngs):np.max(lngs):200j,np.min(lats):np.max(lats):200j]

    sites=np.array(sites)
    vals=np.array(avgyear)

    grid_z=griddata(sites,vals,(grid_x,grid_y),method='linear')

    plt.imshow(grid_z.T,extent=(min(lngs),max(lngs),min(lats),max(lats)),origin='lower')
    #plt.plot(sites[:,0],sites[:,1],'b.',markersize=1)
    plt.subplots_adjust(bottom=0.1, right=0.8, top=0.9)
    cax = plt.axes([0.85,0.1,0.075,0.8])
    plt.colorbar(cax=cax)
    plt.show()


main()
quit()
