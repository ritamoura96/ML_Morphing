import os
import csv
import glob
import time
import queue
import shutil
import datetime 
import subprocess
import numpy as np
from joblib import Parallel, delayed

def exec_sim(k, value, AP):

	simulation_list = ['sim_02', 'sim_03', 'sim_04', 'sim_05', 'sim_06', 'sim_07', 'sim_08', 'sim_09', 'sim_10', 'sim_11']
	range_AP = np.arange(46.0, 74.2+(28.2/11), 28.2/10)
	
	for i in range(len(range_AP)):
		if AP == round(range_AP[i], 2):
			sim_number = simulation_list[i]

	sim_baseline = start_dir + '/' + sim_number + '/' 
	#create new directory - simulation folder 
	directory = 'sim_'+str(k)

	new_directory = sim_number + '_simulations'
	new_folder = os.path.join(os.getcwd(), new_directory)
	os.makedirs(new_folder, exist_ok = True)

	path1 = os.path.join(new_folder, directory)
	shutil.copytree(sim_baseline,path1)
	
	# RUN MORPHING

	cmd='python3.9 main_morphing.py -AP ' + str(value['diam_AP']) + ' -T ' + str(value['diam_T']) 
	print(cmd)
	job = subprocess.Popen(cmd, cwd=path1,
	stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	job.wait()

	# CHANGE MATERIAL PROPERTIES

	properties = path1+'/material_properties.inp'
	my_file = open(properties,'r')
	line = my_file.readlines()
	line[c] = 'C10='+str(value['c'])+'\n'
	line[b] = 'C01='+str(value['b'])+'\n'
	my_file = open(properties,'w')
	my_file.writelines(line)
	my_file.close()

	#run simulation
	cmd1='abaqus job=main.inp user=hgo_martins.for cpus=8 -interactive' 
	print(cmd1)
	job = subprocess.Popen(cmd1, cwd=path1,
	stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	job.wait()

	#if the simulation has not finished - write the simulation number to a text file
	with open(path1+'/main.sta', 'r') as file:
		last_line = file.readlines()[-1]

	if last_line != ' THE ANALYSIS HAS COMPLETED SUCCESSFULLY'+'\n':
		write_file = open(new_folder+'/file.txt','a')
		write_file.write('sim_'+str(k)+', '+datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')+'\n')
		write_file.close()
	else:
		cmd2='abaqus viewer nogui=results.py'
		print(cmd2)
		job = subprocess.Popen(cmd2, cwd=path1,
		stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		job.wait()

	# copy the original inp file and delete all files that start with "main" (to save memory)
	shutil.copyfile(path1+'/main.inp',path1+'/input_file.inp')
	shutil.copyfile(path1+'/main.sta',path1+'/input_file.sta')
	for filename in glob.glob(path1+'/main*'):
		os.remove(filename) 

	write_file = open(path1+'/diameters.txt','a')
	write_file.write(str(value['diam_AP']) + ' -T ' + str(value['diam_T']))
	write_file.close()

	return

######################################################################
start_dir = os.getcwd()

number_simulations = 6897 # total number of simulations to run
c = 15
b = 16

# DEFINE PARAMETER RANGE

range_AP = np.arange(46.0+(28.2/10), 74.2+(28.2/11), 28.2/10)
range_T = np.arange(24.8, 54.8+(30/10), 30/10)
range_c = np.arange(0.02, 0.045+(0.025/10), 0.025/10)
range_b = np.arange(1.0, 1.35, 0.35/10)

value_parallel_list = []

for AP_value in range_AP:
    for T_value in range_T:
        for c_value in range_c:
            for b_value in range_b:
                if (T_value/AP_value < 0.85) and (T_value/AP_value > 0.55):
                    value_parallel_line = [{'diam_AP': round(AP_value,2), 'diam_T': T_value, 'c': round(c_value,4), 'b': round(b_value,4)}]
                    value_parallel_list.append(value_parallel_line)

######################################################################

n = 10 #number of simulations running at the same time (parallel)
index_every_n = np.arange(0, number_simulations, n)

for index in index_every_n:
	
	index_parallel = np.arange(index, index + n, 1) #define the number of the simulations that are going to run - creates an array from the first simulation number until the last	
	value_parallel = [value_parallel_list[x][0] for x in index_parallel]
	AP_value_list = [value_parallel_list[x][0]['diam_AP'] for x in index_parallel]

	#execute function n number of times - simulations in parallel
	out = Parallel(n_jobs=n, backend='multiprocessing', max_nbytes=None)(delayed(exec_sim)(k, f, AP) for k,f,AP in zip(index_parallel, value_parallel, AP_value_list))
