import time
import os
import sys
import boto3
from datetime import datetime

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_latest_execution_arn(sm_client, pipeline_name):
    try:
        executions = sm_client.list_pipeline_executions(
            PipelineName=pipeline_name,
            SortBy="CreationTime",
            SortOrder="Descending",
            MaxResults=1
        ).get("PipelineExecutionSummaries", [])
        if executions:
            return executions[0]["PipelineExecutionArn"], executions[0]["PipelineExecutionStatus"]
    except Exception as e:
        print(f"Error fetching pipeline executions: {e}")
    return None, None

def get_job_logs(logs_client, log_group, job_name, num_lines=15):
    try:
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            logStreamNamePrefix=job_name,
            limit=1
        ).get('logStreams', [])
        if not streams:
            return ["(Logs not available yet or job starting...)"]
        
        stream_name = streams[0]['logStreamName']
        events = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            limit=num_lines,
            startFromHead=False
        ).get('events', [])
        
        return [e['message'].rstrip() for e in events]
    except Exception:
        return ["(Waiting for logs to stream...)"]

def main():
    pipeline_name = "Industrial-Production-Pipeline"
    sm = boto3.client('sagemaker')
    logs = boto3.client('logs')
    
    print("Finding latest pipeline execution...")
    exec_arn, last_status = get_latest_execution_arn(sm, pipeline_name)
    if not exec_arn:
        print(f"No executions found for pipeline: {pipeline_name}")
        return
    
    exec_id = exec_arn.split('/')[-1]
    
    try:
        while True:
            clear_screen()
            
            # Fetch latest steps
            steps = sm.list_pipeline_execution_steps(
                PipelineExecutionArn=exec_arn
            ).get("PipelineExecutionSteps", [])
            
            # Sort chronologically by start time
            steps = sorted(steps, key=lambda x: x.get("StartTime", datetime.min))
            
            # Refresh execution status
            desc = sm.describe_pipeline_execution(PipelineExecutionArn=exec_arn)
            status = desc.get("PipelineExecutionStatus", "Executing")
            
            print("==================================================================")
            print(f"  SageMaker Pipeline Live Monitor: {pipeline_name}")
            print(f"  Execution ID: {exec_id}  |  Overall Status: {status}")
            print("==================================================================")
            print(f"{'Step Name':<30} | {'Status':<12} | {'Duration (s)':<12}")
            print("-" * 66)
            
            active_job_name = None
            active_job_type = "Processing"
            
            for step in steps:
                name = step["StepName"]
                step_status = step["StepStatus"]
                start = step.get("StartTime")
                end = step.get("EndTime")
                
                # Calculate duration
                if start and end:
                    dur = int((end - start).total_seconds())
                    dur_str = f"{dur}s"
                elif start:
                    dur = int((datetime.now(start.tzinfo) - start).total_seconds())
                    dur_str = f"{dur}s (running)"
                else:
                    dur_str = "-"
                
                print(f"{name:<30} | {step_status:<12} | {dur_str:<12}")
                
                if step_status == "Executing":
                    metadata = step.get("Metadata", {})
                    if "ProcessingJob" in metadata:
                        active_job_name = metadata["ProcessingJob"]["Arn"].split('/')[-1]
                        active_job_type = "Processing"
                    elif "TrainingJob" in metadata:
                        active_job_name = metadata["TrainingJob"]["Arn"].split('/')[-1]
                        active_job_type = "Training"
            
            print("==================================================================")
            
            if active_job_name:
                print(f"  Live logs from active {active_job_type} Job: {active_job_name}")
                print("------------------------------------------------------------------")
                log_group = "/aws/sagemaker/ProcessingJobs" if active_job_type == "Processing" else "/aws/sagemaker/TrainingJobs"
                log_lines = get_job_logs(logs, log_group, active_job_name, num_lines=15)
                for line in log_lines:
                    print(f"  > {line}")
            else:
                if status in ["Succeeded", "Failed", "Stopped"]:
                    print(f"\nPipeline finished with status: {status}")
                    break
                else:
                    print("  Waiting for next step to start...")
            
            print("==================================================================")
            print("  Press Ctrl+C to stop watching this terminal monitor.")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

if __name__ == "__main__":
    main()
