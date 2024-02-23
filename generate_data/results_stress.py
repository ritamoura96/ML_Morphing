from abaqus import *
from odbAccess import *
from abaqusConstants import *
from viewerModules import *
#session.Viewport(name='Viewport: 1', origin=(0.0, 0.0), width=1083.57141113281, 
#    height=376.505554199219)
#session.viewports['Viewport: 1'].makeCurrent()
#session.viewports['Viewport: 1'].maximize()
#from driverUtils import executeOnCaeStartup
import odbAccess
import subprocess
import sys
import os
import numpy as np
import math
import argparse
from operator import attrgetter
import csv

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("logfile.log", "a")
   
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass    

def open_odb(odbPath):
    odb = odbAccess.openOdb(path=odbPath, readOnly=False)
    return odb

if __name__ == '__main__':

    sys.stdout = Logger()
    
    folder_path = os.getcwd()
    odb_name = '/main.odb'
    path = folder_path + odb_name 
    #print(path)

    odb = open_odb(path)

    referenceNode = odb.rootAssembly.nodeSets['REFERENCE_POINT_PART-1-1   305290']
    nodesPelvicFloor = odb.rootAssembly.instances['PART-1-1'].nodeSets['PELVIC_FLOOR_NODES']
    elementsPelvicFloor = odb.rootAssembly.instances['PART-1-1'].elementSets['PELVIC_FLOOR']
    
    nodesSet = nodesPelvicFloor
    pos = NODAL 

    lastFrame = odb.steps['Step-8'].frames[-1]

    displacement=lastFrame.fieldOutputs['U'].getSubset(region=nodesSet, position=pos)
    dispValues=displacement.values

    coordinates=lastFrame.fieldOutputs['COORD'].getSubset(region=nodesSet, position=pos)
    coordValues=coordinates.values

    forces_PFM=lastFrame.fieldOutputs['RF'].getSubset(region=nodesSet, position=pos)
    forceValues=forces_PFM.values

    forces_head=lastFrame.fieldOutputs['RF'].getSubset(region=referenceNode, position=pos)
    forceValuesHead=forces_head.values
 
    stress = lastFrame.fieldOutputs['S'].getSubset(region=elementsPelvicFloor, position=ELEMENT_NODAL)
    stressValues=stress.values

    #GET MAX PRINCIPAL STRESS FROM SESSION
    o1 = session.openOdb(name=path, readOnly=False)
    session.viewports['Viewport: 1'].setValues(displayedObject=o1)
    odbName=session.viewports[session.currentViewportName].odbDisplay.name
    
    session.odbData[odbName].setValues(activeFrames=(('Step-2', (-1, )), ))
    xy_1 = session.xyDataListFromField(odb=odb, outputPosition=NODAL, variable=(('S', 
    INTEGRATION_POINT, ((INVARIANT, 'Max. Principal'), )), ), nodeSets=(
    "PART-1-1.PELVIC_FLOOR_NODES", ))
    SMaxPrincipalValues_1 = [xy_1[i][0][1] for i, j in enumerate(xy_1)]
 
    session.odbData[odbName].setValues(activeFrames=(('Step-4', (-1, )), ))
    xy_2 = session.xyDataListFromField(odb=odb, outputPosition=pos, variable=(('S', 
    INTEGRATION_POINT, ((INVARIANT, 'Max. Principal'), )), ), nodeSets=(
    "PART-1-1.PELVIC_FLOOR_NODES", ))
    SMaxPrincipalValues_2 = [xy_2[i][0][1] for i, j in enumerate(xy_2)]

    session.odbData[odbName].setValues(activeFrames=(('Step-7', (-1, )), ))
    xy_3 = session.xyDataListFromField(odb=odb, outputPosition=pos, variable=(('S', 
    INTEGRATION_POINT, ((INVARIANT, 'Max. Principal'), )), ), nodeSets=(
    "PART-1-1.PELVIC_FLOOR_NODES", ))
    SMaxPrincipalValues_3 = [xy_3[i][0][1] for i, j in enumerate(xy_3)]

    session.odbData[odbName].setValues(activeFrames=(('Step-8', (-1, )), ))
    xy_4 = session.xyDataListFromField(odb=odb, outputPosition=pos, variable=(('S', 
    INTEGRATION_POINT, ((INVARIANT, 'Max. Principal'), )), ), nodeSets=(
    "PART-1-1.PELVIC_FLOOR_NODES", ))
    SMaxPrincipalValues_4 = [xy_4[i][0][1] for i, j in enumerate(xy_4)]

    #SAVE DATA TO CSV FILES 
    for k in forceValuesHead:
        output = open('results_head.csv','a')
        output.write(str(k.nodeLabel)+','+str(k.data[0])+','+str(k.data[1])+','+str(k.data[2])+'\n')
        output.close()

    for w in stressValues:
        output = open('results_element_stresses.csv','a')
        output.write(str(w.elementLabel)+','+str(w.data[0])+','+str(w.data[1])+','+str(w.data[2])
        +','+str(w.data[3])+','+str(w.data[4])+','+str(w.data[5])+'\n')
        output.close()    

    for v,x,z,i,j,k,l in zip(dispValues,coordValues,forceValues,SMaxPrincipalValues_1,SMaxPrincipalValues_2,SMaxPrincipalValues_3,SMaxPrincipalValues_4):
        output = open('results.csv','a')
        output.write(str(v.nodeLabel)
        +','+str(v.data[0])+','+str(v.data[1])+','+str(v.data[2])
        +','+str(x.data[0])+','+str(x.data[1])+','+str(x.data[2])
        +','+str(z.data[0])+','+str(z.data[1])+','+str(z.data[2])
        +','+str(i)+','+str(j)+','+str(k)+','+str(l)+'\n')
        output.close()
