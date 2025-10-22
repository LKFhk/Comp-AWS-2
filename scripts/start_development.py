#!/usr/bin/env python3
"""
Development Startup Script for RiskIntel360 Platform
Starts backend and frontend development servers with proper setup.
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path
from threading import Thread

class DevelopmentServer:
    """Development server manager"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.frontend_dir = self.project_root / "frontend"
        self.processes = []
        
    def check_prerequisites(self):
        """Check if all prerequisites are installed"""
        print("🔍 Checking prerequisites...")
        
        # Check Python
        try:
            python_version = subprocess.run([sys.executable, "--version"], 
                                          capture_output=True, text=True)
            print(f"✅ Python: {python_version.stdout.strip()}")
        except:
            print("❌ Python not found")
            return False
        
        # Check Node.js
        try:
            node_version = subprocess.run(["node", "--version"], 
                                        capture_output=True, text=True)
            print(f"✅ Node.js: {node_version.stdout.strip()}")
        except:
            print("❌ Node.js not found")
            return False
        
        # Check npm (try multiple commands for Windows compatibility)
        npm_found = False
        npm_commands = ["npm", "npm.cmd", "npm.exe"]
        
        for npm_cmd in npm_commands:
            try:
                npm_version = subprocess.run([npm_cmd, "--version"], 
                                           capture_output=True, text=True)
                if npm_version.returncode == 0:
                    print(f"✅ npm: {npm_version.stdout.strip()}")
                    npm_found = True
                    break
            except:
                continue
        
        if not npm_found:
            print("❌ npm not found")
            print("💡 Try running: npm --version")
            print("💡 If that works, npm is installed but PATH issue exists")
            return False
        
        return True
    
    def check_docker(self):
        """Check if Docker is available"""
        try:
            docker_version = subprocess.run(["docker", "--version"], 
                                          capture_output=True, text=True)
            if docker_version.returncode == 0:
                print(f"✅ Docker: {docker_version.stdout.strip()}")
                return True
        except:
            pass
        
        print("❌ Docker not found")
        print("💡 Docker is required to run PostgreSQL database")
        print("💡 Please install Docker Desktop from https://www.docker.com/products/docker-desktop")
        return False
    
    def start_database(self):
        """Start PostgreSQL database using Docker"""
        print("🗄️  Starting PostgreSQL database...")
        
        # Check if postgres container is already running
        try:
            result = subprocess.run([
                "docker", "ps", "--filter", "name=riskintel360-postgres", "--format", "{{.Names}}"
            ], capture_output=True, text=True)
            
            if "riskintel360-postgres" in result.stdout:
                print("✅ PostgreSQL database is already running")
                return
        except:
            pass
        
        # Start the database container
        try:
            subprocess.run([
                "docker", "run", "-d",
                "--name", "riskintel360-postgres",
                "-p", "5432:5432",
                "-e", "POSTGRES_DB=riskintel360",
                "-e", "POSTGRES_USER=postgres", 
                "-e", "POSTGRES_PASSWORD=postgres",
                "postgres:15-alpine"
            ], check=True)
            
            print("✅ PostgreSQL database started")
            
            # Wait for database to be ready
            print("⏳ Waiting for database to be ready...")
            for i in range(30):
                try:
                    result = subprocess.run([
                        "docker", "exec", "riskintel360-postgres",
                        "pg_isready", "-U", "postgres", "-d", "riskintel360"
                    ], capture_output=True)
                    
                    if result.returncode == 0:
                        print("✅ Database is ready!")
                        break
                except:
                    pass
                
                time.sleep(1)
            else:
                print("⚠️  Database may still be starting...")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start database: {e}")
            print("💡 Try running: docker run -d --name riskintel360-postgres -p 5432:5432 -e POSTGRES_DB=riskintel360 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres postgres:15-alpine")
    
    def setup_environment(self):
        """Set up development environment"""
        print("\n🔧 Setting up development environment...")
        
        # Check if Docker is available
        if not self.check_docker():
            print("❌ Docker is required for PostgreSQL database")
            return False
        
        # Start PostgreSQL database
        self.start_database()
        
        # Check if virtual environment exists
        venv_path = self.project_root / "venv"
        if not venv_path.exists():
            print("📦 Creating Python virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", "venv"], 
                         cwd=self.project_root)
        
        # Install Python dependencies
        print("📦 Installing Python dependencies...")
        pip_cmd = str(venv_path / "Scripts" / "pip.exe") if os.name == 'nt' else str(venv_path / "bin" / "pip")
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], 
                      cwd=self.project_root)
        
        # Install frontend dependencies
        if self.frontend_dir.exists():
            print("📦 Installing frontend dependencies...")
            npm_commands = ["npm", "npm.cmd", "npm.exe"]
            
            for npm_cmd in npm_commands:
                try:
                    result = subprocess.run([npm_cmd, "install"], cwd=self.frontend_dir)
                    if result.returncode == 0:
                        break
                except:
                    continue
        
        print("✅ Environment setup complete!")
        return True
    
    def start_backend(self):
        """Start backend development server"""
        print("\n🚀 Starting backend server...")
        
        venv_path = self.project_root / "venv"
        python_cmd = str(venv_path / "Scripts" / "python.exe") if os.name == 'nt' else str(venv_path / "bin" / "python")
        
        backend_process = subprocess.Popen([
            python_cmd, "-m", "uvicorn",
            "riskintel360.api.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ], cwd=self.project_root)
        
        self.processes.append(backend_process)
        print("✅ Backend server starting on http://localhost:8000")
        return backend_process
    
    def start_frontend(self):
        """Start frontend development server"""
        print("🚀 Starting frontend server...")
        
        if not self.frontend_dir.exists():
            print("❌ Frontend directory not found")
            return None
        
        # Try different npm commands for Windows compatibility
        npm_commands = ["npm", "npm.cmd", "npm.exe"]
        frontend_process = None
        
        for npm_cmd in npm_commands:
            try:
                frontend_process = subprocess.Popen([
                    npm_cmd, "start"
                ], cwd=self.frontend_dir)
                break
            except:
                continue
        
        if not frontend_process:
            print("❌ Could not start frontend server")
            return None
        
        self.processes.append(frontend_process)
        print("✅ Frontend server starting on http://localhost:3000")
        return frontend_process
    
    def wait_for_servers(self):
        """Wait for servers to be ready"""
        print("\n⏳ Waiting for servers to start...")
        
        # Wait for backend
        backend_ready = False
        for i in range(30):  # Wait up to 30 seconds
            try:
                import requests
                response = requests.get("http://localhost:8000/health", timeout=1)
                if response.status_code == 200:
                    backend_ready = True
                    break
            except:
                pass
            time.sleep(1)
        
        if backend_ready:
            print("✅ Backend server is ready!")
        else:
            print("⚠️  Backend server may still be starting...")
        
        # Frontend typically takes longer to start
        print("⏳ Frontend server is starting (this may take a minute)...")
        time.sleep(5)
        print("✅ Frontend server should be ready soon!")
    
    def run_tests(self):
        """Run the test suite"""
        print("\n🧪 Running test suite...")
        
        try:
            result = subprocess.run([
                sys.executable, "scripts/run_fixed_tests.py"
            ], cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ All tests passed!")
                return True
            else:
                print("❌ Some tests failed")
                return False
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False
    
    def open_browser(self):
        """Open browser to the frontend URL"""
        import webbrowser
        import threading
        
        def delayed_open():
            time.sleep(3)  # Wait a bit more for frontend to be ready
            try:
                print("🌐 Opening browser to http://localhost:3000...")
                webbrowser.open("http://localhost:3000")
            except Exception as e:
                print(f"⚠️  Could not auto-open browser: {e}")
                print("💡 Please manually open http://localhost:3000 in your browser")
        
        # Open browser in a separate thread so it doesn't block
        browser_thread = threading.Thread(target=delayed_open)
        browser_thread.daemon = True
        browser_thread.start()
    
    def cleanup(self):
        """Clean up processes"""
        print("\n🧹 Shutting down servers...")
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except:
                pass
        
        # Optionally stop the database container
        print("💡 PostgreSQL database is still running in Docker")
        print("💡 To stop it, run: docker stop riskintel360-postgres")
        print("💡 To remove it, run: docker rm riskintel360-postgres")
        
        print("✅ Servers shut down")
    
    def start_development_mode(self):
        """Start full development environment"""
        print("🚀 RiskIntel360 Platform - Development Startup")
        print("=" * 50)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Prerequisites not met. Please install required software.")
            return False
        
        # Setup environment
        if not self.setup_environment():
            return False
        
        # Start servers
        backend_process = self.start_backend()
        time.sleep(3)  # Give backend time to start
        
        frontend_process = self.start_frontend()
        
        # Wait for servers
        self.wait_for_servers()
        
        print("\n" + "=" * 50)
        print("🎉 Development environment is ready!")
        print("📋 Available services:")
        print("   🌐 Frontend: http://localhost:3000")
        print("   🔧 Backend API: http://localhost:8000")
        print("   📚 API Docs: http://localhost:8000/docs")
        print("   ❤️  Health Check: http://localhost:8000/health")
        print("\n💡 Press Ctrl+C to stop all servers")
        print("=" * 50)
        
        # Auto-open browser after a short delay
        self.open_browser()
        
        return True
    
    def start_test_mode(self):
        """Start in test mode"""
        print("🧪 RiskIntel360 Platform - Test Mode")
        print("=" * 50)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Prerequisites not met. Please install required software.")
            return False
        
        # Setup environment
        self.setup_environment()
        
        # Run tests
        success = self.run_tests()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 All tests passed! Platform is ready for development.")
        else:
            print("❌ Some tests failed. Please check the output above.")
        print("=" * 50)
        
        return success


def main():
    """Main entry point"""
    server = DevelopmentServer()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n\n🛑 Received interrupt signal...")
        server.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode
        success = server.start_test_mode()
        sys.exit(0 if success else 1)
    else:
        # Development mode
        success = server.start_development_mode()
        
        if success:
            try:
                # Keep running until interrupted
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        
        server.cleanup()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()