## A script for extracting info about the patients used in the analysis

## Load necessary modules

from rpy2 import robjects as ro
import numpy as np
import os
ro.r('library(survival)')
import re

##This call will only work if you are running python from the command line.
##If you are not running from the command line manually type in your paths.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

##LAML did not contain a follow_up file, which might explain why cbioportal didn't allow kaplans for this cancer for a period of time.
##However there was a lot of clinical data in the clinical_patient file

## Sex and age information were taken from the "clinical_patient" file.  A dictionary was created for sex.
clinical4=[]

more_clinical={}

sex_dict={}
sex_dict['MALE']=0
sex_dict['FEMALE']=1


f=open(os.path.join(BASE_DIR,'tcga_data','LAML','clinical','nationwidechildrens.org_clinical_patient_laml.txt'))
##get the column indexes needed
columns=f.readline().split('\t')
sex_column=columns.index('gender')
age_column=columns.index('age_at_diagnosis')
patient_column=columns.index('bcr_patient_barcode')
alive_column=columns.index('last_contact_days_to')
death_column=columns.index('death_days_to')
f.readline()
f.readline()
data=[i.split('\t') for i in f]
for i in data:
    try:
        more_clinical[i[patient_column]]=[0,sex_dict[i[sex_column]],int(i[age_column])]
        if re.search('^[0-9]+$',i[alive_column]):
            clinical4.append([i[patient_column],int(i[alive_column]),'Alive'])
        elif re.search('^[0-9]+$',i[death_column]):
            clinical4.append([i[patient_column],int(i[death_column]),'Dead'])
        else:
            pass
    except:
        pass



## only patients who had a follow up time greater than 0 days are included in the analysis
clinical=[i for i in clinical4 if i[1]>0]


final_clinical=[]

## A new list containing both follow up times and sex and age is constructed.
## Only patients with sex and age information are included.
## Data is [[Patient ID, time (days), vital status, 0, sex, age at diagnosis],...]

for i in clinical:
    if i[0] in more_clinical:
        final_clinical.append(i+more_clinical[i[0]])



##In a separate script I parsed the mitranscriptome.expr.counts.tsv file and extracted the LAML patient and expression values.
##From this file I will load the expression data.
##There are duplicated transcripts and the possibility of a patient having multiple sequencing files.

f=open(os.path.join(BASE_DIR,'tcga_data','LAML','lncrna','LAML.txt'))
##patient list is at the top of the file

patients=f.readline().strip().split()



##create a dictionary mapping patient to all of their lncrna expression data
patient_dict={}
for index, i in enumerate(patients):
    patient_dict[i[:12]]=''


##find which patients have complete clinical data, order the data, and average data if necessary
##it's possible there are expression data for patients without clinical data, and clinical data without expression data

##create a new clinical list called clinical_and_files for consistency with previous scripts
clinical_and_files=[]
for i in final_clinical:
    if i[0] in patient_dict:
        clinical_and_files.append(i)

##print average age at diagnosis
age=np.mean([i[5] for i in clinical_and_files])

##print number of males
males=len([i for i in clinical_and_files if i[4]==0])

##print number of females
females=len([i for i in clinical_and_files if i[4]==1])

##to get the median survival we need to call survfit from r


##prepare variables for R
ro.globalenv['times']=ro.IntVector([i[1] for i in clinical_and_files])

##need to create a dummy variable group
ro.globalenv['group']=ro.IntVector([0 for i in clinical_and_files])

##need a vector for deaths
death_dic={}
death_dic['Alive']=0
death_dic['Dead']=1
ro.globalenv['died']=ro.IntVector([death_dic[i[2]] for i in clinical_and_files])

res=ro.r('survfit(Surv(times,died) ~ as.factor(group))')

#the number of events(deaths) is the fourth column of the output
deaths=str(res).split('\n')[-2].strip().split()[3]


#the median survival time is the fifth column of the output
median=str(res).split('\n')[-2].strip().split()[4]


##write data to a file
f=open('patient_info.txt','w')
f.write('Average Age')
f.write('\t')
f.write('Males')
f.write('\t')
f.write('Females')
f.write('\t')
f.write('Deaths')
f.write('\t')
f.write('Median Survival')
f.write('\n')

f.write(str(age))
f.write('\t')
f.write(str(males))
f.write('\t')
f.write(str(females))
f.write('\t')
f.write(deaths)
f.write('\t')
f.write(median)
f.close()









