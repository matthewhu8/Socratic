#!/usr/bin/env python3
"""
Startup script for MCP servers in Socratic application.
This script starts all necessary MCP servers for the application.
"""

import asyncio
import logging
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPServerManager:
    """Manager for starting and monitoring MCP servers"""
    
    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.servers_dir = self.app_dir / "app" / "mcp" / "servers"
        self.config_file = self.app_dir / "app" / "mcp" / "config" / "server_configs.json"
        self.processes: Dict[str, subprocess.Popen] = {}
        
    def load_server_configs(self) -> Dict:
        """Load server configurations from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            return config.get('mcp_servers', {})
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return {}
    
    def validate_environment(self) -> bool:
        """Validate that required environment variables are set"""
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "GEMINI_API_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return False
        
        return True
    
    def start_server(self, server_name: str, config: Dict) -> bool:
        """Start a single MCP server"""
        try:
            # Build command
            command = config.get("command", "python")
            args = config.get("args", [])
            env = os.environ.copy()
            
            # Add server-specific environment variables
            server_env = config.get("env", {})
            for key, value in server_env.items():
                # Resolve environment variable references
                if value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    env[key] = os.getenv(env_var, "")
                else:
                    env[key] = value
            
            # Full command
            full_command = [command] + args
            
            logger.info(f"Starting {server_name} server: {' '.join(full_command)}")
            
            # Start process
            process = subprocess.Popen(
                full_command,
                cwd=self.app_dir,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[server_name] = process
            logger.info(f"{server_name} server started with PID {process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {server_name} server: {e}")
            return False
    
    def start_all_servers(self) -> bool:
        """Start all configured MCP servers"""
        if not self.validate_environment():
            return False
        
        configs = self.load_server_configs()
        if not configs:
            logger.error("No server configurations found")
            return False
        
        success_count = 0
        for server_name, config in configs.items():
            if self.start_server(server_name, config):
                success_count += 1
        
        logger.info(f"Started {success_count}/{len(configs)} MCP servers")
        return success_count > 0
    
    def check_server_health(self, server_name: str) -> bool:
        """Check if a server is running and healthy"""
        if server_name not in self.processes:
            return False
        
        process = self.processes[server_name]
        if process.poll() is not None:
            # Process has terminated
            logger.warning(f"{server_name} server has terminated")
            return False
        
        return True
    
    def stop_server(self, server_name: str) -> bool:
        """Stop a specific server"""
        if server_name not in self.processes:
            logger.warning(f"{server_name} server not found")
            return False
        
        process = self.processes[server_name]
        try:
            process.terminate()
            process.wait(timeout=10)
            logger.info(f"{server_name} server stopped")
            del self.processes[server_name]
            return True
        except subprocess.TimeoutExpired:
            logger.warning(f"Force killing {server_name} server")
            process.kill()
            process.wait()
            del self.processes[server_name]
            return True
        except Exception as e:
            logger.error(f"Error stopping {server_name} server: {e}")
            return False
    
    def stop_all_servers(self):
        """Stop all running servers"""
        server_names = list(self.processes.keys())
        for server_name in server_names:
            self.stop_server(server_name)
    
    def monitor_servers(self):
        """Monitor server health and restart if needed"""
        logger.info("Starting server monitoring...")
        try:
            while True:
                for server_name in list(self.processes.keys()):
                    if not self.check_server_health(server_name):
                        logger.warning(f"Restarting {server_name} server")
                        configs = self.load_server_configs()
                        if server_name in configs:
                            self.start_server(server_name, configs[server_name])
                
                # Check every 30 seconds
                asyncio.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
        finally:
            self.stop_all_servers()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server Manager for Socratic")
    parser.add_argument("action", choices=["start", "stop", "monitor", "status"], 
                       help="Action to perform")
    parser.add_argument("--server", help="Specific server to target (optional)")
    parser.add_argument("--config", help="Configuration file path (optional)")
    
    args = parser.parse_args()
    
    manager = MCPServerManager()
    
    if args.config:
        manager.config_file = Path(args.config)
    
    if args.action == "start":
        if args.server:
            configs = manager.load_server_configs()
            if args.server in configs:
                success = manager.start_server(args.server, configs[args.server])
                sys.exit(0 if success else 1)
            else:
                logger.error(f"Server '{args.server}' not found in configuration")
                sys.exit(1)
        else:
            success = manager.start_all_servers()
            if success:
                logger.info("All servers started successfully")
                # Keep the process running to maintain server connections
                try:
                    while True:
                        asyncio.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Shutting down servers...")
                    manager.stop_all_servers()
            sys.exit(0 if success else 1)
    
    elif args.action == "stop":
        if args.server:
            success = manager.stop_server(args.server)
            sys.exit(0 if success else 1)
        else:
            manager.stop_all_servers()
            logger.info("All servers stopped")
            sys.exit(0)
    
    elif args.action == "monitor":
        manager.start_all_servers()
        manager.monitor_servers()
    
    elif args.action == "status":
        configs = manager.load_server_configs()
        logger.info(f"Configured servers: {list(configs.keys())}")
        for server_name in configs:
            if manager.check_server_health(server_name):
                logger.info(f"{server_name}: RUNNING")
            else:
                logger.info(f"{server_name}: STOPPED")

if __name__ == "__main__":
    main()