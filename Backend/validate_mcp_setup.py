#!/usr/bin/env python3
"""
Validation script for MCP setup in Socratic application.
This script checks that all MCP dependencies and configurations are correct.
"""

import os
import sys
import json
import importlib
from pathlib import Path
from typing import List, Tuple

def check_environment_variables() -> Tuple[bool, List[str]]:
    """Check required environment variables"""
    required_vars = [
        "DATABASE_URL",
        "REDIS_URL", 
        "GEMINI_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return len(missing_vars) == 0, missing_vars

def check_python_dependencies() -> Tuple[bool, List[str]]:
    """Check required Python packages"""
    required_packages = [
        "mcp",
        "mcp-server", 
        "mcp-types",
        "google-generativeai",
        "sqlalchemy",
        "redis",
        "pillow",
        "numpy"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def check_mcp_configuration() -> Tuple[bool, List[str]]:
    """Check MCP configuration files"""
    app_dir = Path(__file__).parent
    config_file = app_dir / "app" / "mcp" / "config" / "server_configs.json"
    
    issues = []
    
    # Check if config file exists
    if not config_file.exists():
        issues.append(f"Configuration file not found: {config_file}")
        return False, issues
    
    # Check if config file is valid JSON
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        issues.append(f"Invalid JSON in configuration file: {e}")
        return False, issues
    
    # Check if required sections exist
    if "mcp_servers" not in config:
        issues.append("Missing 'mcp_servers' section in configuration")
        return False, issues
    
    servers = config["mcp_servers"]
    if not servers:
        issues.append("No servers configured in 'mcp_servers' section")
        return False, issues
    
    # Check each server configuration
    for server_name, server_config in servers.items():
        if "command" not in server_config:
            issues.append(f"Server '{server_name}' missing 'command' field")
        if "args" not in server_config:
            issues.append(f"Server '{server_name}' missing 'args' field")
    
    return len(issues) == 0, issues

def check_mcp_server_files() -> Tuple[bool, List[str]]:
    """Check that MCP server files exist"""
    app_dir = Path(__file__).parent
    servers_dir = app_dir / "app" / "mcp" / "servers"
    
    required_servers = [
        "smart_practice_server.py",
        "database_server.py",
        "filesystem_server.py", 
        "external_api_server.py"
    ]
    
    missing_files = []
    for server_file in required_servers:
        server_path = servers_dir / server_file
        if not server_path.exists():
            missing_files.append(str(server_path))
    
    return len(missing_files) == 0, missing_files

def check_database_connection() -> Tuple[bool, str]:
    """Check database connection"""
    try:
        from sqlalchemy import create_engine, text
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return False, "DATABASE_URL not set"
        
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return True, "Database connection successful"
            
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"

def check_redis_connection() -> Tuple[bool, str]:
    """Check Redis connection"""
    try:
        import redis
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379") 
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return True, "Redis connection successful"
        
    except Exception as e:
        return False, f"Redis connection failed: {str(e)}"

def main():
    """Main validation function"""
    print("🔍 Validating MCP setup for Socratic application...\n")
    
    all_checks_passed = True
    
    # Check environment variables
    print("1. Checking environment variables...")
    env_ok, missing_env = check_environment_variables()
    if env_ok:
        print("   ✅ All required environment variables are set")
    else:
        print(f"   ❌ Missing environment variables: {', '.join(missing_env)}")
        all_checks_passed = False
    
    # Check Python dependencies
    print("\n2. Checking Python dependencies...")
    deps_ok, missing_deps = check_python_dependencies()
    if deps_ok:
        print("   ✅ All required Python packages are installed")
    else:
        print(f"   ❌ Missing Python packages: {', '.join(missing_deps)}")
        print(f"   💡 Install with: pip install {' '.join(missing_deps)}")
        all_checks_passed = False
    
    # Check MCP configuration
    print("\n3. Checking MCP configuration...")
    config_ok, config_issues = check_mcp_configuration()
    if config_ok:
        print("   ✅ MCP configuration is valid")
    else:
        print("   ❌ MCP configuration issues:")
        for issue in config_issues:
            print(f"      - {issue}")
        all_checks_passed = False
    
    # Check MCP server files
    print("\n4. Checking MCP server files...")
    files_ok, missing_files = check_mcp_server_files()
    if files_ok:
        print("   ✅ All MCP server files exist")
    else:
        print("   ❌ Missing MCP server files:")
        for file_path in missing_files:
            print(f"      - {file_path}")
        all_checks_passed = False
    
    # Check database connection
    print("\n5. Checking database connection...")
    db_ok, db_message = check_database_connection()
    if db_ok:
        print(f"   ✅ {db_message}")
    else:
        print(f"   ❌ {db_message}")
        all_checks_passed = False
    
    # Check Redis connection 
    print("\n6. Checking Redis connection...")
    redis_ok, redis_message = check_redis_connection()
    if redis_ok:
        print(f"   ✅ {redis_message}")
    else:
        print(f"   ❌ {redis_message}")
        all_checks_passed = False
    
    # Final result
    print("\n" + "="*50)
    if all_checks_passed:
        print("🎉 All checks passed! MCP setup is ready.")
        print("\nNext steps:")
        print("1. Start MCP servers: python start_mcp_servers.py start")
        print("2. Run your application")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nFor help:")
        print("- Check the README for setup instructions")
        print("- Ensure all environment variables are set") 
        print("- Install missing dependencies")
        sys.exit(1)

if __name__ == "__main__":
    main()