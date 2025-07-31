#!/usr/bin/env python3
"""
Integration test for MCP functionality in Socratic application.
This script tests the MCP integration without requiring the full application to be running.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mcp_client_manager():
    """Test MCP client manager initialization"""
    try:
        from app.mcp.client.mcp_client import MCPClientManager
        
        print("🔧 Testing MCP Client Manager...")
        
        # Create client manager
        manager = MCPClientManager()
        
        # Test initialization (this will use mock connections for now)
        await manager.initialize(["smart_practice"])
        
        print("✅ MCP Client Manager initialized successfully")
        
        # Test tool calling (should work with mock responses)
        result = await manager.call_tool(
            "smart_practice",
            "get_student_profile",
            {"student_id": 1, "subject": "mathematics"}
        )
        
        print(f"✅ Tool call successful: {result}")
        
        # Cleanup
        await manager.close()
        
        return True
        
    except Exception as e:
        print(f"❌ MCP Client Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_gemini_service_mcp():
    """Test GeminiService MCP integration"""
    try:
        from app.services.gemini_service import GeminiService
        
        print("\n🤖 Testing GeminiService MCP Integration...")
        
        # Create Gemini service
        gemini_service = GeminiService()
        
        # Test MCP manager initialization
        mcp_manager = await gemini_service._get_mcp_manager()
        
        if mcp_manager:
            print("✅ GeminiService MCP manager initialized")
            
            # Test smart question selection (will use mock data)
            result = await gemini_service.select_next_smart_question(
                student_id=1,
                subject="mathematics",
                chapter="Algebra"
            )
            
            print(f"✅ Smart question selection result: {result}")
            return True
        else:
            print("❌ GeminiService MCP manager failed to initialize")
            return False
            
    except Exception as e:
        print(f"❌ GeminiService MCP test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mcp_server_imports():
    """Test that all MCP servers can be imported"""
    try:
        print("\n📦 Testing MCP Server Imports...")
        
        # Test smart practice server
        from app.mcp.servers.smart_practice_server import SmartPracticeMCPServer
        print("✅ Smart Practice Server imported")
        
        # Test database server
        from app.mcp.servers.database_server import DatabaseMCPServer
        print("✅ Database Server imported")
        
        # Test filesystem server  
        from app.mcp.servers.filesystem_server import FilesystemMCPServer
        print("✅ Filesystem Server imported")
        
        # Test external API server
        from app.mcp.servers.external_api_server import ExternalAPIMCPServer
        print("✅ External API Server imported")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP Server import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_configuration_loading():
    """Test configuration loading"""
    try:
        print("\n⚙️ Testing Configuration Loading...")
        
        import json
        config_file = app_dir / "app" / "mcp" / "config" / "server_configs.json"
        
        if not config_file.exists():
            print(f"❌ Configuration file not found: {config_file}")
            return False
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        if "mcp_servers" not in config:
            print("❌ Missing 'mcp_servers' in configuration")
            return False
        
        servers = config["mcp_servers"]
        print(f"✅ Configuration loaded with {len(servers)} servers")
        
        for server_name in servers:
            print(f"   - {server_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading test failed: {e}")
        return False

def test_environment_setup():
    """Test environment setup"""
    try:
        print("\n🌍 Testing Environment Setup...")
        
        required_vars = ["DATABASE_URL", "REDIS_URL", "GEMINI_API_KEY"]
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
            else:
                print(f"✅ {var} is set")
        
        if missing_vars:
            print(f"⚠️ Missing environment variables: {missing_vars}")
            print("   (This is OK for testing, but required for full functionality)")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment setup test failed: {e}")
        return False

async def run_all_tests():
    """Run all integration tests"""
    print("🚀 Starting MCP Integration Tests...\n")
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Configuration Loading", test_configuration_loading),
        ("MCP Server Imports", test_mcp_server_imports),
        ("MCP Client Manager", test_mcp_client_manager),
        ("GeminiService MCP Integration", test_gemini_service_mcp)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! MCP integration is working correctly.")
        return True
    else:
        print(f"\n⚠️ {total - passed} tests failed. Check the output above for details.")
        return False

async def main():
    """Main test function"""
    success = await run_all_tests()
    
    if success:
        print("\n📝 Next Steps:")
        print("1. Run the validation script: python validate_mcp_setup.py")
        print("2. Start your application normally")
        print("3. Test the smart practice endpoints")
        sys.exit(0)
    else:
        print("\n🔧 Fix the failed tests before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())