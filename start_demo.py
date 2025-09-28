#!/usr/bin/env python3
"""
Demo startup script for MCP Agent + FastAPI chat service
Starts both the MCP agent and FastAPI backend for demo
"""
import subprocess
import sys
import time
import os
from pathlib import Path
import signal
import threading

def start_mcp_agent():
    """Start the MCP agent in the background"""
    print("🤖 Starting MCP Agent...")
    agent_dir = Path(__file__).parent / "agent"
    os.chdir(agent_dir)
    
    process = subprocess.Popen([
        sys.executable, "agents.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return process

def start_fastapi_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI Backend...")
    backend_dir = Path(__file__).parent / "backend"
    
    process = subprocess.Popen([
        sys.executable, "chat_api.py"
    ], cwd=backend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return process

def check_health():
    """Check if services are healthy"""
    import requests
    try:
        response = requests.get("http://localhost:3001/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("🎉 Starting RentalBuddy Demo Services")
    print("=" * 50)
    
    processes = []
    
    try:
        # Start MCP agent
        mcp_process = start_mcp_agent()
        processes.append(mcp_process)
        
        # Wait a bit for MCP agent to start
        print("⏱️  Waiting for MCP agent to initialize...")
        time.sleep(3)
        
        # Start FastAPI backend
        api_process = start_fastapi_backend()
        processes.append(api_process)
        
        # Wait for backend to start
        print("⏱️  Waiting for FastAPI backend to start...")
        time.sleep(5)
        
        # Check health
        if check_health():
            print("✅ Backend is healthy!")
        else:
            print("⚠️  Backend health check failed, but continuing...")
        
        print("\n🎯 Demo is ready!")
        print("📋 Services:")
        print("   • MCP Agent: Running on port 8000")
        print("   • FastAPI Backend: http://localhost:3001")
        print("   • Frontend: Start with 'npm run dev' in frontend/")
        print("\n💡 Demo Tips:")
        print("   • Try: 'Show me apartments under $2000'")
        print("   • Try: 'I need a 2-bedroom apartment'")
        print("   • Try: 'Find properties in downtown area'")
        print("\n🛑 Press Ctrl+C to stop all services")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping demo services...")
        for process in processes:
            process.terminate()
        print("✅ Demo stopped successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        for process in processes:
            process.terminate()

if __name__ == "__main__":
    main()