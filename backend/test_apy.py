#!/usr/bin/env python3
"""
Simple script to test the NL-to-IaC API.
"""

import requests
import time
import sys
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Test the NL-to-IaC API')
    parser.add_argument('url', help='Base URL of the API (e.g., https://nl-to-iac-api-abc123-uc.a.run.app)')
    parser.add_argument('--prompt', '-p', default='Create a VPC with a public subnet and a web server',
                      help='Natural language prompt to process')
    parser.add_argument('--project', '-n', default='demo-project',
                      help='Project name')
    parser.add_argument('--provider', '-c', choices=['aws', 'gcp', 'azure'], default='gcp',
                      help='Cloud provider')
    return parser.parse_args()

def test_health(base_url):
    """Test the health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{base_url}/health")
    if response.status_code == 200:
        print("✅ Health check successful")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        print(response.text)
        return False

def process_nl_prompt(base_url, prompt, project_name, cloud_provider):
    """Process a natural language prompt"""
    print(f"Processing prompt: '{prompt}'")
    
    data = {
        "prompt": prompt,
        "project_name": project_name,
        "cloud_provider": cloud_provider
    }
    
    response = requests.post(f"{base_url}/api/process", json=data)
    
    if response.status_code != 202:
        print(f"❌ Process request failed: {response.status_code}")
        print(response.text)
        return None
    
    print("✅ Process request accepted")
    result = response.json()
    job_id = result["job_id"]
    print(f"Job ID: {job_id}")
    return job_id

def poll_job_status(base_url, job_id):
    """Poll the job status until completion or failure"""
    print(f"Polling status for job {job_id}...")
    
    max_polls = 30
    poll_interval = 5  # seconds
    
    for i in range(max_polls):
        response = requests.get(f"{base_url}/api/status/{job_id}")
        
        if response.status_code != 200:
            print(f"❌ Status check failed: {response.status_code}")
            print(response.text)
            return None
        
        result = response.json()
        status = result["status"]
        progress = result.get("progress", 0)
        
        print(f"Status: {status}, Progress: {progress}%")
        
        if status == "failed":
            print(f"❌ Job failed: {result.get('error', 'Unknown error')}")
            return None
        
        if status == "diagrams_ready":
            print("✅ Diagrams ready")
            return result
        
        if status == "completed":
            print("✅ Job completed")
            return result
        
        print(f"Waiting {poll_interval} seconds...")
        time.sleep(poll_interval)
    
    print("❌ Timeout waiting for job completion")
    return None

def get_diagrams(base_url, job_id):
    """Get the generated diagrams"""
    print(f"Getting diagrams for job {job_id}...")
    
    response = requests.get(f"{base_url}/api/diagrams/{job_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get diagrams: {response.status_code}")
        print(response.text)
        return None
    
    result = response.json()
    diagrams = result["diagrams"]
    
    print(f"Found {len(diagrams)} diagrams:")
    for diagram in diagrams:
        print(f"- {diagram['name']}: {diagram['url']}")
    
    return diagrams

def confirm_job(base_url, job_id):
    """Confirm the job to proceed with Terraform generation"""
    print(f"Confirming job {job_id}...")
    
    data = {
        "confirmed": True,
        "feedback": "Looks good!"
    }
    
    response = requests.post(f"{base_url}/api/confirm/{job_id}", json=data)
    
    if response.status_code != 200:
        print(f"❌ Failed to confirm job: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Job confirmed")
    return True

def get_generated_output(base_url, job_id):
    """Get the generated Terraform files and documentation"""
    print(f"Getting generated output for job {job_id}...")
    
    # First, poll until completion
    max_polls = 30
    poll_interval = 5  # seconds
    
    for i in range(max_polls):
        response = requests.get(f"{base_url}/api/status/{job_id}")
        
        if response.status_code != 200:
            print(f"❌ Status check failed: {response.status_code}")
            print(response.text)
            return None
        
        result = response.json()
        status = result["status"]
        
        if status == "completed":
            break
        
        if status == "failed":
            print(f"❌ Job failed: {result.get('error', 'Unknown error')}")
            return None
        
        print(f"Status: {status}, waiting {poll_interval} seconds...")
        time.sleep(poll_interval)
    
    # Now get the generated output
    response = requests.get(f"{base_url}/api/generate/{job_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get generated output: {response.status_code}")
        print(response.text)
        return None
    
    result = response.json()
    
    print("✅ Generated output retrieved")
    print(f"Terraform files ({len(result['terraform_files'])}):")
    for tf_file in result["terraform_files"]:
        print(f"- {tf_file['name']}: {tf_file['url']}")
    
    print(f"Documentation: {result['documentation_url']}")
    
    return result

def main():
    args = parse_args()
    base_url = args.url.rstrip('/')
    
    # Test health
    if not test_health(base_url):
        sys.exit(1)
    
    # Process NL prompt
    job_id = process_nl_prompt(base_url, args.prompt, args.project, args.provider)
    if not job_id:
        sys.exit(1)
    
    # Poll job status
    result = poll_job_status(base_url, job_id)
    if not result:
        sys.exit(1)
    
    # Get diagrams
    diagrams = get_diagrams(base_url, job_id)
    if not diagrams:
        sys.exit(1)
    
    # Confirm job
    if not confirm_job(base_url, job_id):
        sys.exit(1)
    
    # Get generated output
    output = get_generated_output(base_url, job_id)
    if not output:
        sys.exit(1)
    
    print("\n✅ All tests passed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())