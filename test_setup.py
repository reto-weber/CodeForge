#!/usr/bin/env python3
"""
Test script for container manager functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_without_docker():
    """Test the container manager imports and basic functionality without Docker."""
    try:
        from container_manager import ContainerManager
        print("✓ Container manager module imported successfully")
        
        try:
            # This will fail if Docker is not running, which is expected
            manager = ContainerManager()
            print("✓ Docker is available and running")
            return True
        except RuntimeError as e:
            print(f"⚠ Docker not available: {e}")
            print("This is expected if Docker Desktop is not running.")
            return False
            
    except ImportError as e:
        print(f"✗ Failed to import container manager: {e}")
        return False

def test_main_app():
    """Test that the main app can import and run without Docker."""
    try:
        import main
        print("✓ Main application imports successfully")
        
        # Test that we can get the container manager (will fail gracefully)
        try:
            from container_manager import get_container_manager
            manager = get_container_manager()
            print("✓ Container manager initialized")
        except RuntimeError:
            print("⚠ Container manager failed to initialize (Docker not running)")
        
        return True
    except Exception as e:
        print(f"✗ Failed to import main application: {e}")
        return False

if __name__ == "__main__":
    print("Testing Code Compiler and Runner - Docker Integration")
    print("=" * 50)
    
    docker_available = test_without_docker()
    app_working = test_main_app()
    
    print("\n" + "=" * 50)
    if docker_available:
        print("✅ All tests passed! Docker is available.")
        print("You can run the application with: python main.py")
    elif app_working:
        print("⚠ Application is ready but Docker is not running.")
        print("To use Docker containers:")
        print("1. Start Docker Desktop")
        print("2. Run: .\\setup-docker.bat")
        print("3. Then run: python main.py")
        print("\nAlternatively, you can run without Docker (limited functionality):")
        print("python main.py")
    else:
        print("❌ Application has issues. Check the error messages above.")
