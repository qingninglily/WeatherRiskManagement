import csv
import glob
from tibbslib import *
import shutil
load_states()
info=get_json('data\\info.json')
info['statedata']='wind_nrel'


ourstates = ["iowaminnesota","northtexasoklahoma","texasercot","kansas"]



#siteid=[]
lngs=[]
lats=[]
n=0
for name in glob.glob('unknown\\*.csv'):
    #purename=name.split('\\')[-1]
    #siteid.append(purename.split('-')[0])
    with open(name,'r') as readfile:
        reader=csv.reader(readfile,lineterminator='\n')
        n+=1
        nrow=0
        for row in reader:
            nrow+=1
            if nrow==2:
                lng=float(row[1])
                lngs.append(lng)
            elif nrow==3:
                lat=float(row[1])
                lats.append(lat)
            else:
                continue
        if n==1:
            for ourstate in ourstates:
                if point_in_poly(Point(lng,lat), states[ourstate].poly):
                    print(ourstate)
                    statename=ourstate
        else:
            break

move=0
for name in glob.glob('unknown\\*.csv'):
    pure_name=name.split('\\')[-1]
    #print(pure_name)
    if not os.path.isfile(info["statedata"]+"\\"+statename+"\\"+pure_name):
        move+=1
        if move%500==0:
            print('moving files',str(move))
        shutil.copyfile(name,info["statedata"]+"\\"+statename+"\\"+pure_name)