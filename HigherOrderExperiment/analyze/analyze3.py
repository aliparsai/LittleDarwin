from scipy.stats.stats import pearsonr   
# from math import sqrt


corr = list()

for i in range(1,46):
    inputFileF = "fo-"+ str(2*i) + ".csv"
    inputFileS = "so-"+ str(i) + ".csv"
    


    with open(inputFileF, 'r') as iF:
        inF = iF.readlines()
    
    with open(inputFileS, 'r') as iS:
        inS = iS.readlines()
        
    fo = list()
    so = list()
    
    for i in range(0,len(inF)):
        inFs = inF[i].split(',')
        fop = (float(inFs[2])/float(inFs[3]))
        fo.append(fop*2 - fop**2)
        
        inSs = inS[i].split(',')
        so.append(float(inSs[2])/float(inSs[3]))
    
    # print (fo,so)
    
    r,p = pearsonr(fo, so)
    corr.append(str(r**2)+"\n")

with open("corr2.csv", 'w') as corrF:
    corrF.writelines(corr)
