#!/usr/bin/env python3
"""Setup script for EventFlow"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command"""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False


def check_prerequisites():
    """Check if required tools are installed"""
    print("\n🔍 Checking prerequisites...")
    
    tools = {
        "docker": "docker --version",
        "docker-compose": "docker-compose --version",
        "python": "python --version"
    }
    
    missing = []
    for tool, cmd in tools.items():
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
            print(f"  ✅ {tool} found")
        except subprocess.CalledProcessError:
            print(f"  ❌ {tool} not found")
            missing.append(tool)
    
    if missing:
        print(f"\n❌ Missing tools: {', '.join(missing)}")
        print("\nPlease install:")
        if "docker" in missing:
            print("  - Docker: https://docs.docker.com/get-docker/")
        if "docker-compose" in missing:
            print("  - Docker Compose: https://docs.docker.com/compose/install/")
        if "python" in missing:
            print("  - Python 3.11+: https://www.python.org/downloads/")
        return False
    
    return True


def setup_environment():
    """Setup environment file"""
    print("\n📝 Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("  ℹ️  .env file already exists")
        return True
    
    if env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        print("  ✅ Created .env from .env.example")
        return True
    else:
        print("  ❌ .env.example not found")
        return False


def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    return run_command(
        "pip install -r requirements.txt",
        "Installing packages"
    )


def start_services():
    """Start Docker services"""
    print("\n🚀 Starting services...")
    
    if not run_command(
        "docker-compose up -d",
        "Starting Docker containers"
    ):
        return False
    
    print("\n⏳ Waiting for services to be ready...")
    import time
    time.sleep(10)
    
    return True


def verify_services():
    """Verify services are running"""
    print("\n✅ Verifying services...")
    
    import httpx
    
    try:
        response = httpx.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("  ✅ API is healthy")
            return True
        else:
            print(f"  ❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Could not connect to API: {e}")
        return False


def print_success():
    """Print success message"""
    print("\n" + "="*60)
    print("  🎉 EventFlow is ready!")
    print("="*60)
    print("\n📊 Access points:")
    print("  - API:        http://localhost:8000")
    print("  - API Docs:   http://localhost:8000/docs")
    print("  - Prometheus: http://localhost:9090")
    print("  - Grafana:    http://localhost:3000 (admin/admin)")
    print("\n🧪 Try it out:")
    print("  python scripts/producer.py --count 100")
    print("  python scripts/monitor.py")
    print("\n📚 Documentation:")
    print("  - README.md - Project overview")
    print("  - QUICKSTART.md - Getting started guide")
    print("  - ARCHITECTURE.md - System design")
    print("  - INTERVIEW_GUIDE.md - Interview prep")
    print("\n💡 Next steps:")
    print("  1. Read QUICKSTART.md")
    print("  2. Send test events")
    print("  3. Explore the dashboards")
    print("  4. Review the code")
    print("  5. Prepare for interviews with INTERVIEW_GUIDE.md")
    print()


def main():
    """Main setup flow"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║              EventFlow Setup Script                       ║
    ║                                                           ║
    ║     Distributed Event Processing & Reliability System    ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Failed to setup environment")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies")
        sys.exit(1)
    
    # Start services
    if not start_services():
        print("\n❌ Failed to start services")
        print("\nTry running: docker-compose logs")
        sys.exit(1)
    
    # Verify services
    if not verify_services():
        print("\n⚠️  Services started but health check failed")
        print("\nCheck logs: docker-compose logs -f")
        sys.exit(1)
    
    # Success!
    print_success()


if __name__ == "__main__":
    main()
