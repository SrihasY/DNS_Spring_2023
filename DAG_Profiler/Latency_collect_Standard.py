# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Purpose

Shows how to use the AWS SDK for Python (Boto3) with AWS Step Functions to
create and run state machines.
"""
from StepFunction_util import *
import json
import logging
from botocore.exceptions import ClientError
import boto3
import sys
import time
import random
import string
from datetime import datetime
import os

def recursive_items(dictionary):
    for key, value in dictionary.items():
        if type(value) is dict:
            yield from recursive_items(value)
        else:
            yield (key, value)



def event_log_extract(events):
	print(events)
	function_durations_by_name = {}
	#print(events)
	events_id_dict = {}
	#print("num of events:" + str(len(events)))
	for event in events:
		#event = json.loads(event_str)
		#print(event)
		events_id_dict[event["id"]] = event
		if(event["type"] == "TaskSucceeded" or event["type"] == "MapStateSucceeded"):
			#print(event)
			#print("**********************")
			time_stamp_end = event["timestamp"]
			task_type = event["type"]
			prev_event = event
			while(task_type != "TaskStateEntered" and task_type != "MapStateEntered"): #TaskStateEntered stateEnteredEventDetails["name"]
				prev_event = events_id_dict[prev_event["previousEventId"]]
				task_type = prev_event["type"]
			time_stamp_start = prev_event["timestamp"]
			function_name = prev_event["stateEnteredEventDetails"]["name"]
			elapsed_time = int((time_stamp_end - time_stamp_start).total_seconds() * 1000)
			#print(function_name + "\t" + str(elapsed_time))
			if(function_name not in function_durations_by_name):
				function_durations_by_name[function_name] = []
			function_durations_by_name[function_name].append(elapsed_time)
	e2e_start_time = events[0]["timestamp"]
	e2e_end_time = events[-1]["timestamp"]
	function_durations_by_name["E2E"] = [int((e2e_end_time-e2e_start_time).total_seconds() * 1000)]
	return function_durations_by_name

	

def main():
	
	args = sys.argv[1:]
	logger = logging.getLogger(__name__)

	lambda_client = boto3.client('lambda')
	stepFunctions_client = boto3.client('stepfunctions')
	if(len(args) == 0):
		print("Please enter the DAG's arn as the first argument")
		return

	if(len(args) == 1):
		print("Please enter the number of profiling runs as the second argument")
		return

	if(len(args) == 2):
		print("Please enter the inputs.json file name as the third argument")
		return

	#Example usage:  StepFunctionsStateMachine(stepFunctions_client, "arn:aws:XXXXXXXXXXXX")
	DAG_arn = args[0]
	Num_of_runs = int(args[1])
	inputs_file_name = args[2]
	step_controler = StepFunctionsStateMachine(stepFunctions_client, DAG_arn)

	memResnet = [2048]
	memlang = [5632]
	memTranslate = [4096]
	
	print("collecting data for memory sizes of:")
	print(memResnet, memlang, memTranslate)
	
	print("lambda function names/arns in the DAG")


	# Extract all function arns from the DAG
	# describe_out = step_controler.describe()
	# #print(describe_out['definition'])
	# j_def = json.loads(describe_out['definition'])
	# describe_out_unrolled = recursive_items(j_def)
	function_arns = ["arn:aws:lambda:us-west-2:246098724710:function:langdetect", 
                  "arn:aws:lambda:us-west-2:246098724710:function:es2en",
                  "arn:aws:lambda:us-west-2:246098724710:function:de2en",
                  "arn:aws:lambda:us-west-2:246098724710:function:resnet"]
	# for key, value in describe_out_unrolled:
	# 	if(key == "Resource"):
	# 		#print(key, value)
	# 		function_arns.append(value)
	print("Identified the following functions in the DAG")
	print(function_arns)

	letters = string.ascii_lowercase
	profile_hash = ''.join(random.choice(letters) for i in range(10))
	app_name = inputs_file_name.split('_')[0]
	profile_hash = profile_hash + "_" + app_name
	os.makedirs("profile_"+ profile_hash)
	print("Created folder profile_"+ profile_hash + " with profiled runtimes and memory sizes")

	for mindex in range(len(memlang)):
		runtimes_by_name = {} # dictionary to save the runtimes of each function by name. Function_name -> List of runtimes
		# change the memory sizes for all functions in the DAG
		response = lambda_client.update_function_configuration(FunctionName=function_arns[0], MemorySize=int(memlang[mindex]))
		for func in function_arns[1:3]:
			response = lambda_client.update_function_configuration(FunctionName=func, MemorySize=int(memTranslate[mindex]))
		response = lambda_client.update_function_configuration(FunctionName=function_arns[3], MemorySize=int(memResnet[mindex]))
		time.sleep(5)
		
		# load profiling runs' inputs from file
		input_dict_list = []
		f = open(inputs_file_name, "r")
		lines = f.readlines()
		for l in lines:
			input_dict_list.append(json.loads(l))

		
		# execute the DAG for Num_of_runs times
		input_id = 0
		for run_id in range(Num_of_runs):

			letters = string.ascii_lowercase
			run_hash = ''.join(random.choice(letters) for i in range(10))
			run_name = "run_" + run_hash
			run_arn = step_controler.start_run(run_name, input_dict_list[input_id])
			input_id += 1
			
			# if number of inputs < number of runs, we re-iterate over the inputs
			if(input_id > len(input_dict_list)):
				input_id = 0

			run_succeeded = False
			for i in range(200): # Busy loop until success or until 1000 seconds have elapsed
				arn_describtion = step_controler.describe_execution(run_arn)
				print(arn_describtion)
				print("+++++++++++++++++++++++++++++++++++++++++++")
				if(arn_describtion['status'] == 'SUCCEEDED'):
					run_succeeded = True
					break
				time.sleep(5)

			if(run_succeeded == True):
				response = step_controler.get_run_logs(run_arn)
				runtimes = event_log_extract(response["events"])
				for key in runtimes:
					if(key not in runtimes_by_name):
						runtimes_by_name[key] = []
					runtimes_by_name[key].append(runtimes[key])
		print("+++++++++++++++++++++++++++++++++++++++++++")				
		print("+++++++++++++++++++++++++++++++++++++++++++")
		print("For memory size of " + str(memResnet[mindex]) + ", memlang: " + str(memlang[mindex]) + ", memtranslate: " + str(memTranslate[mindex]))
		print(runtimes_by_name)
		out_file_name = "profile_"+ profile_hash + "//" + "rsc_" + str(memResnet[mindex]) + "_" + str(memlang[mindex]) + "_" + str(memTranslate[mindex]) + ".txt"
		num_of_runs = len(runtimes_by_name["E2E"])
		
		if("ObjectDetectUpload_" in runtimes_by_name):
			f = open(out_file_name, 'w')
			for run_id in range(num_of_runs):
				line = "Video:" + str(run_id) + " Chunk:" + str(run_id) +  " E2E:" + str(max(runtimes_by_name["E2E"][run_id])) +  " Split:" + str(max(runtimes_by_name["Split"][run_id])) +  " Extract:" + str(max(runtimes_by_name["Extract"][run_id])) +  " Classify:" + str(max(runtimes_by_name["ObjectDetectUpload"][run_id]))
				f.write(line + "\n")
			f.close()
			
		else:
			f = open(out_file_name, 'w')
			f.write(json.dumps(runtimes_by_name))
			# for run_id in range(num_of_runs):
			# 	line = "E2E:" + str(max(runtimes_by_name["E2E"][run_id]))
			# 	for key in runtimes_by_name:
			# 		line = line + " " + key + ":" + str(max(runtimes_by_name[key][run_id]))
			# 	f.write(line + "\n")
			f.close()

main()
