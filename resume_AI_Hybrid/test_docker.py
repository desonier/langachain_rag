#!/usr/bin/env python3
"""
Local Docker container testing script
Tests the containerized application before deploying to Azure
"""

import subprocess
import time
import requests
import sys
import os

def run_command(cmd, capture_output=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True, timeout=60)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"

def test_docker_container():
    """Test the Docker container locally"""
    
    container_name = "resume-rag-test"
    image_name = "resume-rag-app"
    port = 5001
    
    print("🐳 Testing Resume RAG Docker Container")
    print("=" * 50)
    
    # Check if Docker is running
    print("🔍 Checking Docker availability...")
    success, _, _ = run_command("docker --version")
    if not success:
        print("❌ Docker is not available. Please install and start Docker.")
        return False
    print("✅ Docker is available")
    
    # Stop and remove existing container if it exists
    print("🧹 Cleaning up existing containers...")
    run_command(f"docker stop {container_name}", capture_output=True)
    run_command(f"docker rm {container_name}", capture_output=True)
    
    # Build Docker image
    print("🏗️ Building Docker image...")
    success, stdout, stderr = run_command(f"docker build -t {image_name} .")
    if not success:
        print(f"❌ Failed to build Docker image: {stderr}")
        return False
    print("✅ Docker image built successfully")
    
    # Set environment variables for testing
    env_vars = []
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY", 
        "AZURE_OPENAI_CHATGPT_DEPLOYMENT"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            env_vars.append(f"-e {var}={value}")
        else:
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️ Missing environment variables (container will use defaults):")
        for var in missing_vars:
            print(f"   - {var}")
    
    # Run container
    env_string = " ".join(env_vars)
    docker_cmd = f"docker run -d --name {container_name} -p {port}:80 {env_string} {image_name}"
    print(f"🚀 Starting container: {container_name}")
    print(f"📡 Port mapping: localhost:{port} -> container:80")
    
    success, container_id, stderr = run_command(docker_cmd)
    if not success:
        print(f"❌ Failed to start container: {stderr}")
        return False
    
    print(f"✅ Container started with ID: {container_id.strip()}")
    
    # Wait for container to start
    print("⏳ Waiting for application to start...")
    for i in range(30):
        time.sleep(2)
        try:
            response = requests.get(f"http://localhost:{port}", timeout=5)
            if response.status_code == 200:
                print(f"✅ Application is responding on port {port}")
                break
        except requests.exceptions.RequestException:
            if i == 29:
                print("❌ Application failed to start within 60 seconds")
                # Show container logs
                print("\n📋 Container logs:")
                run_command(f"docker logs {container_name}", capture_output=False)
                return False
            print(f"⏳ Attempt {i+1}/30 - waiting for application...")
    
    # Test application endpoints
    print("\n🧪 Testing application endpoints...")
    
    endpoints = [
        ("/", "Main dashboard"),
        ("/admin/collections", "Collections page"),
        ("/admin/query", "Query interface"),
        ("/api/collections", "Collections API")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://localhost:{port}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {description}: {response.status_code}")
            else:
                print(f"⚠️ {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: {str(e)}")
    
    # Show container information
    print("\n📊 Container Information:")
    run_command(f"docker ps --filter name={container_name} --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'", capture_output=False)
    
    print(f"\n🌐 Application URL: http://localhost:{port}")
    print("📋 Container logs: docker logs resume-rag-test")
    print("🛑 Stop container: docker stop resume-rag-test")
    print("🧹 Remove container: docker rm resume-rag-test")
    
    return True

if __name__ == "__main__":
    success = test_docker_container()
    if success:
        print("\n🎉 Container test completed successfully!")
        print("🚀 Ready for Azure deployment!")
    else:
        print("\n❌ Container test failed!")
        sys.exit(1)