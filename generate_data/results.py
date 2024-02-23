from abaqus import *
from odbAccess import *
from abaqusConstants import *
from viewerModules import *
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

    # GET RESULTS FROM THE LAST FRAME OF EACH STEP

    number_steps = 9
    lastFrame = [0]*number_steps
    for i in range(number_steps):
        lastFrame[i] = odb.steps['Step-' + str(i+1)].frames[-1]

    displacement = [0]*number_steps
    dispValues = [0]*number_steps

    coordinates = [0]*number_steps
    coordValues = [0]*number_steps

    forces_head = [0]*number_steps
    forceValuesHead = [0]*number_steps
    
    stress = [0]*number_steps
    stressValues = [0]*number_steps
    
    for i in range(number_steps):
        
        displacement[i]=lastFrame[i].fieldOutputs['U'].getSubset(region=nodesSet, position=pos)
        dispValues[i]=displacement[i].values

        coordinates[i]=lastFrame[i].fieldOutputs['COORD'].getSubset(region=nodesSet, position=pos)
        coordValues[i]=coordinates[i].values

        forces_head[i]=lastFrame[i].fieldOutputs['RF'].getSubset(region=referenceNode, position=pos)
        forceValuesHead[i]=forces_head[i].values

        stress[i] = lastFrame[i].fieldOutputs['S'].getSubset(region=elementsPelvicFloor, position=ELEMENT_NODAL)
        stressValues[i]=stress[i].values

    output_coord = open('results_coordinates.csv','a')
    for i in range(len(coordValues)):
        for k in coordValues[i]:
            output_coord.write(str(k.nodeLabel)+','+str(k.data[0])+','+str(k.data[1])+','+str(k.data[2])+'\n')
    output_coord.close()   

    output_disp = open('results_displacement.csv','a')
    for i in range(len(dispValues)):
        for k in dispValues[i]:
            output_disp.write(str(k.nodeLabel)+','+str(k.data[0])+','+str(k.data[1])+','+str(k.data[2])+'\n')
    output_disp.close()   

    output_stress = open('results_stresses.csv','a')
    for i in range(len(stressValues)):
        for w in stressValues[i]:
            output_stress.write(str(w.elementLabel)+','+str(w.data[0])+','+str(w.data[1])+','+str(w.data[2])+','+str(w.data[3])+','+str(w.data[4])+','+str(w.data[5])+'\n')
    output_stress.close()   
    
    output = open('results_head_forces.csv','a')
    for i in range(len(forceValuesHead)):
        for k in forceValuesHead[i]:
            output.write(str(k.data[0])+','+str(k.data[1])+','+str(k.data[2])+'\n')
    output.close()     

    # GET RESULTS FOR ALL FRAMES BETWEEN 50 TO 80 MM 

    allFrames = []
    steps_stretch = [8, 9]
    count = 0

    for i in steps_stretch:
        step_name = 'Step-' + str(i)
        step = odb.steps[step_name]
        frames = step.frames

        for frame in frames:
            #if count % 5 == 0:
            allFrames.append(frame)  # Append each frame to the list
            #count += 1

    displacementAllFrames = [0]*len(allFrames)
    dispValuesAllFrames = [0]*len(allFrames)

    coordinatesAllFrames = [0]*len(allFrames)
    coordValuesAllFrames = [0]*len(allFrames)

    for i in range(len(allFrames)):
        
        displacementAllFrames[i]=allFrames[i].fieldOutputs['U'].getSubset(region=nodesSet, position=pos)
        dispValuesAllFrames[i]=displacementAllFrames[i].values

        coordinatesAllFrames[i]=allFrames[i].fieldOutputs['COORD'].getSubset(region=nodesSet, position=pos)
        coordValuesAllFrames[i]=coordinatesAllFrames[i].values

    output_coord = open('results_coordinates_AllFrames.csv','a')
    for i in range(len(coordValuesAllFrames)):
        for k in coordValuesAllFrames[i]:
            output_coord.write(str(k.nodeLabel)+','+str(k.data[0])+','+str(k.data[1])+','+str(k.data[2])+'\n')
    output_coord.close()   

    output_disp = open('results_displacement_AllFrames.csv','a')
    for i in range(len(dispValuesAllFrames)):
        for k in dispValuesAllFrames[i]:
            output_disp.write(str(k.nodeLabel)+','+str(k.data[0])+','+str(k.data[1])+','+str(k.data[2])+'\n')
    output_disp.close()   

    ################## GET MAX PRINCIPAL STRESS FROM SESSION ##################
    
    o1 = session.openOdb(name=path, readOnly=False)
    session.viewports['Viewport: 1'].setValues(displayedObject=o1)
    odbName=session.viewports[session.currentViewportName].odbDisplay.name

    # LAST FRAME OF EACH STEP

    odb_frames = ['Step-1', 'Step-2', 'Step-3', 'Step-4', 'Step-5', 'Step-6', 'Step-7', 'Step-8', 'Step-9']
    SMaxPrincipalValues = []

    for frame in odb_frames:
        session.odbData[odbName].setValues(activeFrames=((frame, (-1,)),))
        xy_data = session.xyDataListFromField(odb=odb, outputPosition=pos, variable=(('S', INTEGRATION_POINT, ((INVARIANT, 'Max. Principal'),)),), nodeSets=("PART-1-1.PELVIC_FLOOR_NODES",))
        SMaxPrincipalValues.append([value[0][1] for _, value in enumerate(xy_data)])

    with open('results_max_principal_stresses.csv', 'a') as output:
        for row in zip(*SMaxPrincipalValues):
            row_values = ','.join(str(value) for value in row)
            output.write(row_values + '\n')

    # ALL FRAMES OF STEPS 8 AND 9

    odb_AllFrames = ['Step-8', 'Step-9']  
    SMaxPrincipalValuesAllFrames = []
    count_stress = 0

    for step in odb_AllFrames:
        step_instance = session.odbData[odbName].steps[step]
        num_frames = len(step_instance.frames)

        for frame in range(num_frames):
            #if count_stress % 5 == 0:
            session.odbData[odbName].setValues(activeFrames=((step, (frame,)),))
            xy_data = session.xyDataListFromField(odb=odb, outputPosition=pos, variable=(('S', INTEGRATION_POINT, ((INVARIANT, 'Max. Principal'),)),), nodeSets=("PART-1-1.PELVIC_FLOOR_NODES",))
            SMaxPrincipalValuesAllFrames.append([value[0][1] for _, value in enumerate(xy_data)])
            #count_stress += 1

    with open('results_max_principal_stresses_AllFrames.csv', 'a') as output_AllFrames:
        for row in zip(*SMaxPrincipalValuesAllFrames):
            row_values_AllFrames = ','.join(str(value) for value in row)
            output_AllFrames.write(row_values_AllFrames + '\n')