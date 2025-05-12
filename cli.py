#!/usr/bin/env python3
"""
KOI-Net Runner

This script provides a way to run all KOI-net commands without using make.
It includes commands for setting up repositories, running nodes, and interacting with CLI tools.

Usage:
    python3 run_koi_net.py <command> [options]

Commands:
    setup-all            - Clone repositories and generate configurations
    coordinator          - Run the coordinator node
    github-sensor        - Run the GitHub sensor node
    hackmd-sensor        - Run the HackMD sensor node
    github-processor     - Run the GitHub processor node
    hackmd-processor     - Run the HackMD processor node
    hackmd-processor-cli - Run the HackMD processor node CLI
    github-processor-cli - Run the GitHub processor node CLI
    docker-setup         - Set up Docker configuration
    docker-up            - Start all Docker services
    docker-down          - Stop all Docker services
    clean                - Clean up all generated files
"""

import argparse
import os
import subprocess
import sys
import shutil
from pathlib import Path
import signal

# Base directory for all operations
BASE_DIR = Path(__file__).parent.resolve()

# Configuration for each node
NODE_CONFIGS = {
    "coordinator": {
        "directory": "koi-net-coordinator-node",
        "module": "coordinator_node"
    },
    "github-sensor": {
        "directory": "koi-net-github-sensor-node",
        "module": "github_sensor_node"
    },
    "hackmd-sensor": {
        "directory": "koi-net-hackmd-sensor-node",
        "module": "hackmd_sensor_node"
    },
    "github-processor": {
        "directory": "koi-net-github-processor-node",
        "module": "github_processor_node"
    },
    "hackmd-processor": {
        "directory": "koi-net-hackmd-processor-node",
        "module": "hackmd_processor_node"
    }
}

def run_command(cmd, cwd=None, shell=True, env=None):
    """Run a shell command"""
    print(f"Running command: {cmd}")
    return subprocess.run(cmd, cwd=cwd, shell=shell, env=env)

def setup_all():
    """Clone repositories and generate configurations"""
    print("Setting up all node repositories...")
    run_command(f"python {BASE_DIR}/orchestrator.py", cwd=BASE_DIR)
    print("Setup complete. Virtual environments are ready at .venv in each node directory.")

def docker_setup():
    """Generate Docker configurations"""
    print("Setting up Docker configuration...")
    run_command(f"python {BASE_DIR}/orchestrator.py --docker", cwd=BASE_DIR)
    print("Docker setup complete. You can now use docker-up to start all services.")

def docker_up():
    """Start all Docker services"""
    print("Starting all Docker services...")
    run_command("docker compose up -d", cwd=BASE_DIR)
    print("All services started. Use docker-down to stop them.")

def docker_down():
    """Stop all Docker services"""
    print("Stopping all Docker services...")
    run_command("docker compose down", cwd=BASE_DIR)
    print("All services stopped.")

def clean():
    """Clean up all generated files"""
    print("Cleaning up generated files...")

    # Clean virtual environments
    for node_config in NODE_CONFIGS.values():
        venv_path = BASE_DIR / node_config["directory"] / ".venv"
        if venv_path.exists():
            print(f"Removing virtual environment at {venv_path}")
            shutil.rmtree(venv_path)

    # Clean cache files
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip .git directories
        if '.git' in dirs:
            dirs.remove('.git')

        # Remove pycache directories
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            print(f"Removing {pycache_path}")
            shutil.rmtree(pycache_path)

        # Remove .koi directories
        if '.koi' in dirs:
            koi_path = os.path.join(root, '.koi')
            print(f"Removing {koi_path}")
            shutil.rmtree(koi_path)

        # Remove cache files
        for file in files:
            if file in ['config.yaml', 'Dockerfile'] or file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                print(f"Removing {file_path}")
                os.remove(file_path)

    # Remove docker-compose.yml
    docker_compose = BASE_DIR / "docker-compose.yml"
    if docker_compose.exists():
        print(f"Removing {docker_compose}")
        os.remove(docker_compose)

    print("Cleanup complete.")

def run_node(node_type):
    """Run a specific node"""
    if node_type not in NODE_CONFIGS:
        print(f"Unknown node type: {node_type}")
        return

    config = NODE_CONFIGS[node_type]
    node_dir = BASE_DIR / config["directory"]
    module = config["module"]

    # Set up signal handler to gracefully exit
    def signal_handler(sig, frame):
        print(f"\nShutting down {node_type} node...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    print(f"Running {node_type} node...")
    venv_python = node_dir / ".venv" / "bin" / "python"

    # Ensure virtual environment exists
    if not venv_python.exists():
        print(f"Error: Virtual environment not found at {venv_python}")
        print("Please run 'python run_koi_net.py setup-all' first")
        return

    # Clear log file for sensor nodes
    if node_type == "hackmd-sensor":
        log_file = node_dir / "node.sensor.log"
        if log_file.exists():
            os.remove(log_file)
    elif node_type == "hackmd-processor":
        log_file = node_dir / "node.proc.log"
        if log_file.exists():
            os.remove(log_file)

    # Run the node module
    run_command(f"{venv_python} -m {module}", cwd=node_dir)

def run_cli(node_type, cli_command):
    """Run a CLI command for a node"""
    if node_type == "hackmd-processor":
        node_dir = BASE_DIR / "koi-net-hackmd-processor-node"
        default_command = "list"
    elif node_type == "github-processor":
        node_dir = BASE_DIR / "koi-net-github-processor-node"
        default_command = "list-repos"
    else:
        print(f"CLI not supported for node type: {node_type}")
        return

    venv_python = node_dir / ".venv" / "bin" / "python"

    # Ensure virtual environment exists
    if not venv_python.exists():
        print(f"Error: Virtual environment not found at {venv_python}")
        print(f"Please run 'python run_koi_net.py setup-all' first")
        return

    command = cli_command if cli_command else default_command
    print(f"Running {node_type} CLI with command: {command}")
    run_command(f"{venv_python} -m cli {command}", cwd=node_dir)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run KOI-net commands without make")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Setup commands
    subparsers.add_parser("setup-all", help="Clone repositories and generate configurations")
    subparsers.add_parser("clean", help="Clean up all generated files")

    # Node commands
    for node in NODE_CONFIGS:
        subparsers.add_parser(node, help=f"Run the {node} node")

    # CLI commands
    hackmd_cli = subparsers.add_parser("hackmd-processor-cli", help="Run the HackMD processor CLI")
    hackmd_cli.add_argument("cli_command", nargs="?", default="list",
                           help="CLI command to run (default: list)")

    github_cli = subparsers.add_parser("github-processor-cli", help="Run the GitHub processor CLI")
    github_cli.add_argument("cli_command", nargs="?", default="list-repos",
                           help="CLI command to run (default: list-repos)")

    # Docker commands
    subparsers.add_parser("docker-setup", help="Set up Docker configuration")
    subparsers.add_parser("docker-up", help="Start all Docker services")
    subparsers.add_parser("docker-down", help="Stop all Docker services")

    return parser.parse_args()

def main():
    """Main function to parse arguments and run commands"""
    args = parse_args()

    if not args.command:
        print("Please specify a command. Use --help for more information.")
        return

    # Run the appropriate command
    if args.command == "setup-all":
        setup_all()
    elif args.command == "clean":
        clean()
    elif args.command == "docker-setup":
        docker_setup()
    elif args.command == "docker-up":
        docker_up()
    elif args.command == "docker-down":
        docker_down()
    elif args.command in ["hackmd-processor-cli", "github-processor-cli"]:
        node_type = args.command.split("-")[0] + "-processor"
        run_cli(node_type, getattr(args, "cli_command", None))
    elif args.command in NODE_CONFIGS:
        run_node(args.command)
    else:
        print(f"Unknown command: {args.command}")

if __name__ == "__main__":
    main()
