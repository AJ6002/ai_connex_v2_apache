import sys
import time
import argparse
from datetime import datetime
import boto3

def get_failure_reason(client, step):
    metadata = step.get('Metadata', {})
    if 'ProcessingJob' in metadata:
        job_arn = metadata['ProcessingJob']['Arn']
        job_name = job_arn.split('/')[-1]
        try:
            desc = client.describe_processing_job(ProcessingJobName=job_name)
            return desc.get('FailureReason', 'Unknown failure reason in processing job')
        except Exception as e:
            return f"Error describing processing job {job_name}: {str(e)}"
    elif 'TrainingJob' in metadata:
        job_arn = metadata['TrainingJob']['Arn']
        job_name = job_arn.split('/')[-1]
        try:
            desc = client.describe_training_job(TrainingJobName=job_name)
            return desc.get('FailureReason', 'Unknown failure reason in training job')
        except Exception as e:
            return f"Error describing training job {job_name}: {str(e)}"
    elif 'TransformJob' in metadata:
        job_arn = metadata['TransformJob']['Arn']
        job_name = job_arn.split('/')[-1]
        try:
            desc = client.describe_transform_job(TransformJobName=job_name)
            return desc.get('FailureReason', 'Unknown failure reason in transform job')
        except Exception as e:
            return f"Error describing transform job {job_name}: {str(e)}"
    elif 'Fail' in metadata:
        return metadata['Fail'].get('ErrorMessage', 'Fail step executed')
    return "No job details available for failure reason"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execution-arn', type=str, required=True, help='SageMaker Pipeline Execution ARN')
    parser.add_argument('--log-file', type=str, default='pipeline_monitoring.log', help='Path to log file')
    args = parser.parse_args()

    client = boto3.client('sagemaker', region_name='ap-south-1')
    
    print(f"[{datetime.now().isoformat()}] Starting monitoring for execution ARN: {args.execution_arn}")
    print(f"[{datetime.now().isoformat()}] Logs will be written to {args.log_file}")
    sys.stdout.flush()

    known_steps = {}

    while True:
        try:
            # Describe pipeline execution to get overall status
            exec_desc = client.describe_pipeline_execution(PipelineExecutionArn=args.execution_arn)
            pipeline_status = exec_desc.get('PipelineExecutionStatus', 'Unknown')
            
            # List pipeline execution steps
            steps_resp = client.list_pipeline_execution_steps(PipelineExecutionArn=args.execution_arn)
            steps = steps_resp.get('PipelineExecutionSteps', [])
            
            log_entries = []
            log_entries.append(f"--- Poll Time: {datetime.now().isoformat()} ---")
            log_entries.append(f"Pipeline Status: {pipeline_status}")
            
            transitions = []
            
            for step in steps:
                name = step['StepName']
                status = step['StepStatus']
                start_time = step.get('StartTime')
                end_time = step.get('EndTime')
                
                start_str = start_time.isoformat() if start_time else 'N/A'
                end_str = end_time.isoformat() if end_time else 'N/A'
                
                log_entries.append(f"Step: {name} | Status: {status} | Start: {start_str} | End: {end_str}")
                
                # Check for status transitions
                if name not in known_steps:
                    # New step discovered
                    known_steps[name] = status
                    transitions.append(f"NEW_STEP: {name} is {status} (Start: {start_str})")
                    if status == 'Failed':
                        reason = get_failure_reason(client, step)
                        transitions.append(f"FAILURE_REASON: Step {name} failed: {reason}")
                elif known_steps[name] != status:
                    # Status transition
                    old_status = known_steps[name]
                    known_steps[name] = status
                    transitions.append(f"TRANSITION: {name} transitioned from {old_status} to {status} (End: {end_str})")
                    if status == 'Failed':
                        reason = get_failure_reason(client, step)
                        transitions.append(f"FAILURE_REASON: Step {name} failed: {reason}")
            
            # Write to log file
            with open(args.log_file, 'a') as f:
                f.write('\n'.join(log_entries) + '\n\n')
                
            # Print transitions to stdout (will trigger parent agent notification)
            for t in transitions:
                print(f"[{datetime.now().isoformat()}] {t}")
            
            # Print heartbeats to stdout
            print(f"[{datetime.now().isoformat()}] Heartbeat: Status={pipeline_status}, ActiveSteps={[s['StepName'] for s in steps if s['StepStatus'] == 'Executing']}")
            sys.stdout.flush()
            
            # Check if overall pipeline execution is completed
            if pipeline_status in ['Succeeded', 'Failed', 'Stopped']:
                print(f"[{datetime.now().isoformat()}] TERMINAL_STATE: Pipeline execution reached terminal state: {pipeline_status}")
                sys.stdout.flush()
                break
                
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] ERROR: {str(e)}")
            sys.stdout.flush()
            
        time.sleep(45)

if __name__ == '__main__':
    main()
