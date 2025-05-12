#!/usr/bin/env python3
"""
KOI-net Orchestrator Script

This script sets up and configures a KOI-net system with multiple nodes.
It clones repositories, creates config files, and installs dependencies.

Usage:
    python orchestrator.py [--docker]

Configuration Files Generated:
    - config.yaml: Created in each repository directory (e.g., koi-net-coordinator-node/config.yaml)
    - global.env: Created in the project root directory (only in --docker mode)
    - docker-compose.yml: Created in the project root directory (only in --docker mode)
    - Dockerfile: Created in each repository directory (only in --docker mode)
"""
import subprocess
from pathlib import Path
import yaml
from rich.table import Table
from rich.console import Console
import shutil
import argparse
import os

console = Console()


# ---- USER CONFIG ----
# Port to start from for local deployments (ports will increment by 1 for each node)
START_PORT = 8000
# Docker-specific port configuration (fixed ports for each service)
DOCKER_PORTS = {
    "koi-net-coordinator-node": 8080,   # Docker coordinator always uses port 8080
    "koi-net-github-sensor-node": 8001, # GitHub sensor uses port 8001
    "koi-net-hackmd-sensor-node": 8002, # HackMD sensor uses port 8002
    "koi-net-processor-gh-node": 8011,  # GitHub processor uses port 8011
    "koi-net-hackmd-processor-node": 8012  # HackMD processor uses port 8012
}
MODULE_NAMES = {
    "koi-net-coordinator-node": "coordinator_node",
    "koi-net-github-sensor-node": "github_sensor_node",
    "koi-net-hackmd-sensor-node": "hackmd_sensor_node",
    "koi-net-processor-gh-node": "processor_github_node",
    "koi-net-hackmd-processor-node": "processor_hackmd_node"
}

# Templates for each node type, based on configs.txt
NODE_CONFIGS = {
    "koi-net-coordinator-node": lambda port: {
        "server": {
            "host": "127.0.0.1",
            "port": port,
            "path": "/koi-net"
        },
        "koi_net": {
            "node_name": "coordinator",
            "node_rid": "orn:koi-net.node:coordinator+40610903-4272-4494-91fd-1e57501a0980",
            "node_profile": {
                "base_url": f"http://127.0.0.1:{port}/koi-net",
                "node_type": "FULL",
                "provides": {
                    "event": ["orn:koi-net.node", "orn:koi-net.edge"],
                    "state": ["orn:koi-net.node", "orn:koi-net.edge"]
                }
            },
            "cache_directory_path": ".koi",
            "event_queues_path": ".koi/coordinator/queues.json",
            "first_contact": ""
        }
    },
    "koi-net-github-sensor-node": lambda port: {
        "server": {
            "host": "127.0.0.1",
            "port": port,
            "path": "/koi-net"
        },
        "koi_net": {
            "node_name": "github-sensor",
            "node_rid": "orn:koi-net.node:github-sensor+04075a17-b636-48e0-9e2b-104da4710e34",
            "node_profile": {
                "base_url": f"http://127.0.0.1:{port}/koi-net",
                "node_type": "FULL",
                "provides": {
                    "event": ["orn:github.event"],
                    "state": ["orn:github.event"]
                }
            },
            "cache_directory_path": ".koi/github_sensor_cache",
            "event_queues_path": ".koi/queues.json",
            "first_contact": COORD_URL.format(START_PORT)
        },
        "env": {
            "github_token": "GITHUB_TOKEN",
            "github_webhook_secret": "GITHUB_WEBHOOK_SECRET"
        },
        "github": {
            "api_url": "https://api.github.com/",
            "monitored_repositories": [{"name": "Blockscience/koi-net"}],
            "backfill_max_items": 50,
            "backfill_lookback_days": 30,
            "backfill_state_file_path": ".koi/github/github_state.json"
        }
    },
    "koi-net-hackmd-sensor-node": lambda port: {
        "server": {
            "host": "127.0.0.1",
            "port": port,
            "path": "/koi-net"
        },
        "koi_net": {
            "node_name": "hackmd-sensor",
            "node_rid": "orn:koi-net.node:hackmd-sensor+c1311da2-023f-4ce5-a262-6b9a6db85dea",
            "node_profile": {
                "base_url": f"http://127.0.0.1:{port}/koi-net",
                "node_type": "FULL",
                "provides": {
                    "event": ["orn:hackmd.note"],
                    "state": ["orn:hackmd.note"]
                }
            },
            "cache_directory_path": ".koi/cache",
            "event_queues_path": ".koi/hackmd/queues.json",
            "first_contact": COORD_URL.format(START_PORT)
        },
        "env": {
            "hackmd_api_token": "HACKMD_API_TOKEN"
        },
        "hackmd": {
            "team_path": "blockscience",
            "target_note_ids": ["C1xso4C8SH-ZzDaloTq4Uw"]
        }
    },
    "koi-net-processor-gh-node": lambda port: {
        "server": {
            "host": "127.0.0.1",
            "port": port,
            "path": "/koi-net"
        },
        "koi_net": {
            "node_name": "processor_github",
            "node_rid": "orn:koi-net.node:processor_github+0bf78f28-9f56-4d31-8377-a33f49a0828e",
            "node_profile": {
                "base_url": f"http://127.0.0.1:{port}/koi-net",
                "node_type": "FULL",
                "provides": {
                    "event": [],
                    "state": []
                }
            },
            "cache_directory_path": ".koi/processor-github/cache",
            "event_queues_path": ".koi/processor-github/queues.json",
            "first_contact": COORD_URL.format(START_PORT)
        },
        "index_db_path": ".koi/processor-github/index.db",
        "env": {
            "github_token": "GITHUB_TOKEN"
        }
    },
    "koi-net-hackmd-processor-node": lambda port: {
        "server": {
            "host": "127.0.0.1",
            "port": port,
            "path": "/koi-net"
        },
        "koi_net": {
            "node_name": "processor_hackmd",
            "node_rid": "orn:koi-net.node:processor_hackmd+62eabec3-ed43-4122-94cc-ea7aa8701fde",
            "node_profile": {
                "base_url": f"http://127.0.0.1:{port}/koi-net",
                "node_type": "FULL",
                "provides": {
                    "event": [],
                    "state": []
                }
            },
            "cache_directory_path": ".koi/processor-hackmd",
            "event_queues_path": ".koi/processor-hackmd/queues.json",
            "first_contact": COORD_URL.format(START_PORT)
        },
        "fetch_retry_initial": 30,
        "fetch_retry_multiplier": 2,
        "fetch_retry_max_attempts": 3,
        "index_db_path": ".koi/index_db/index.db"
    }
}

REPO_ORDER = [
    "koi-net-coordinator-node",
    "koi-net-hackmd-sensor-node",
    "koi-net-github-sensor-node",
    "koi-net-processor-gh-node",
    "koi-net-hackmd-processor-node"
]

# ---------------------
def run(cmd, cwd=None):
    console.print(f"$ {' '.join(cmd)}" + (f" (in {cwd})" if cwd else ""))
    subprocess.run(cmd, check=True, cwd=cwd)

def clone_repo(repo):
    if not Path(repo).exists():
        run(["git", "clone", f"https://github.com/BlockScience/{repo}", repo])
    else:
        console.print(f"Repo {repo} already exists, skipping clone.")
    return repo

def write_full_config(repo_dir, config_dict):
    """
    Write the configuration YAML file to the specified repository directory
    
    This creates a config.yaml file in each repository's root directory containing
    server settings, node configuration, and network settings.
    
    Args:
        repo_dir: Repository directory path
        config_dict: Configuration dictionary to write
        
    Returns:
        Path to the created config file
    """
    config_path = Path(repo_dir) / "config.yaml"
    
    # Remove existing config file if it exists
    if config_path.exists():
        config_path.unlink()
        console.print(f"Removed existing {config_path}")
        
    with open(config_path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    console.print(f"Wrote {config_path}")
    return config_path

def write_dockerfile(repo_dir, module_name, port):
    """
    Generate a Dockerfile based on the template
    
    Args:
        repo_dir: The repository directory
        module_name: The Python module name to import
        port: The port number to use for this container
    """
    template_path = Path(__file__).parent / "templates" / "Dockerfile.template"
    if not template_path.exists():
        console.print(f"[bold red]Dockerfile template not found at {template_path}[/bold red]")
        console.print("[bold yellow]This file should be part of the repository in the templates directory.[/bold yellow]")
        return
    
    with open(template_path, "r") as f:
        template_content = f.read()
    
    # Replace placeholders in template
    # The template may use ${MODULE_NAME} or $MODULE_NAME format
    dockerfile_content = template_content.replace("${MODULE_NAME}", module_name).replace("$MODULE_NAME", module_name)
    
    # Replace the default port with the specified port
    dockerfile_content = dockerfile_content.replace("ARG PORT=8080", f"ARG PORT={port}")
    
    dockerfile_path = Path(repo_dir) / "Dockerfile"
    
    # Remove existing Dockerfile if it exists
    if dockerfile_path.exists():
        dockerfile_path.unlink()
        console.print(f"[bold yellow]Removed existing Dockerfile at {dockerfile_path}[/bold yellow]")
    
    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_content)
    
    console.print(f"[bold green]Generated Dockerfile at {dockerfile_path} with PORT={port}[/bold green]")
    return dockerfile_path

def _get_exec_path(venv_base_dir: Path, executable_name: str) -> Path | None:
    """Finds an executable (like python or pip) in standard venv bin/Scripts folders."""
    for sub_dir in ["bin", "Scripts"]: # Scripts for Windows, bin for POSIX
        path = venv_base_dir / sub_dir / executable_name
        if path.exists():
            return path.resolve()
    return None

def install_requirements(repo_dir_str: str):
    repo_path = Path(repo_dir_str)
    venv_path = repo_path / ".venv"
    requirements_path = repo_path / "requirements.txt"

    # 1. Create venv if it doesn't exist
    if not venv_path.exists():
        console.print(f"Creating venv with 'python3 -m venv' in {venv_path}...")
        try:
            run(["python3", "-m", "venv", str(venv_path.name)], cwd=str(repo_path))
        except subprocess.CalledProcessError as e_venv:
            console.print(f"[bold red]Error: 'python3 -m venv' command failed. Error: {e_venv}[/bold red]")
            console.print("[bold yellow]Ensure the 'python3' command can create virtual environments.[/bold yellow]")
            return # Stop if venv creation fails
        except FileNotFoundError:
            console.print("[bold red]Error: 'python3' command not found. Please install Python 3.[/bold red]")
            return
    else:
        console.print(f"Venv already exists in {venv_path}, skipping creation.")

    # 2. Find Python and Pip in the venv
    venv_python_executable = _get_exec_path(venv_path, "python") or _get_exec_path(venv_path, "python3")
    venv_pip_executable = _get_exec_path(venv_path, "pip") or _get_exec_path(venv_path, "pip3")
    if not venv_python_executable or not venv_pip_executable:
        console.print(f"[bold red]Error: Python or pip not found in venv {venv_path} after creation attempt.[/bold red]")
        console.print(f"DEBUG: venv_path={venv_path.resolve()}")
        console.print(f"DEBUG: repo_path={repo_path.resolve()}")
        console.print(f"DEBUG: Contents of venv_path: {list(venv_path.iterdir()) if venv_path.exists() else 'DOES NOT EXIST'}")
        bin_dir = venv_path / 'bin'
        console.print(f"DEBUG: Contents of bin_dir: {list(bin_dir.iterdir()) if bin_dir.exists() else 'DOES NOT EXIST'}")
        if venv_path.exists():
            console.print(f"[bold yellow]Attempting to remove venv at {venv_path} for a fresh start next time...[/bold yellow]")
            try:
                shutil.rmtree(venv_path)
                console.print(f"[bold green]Successfully removed {venv_path}. Please re-run the script.[/bold green]")
            except Exception as e_rm:
                console.print(f"[bold red]Failed to remove {venv_path}: {e_rm}. Please remove it manually.[/bold red]")
        return

    # 3. Install requirements using the venv's pip
    if requirements_path.exists():
        console.print(f"Installing requirements from {requirements_path} into {venv_path} using {venv_pip_executable} install...")
        try:
            run([
                str(venv_pip_executable), "install",
                "-r", str(requirements_path.name)
            ], cwd=str(repo_path))
        except subprocess.CalledProcessError as e_install:
            console.print(f"[bold red]Error during 'pip install': {e_install}. Pip executable: {venv_pip_executable}[/bold red]")
            if hasattr(e_install, 'stderr') and e_install.stderr and ("Library not loaded" in e_install.stderr.decode(errors='ignore') or "dyld" in e_install.stderr.decode(errors='ignore')):
                 console.print("[bold yellow]This looks like a broken Python/Pip interpreter in the venv (dylid issue).[/bold yellow]")
                 if venv_path.exists():
                    console.print(f"[bold yellow]Attempting to remove broken venv at {venv_path} for a fresh start next time...[/bold yellow]")
                    try:
                        shutil.rmtree(venv_path)
                        console.print(f"[bold green]Successfully removed {venv_path}. Please re-run the script.[/bold green]")
                    except Exception as e_rm:
                        console.print(f"[bold red]Failed to remove {venv_path}: {e_rm}. Please remove it manually.[/bold red]")
            else:
                 console.print("[bold yellow]Consider manually deleting the .venv directory in this repository and re-running the script.[/bold yellow]")
            return # Stop processing this repo if install fails
    else:
        console.print(f"No requirements.txt in {repo_dir_str}, skipping install.")

def copy_docker_compose_template():
    """
    Copy the docker-compose template to the project root
    
    This generates a docker-compose.yml file with the correct ports
    and service names matching the node configuration.
    
    The service names and ports in docker-compose.yml are:
    - coordinator: Port 8080
    - github-sensor: Port 8001
    - hackmd-sensor: Port 8002
    - processor-github: Port 8011
    - processor-hackmd: Port 8012
    
    File locations:
    - docker-compose.yml: Created in the project root
    - global.env: Created in the project root with environment variables
    - config/ directory: Created in the project root for mounted volumes
    
    Note: These port assignments are fixed in Docker mode and match the DOCKER_PORTS
    configuration, unlike the sequential port assignments in local mode.
    """
    templates_dir = Path(__file__).parent / "templates"
    docker_compose_template = templates_dir / "docker-compose.template.yml"
    docker_compose_dest = Path(__file__).parent / "docker-compose.yml"
    
    # Remove existing docker-compose.yml if it exists
    if docker_compose_dest.exists():
        docker_compose_dest.unlink()
        console.print(f"[bold yellow]Removed existing docker-compose.yml[/bold yellow]")
    
    if not docker_compose_template.exists():
        console.print("[bold red]ERROR: docker-compose template not found at {docker_compose_template}[/bold red]")
        console.print("[bold yellow]This file should be part of the repository in the templates directory.[/bold yellow]")
        return
    
    # Create config directory if needed for mounted volumes
    config_dir = Path(__file__).parent / "config"
    if not config_dir.exists():
        os.makedirs(config_dir, exist_ok=True)
        console.print(f"[bold green]Created directory: {config_dir}[/bold green]")
    
    # Create a sample global.env file in the root directory if it doesn't exist
    global_env = Path(__file__).parent / "global.env"
    global_env_example = Path(__file__).parent / "global.env.example"
    
    if not global_env.exists():
        # First check if we have an example file to copy from
        if global_env_example.exists():
            shutil.copy2(global_env_example, global_env)
            console.print(f"[bold green]Copied global.env.example to {global_env}[/bold green]")
        else:
            # Create a new file with helpful comments if no example exists
            with open(global_env, "w") as f:
                f.write("""# Global environment variables for all KOI-net containers
# This file is used by all Docker containers via the 'env_file' setting in docker-compose.yml
# You MUST edit this file to add your actual API tokens before running the containers

# GitHub API token for accessing repository data
# Create one at: https://github.com/settings/tokens
# Required scopes: repo, read:org
GITHUB_TOKEN=

# GitHub webhook secret for validating incoming webhooks
# Can be any random string you create
GITHUB_WEBHOOK_SECRET=

# HackMD API token for accessing note data
# Get this from your HackMD account settings
HACKMD_API_TOKEN=
""")
            console.print(f"[bold green]Created sample environment file: {global_env}[/bold green]")
    else:
        console.print(f"[bold green]Using existing environment file: {global_env}[/bold green]")
        console.print(f"[bold yellow]Make sure it contains valid API tokens for GitHub and HackMD[/bold yellow]")
        console.print("[bold green]docker-compose template created![/bold green]")
    
    # Create a modified copy of the docker-compose template with the correct ports
    with open(docker_compose_template, 'r') as src_file:
        template_content = src_file.read()
        
    # Replace port placeholders with actual values from DOCKER_PORTS
    for repo, port in DOCKER_PORTS.items():
        # Replace ports in all relevant places
        template_content = template_content.replace(f"PORT={port}", f"PORT={port}")
        template_content = template_content.replace(f"\"{port}:{port}\"", f"\"{port}:{port}\"")
        template_content = template_content.replace(f"localhost:{port}", f"localhost:{port}")
        
    # Write the modified template to the destination
    with open(docker_compose_dest, 'w') as dest_file:
        dest_file.write(template_content)
        
    console.print(f"[bold green]Copied docker-compose.yml to {docker_compose_dest} with ports from DOCKER_PORTS[/bold green]")
    console.print(f"[bold green]Volume mounts in docker-compose.yml are configured based on cache_directory_path in node configs[/bold green]")

def main(is_docker=False):
    """
    Main function to orchestrate KOI-net system setup
    
    This function:
    1. Clones the required repositories if they don't exist
    2. Removes any existing configuration files
    3. Generates config.yaml files in each repository
    4. Creates Docker configuration files if in Docker mode
    5. Sets up virtual environments and installs dependencies
    
    Args:
        is_docker (bool): Whether to run in Docker mode, which changes URLs for container networking
                          and generates Docker configuration files
    
    Configuration files created:
    - Each repo/config.yaml: Node configuration files
    - ./docker-compose.yml: Docker Compose configuration (in Docker mode)
    - ./global.env: Environment variables for Docker (in Docker mode)
    - Each repo/Dockerfile: Docker build instructions (in Docker mode)
    """
    global COORD_URL
    
    # Initialize the port counter for local mode
    # In local mode, ports increment sequentially from START_PORT (8000, 8001, 8002...)
    # In Docker mode, we'll use the fixed port numbers from DOCKER_PORTS
    port = START_PORT

    # Clean up existing configuration if in Docker mode
    if is_docker:
        # Remove existing docker-compose.yml but preserve global.env
        docker_compose_path = Path(__file__).parent / "docker-compose.yml"
        
        if docker_compose_path.exists():
            docker_compose_path.unlink()
            console.print("[bold yellow]Removed existing docker-compose.yml[/bold yellow]")
            
        # Create global.env.example if it doesn't exist
        global_env_example = Path(__file__).parent / "global.env.example"
        if not global_env_example.exists():
            with open(global_env_example, "w") as f:
                f.write("""GITHUB_TOKEN=
HACKMD_API_TOKEN=
GITHUB_WEBHOOK_SECRET=
""")
            console.print("[bold green]Created global.env.example template[/bold green]")
            
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / "templates"
    if not templates_dir.exists():
        os.makedirs(templates_dir)
        console.print(f"Created templates directory at {templates_dir}")
        
    # Create Dockerfile template if it doesn't exist and docker mode is enabled
    if is_docker:
        console.print("[bold yellow]Docker mode enabled - will create Docker configuration files[/bold yellow]")
        dockerfile_template = templates_dir / "Dockerfile.template"
        if not dockerfile_template.exists():
            console.print("[bold red]ERROR: Dockerfile template not found at {dockerfile_template}[/bold red]")
            console.print("[bold yellow]This file should be part of the repository in the templates directory.[/bold yellow]")
            return
            
        console.print(f"[bold green]Using Dockerfile template: {dockerfile_template}[/bold green]")
            
        # Generate docker-compose.yml with ports from DOCKER_PORTS
        copy_docker_compose_template()

    # Determine coordinator port (in case order changes)
    coordinator_index = REPO_ORDER.index("koi-net-coordinator-node")
    coordinator_port = START_PORT + coordinator_index
        
    # Set the coordinator URL based on whether we're in docker mode
    coordinator_docker_port = DOCKER_PORTS["koi-net-coordinator-node"]
    if is_docker:
        # In Docker mode, use the service name (always "coordinator") and Docker port
        COORD_URL = f"http://coordinator:{coordinator_docker_port}/koi-net"
        console.print(f"[bold green]Using Docker coordinator URL: {COORD_URL}[/bold green]")
    else:
        # In local mode, use localhost and the incremental port
        COORD_URL = f"http://127.0.0.1:{coordinator_port}/koi-net"
    table = Table(title="KOI-net System Overview")
    table.add_column("Repo", style="cyan", no_wrap=True)
    table.add_column("Node Name", style="magenta")
    table.add_column("Port", style="green")
    table.add_column("Node Type", style="yellow")
    table.add_column("Cache Path", style="blue")
    table.add_column("Config Path", style="white")
    table.add_column("First Contact", style="red")
    for i, repo in enumerate(REPO_ORDER):
        repo_dir = clone_repo(repo)
        # Select the appropriate port based on mode:
        # - Docker mode: Use fixed ports from DOCKER_PORTS dictionary
        # - Local mode: Use sequential ports starting from START_PORT
        node_port = DOCKER_PORTS[repo] if is_docker else port
        # Store the actual port used for display in the table
        actual_port = node_port
        config_dict = NODE_CONFIGS[repo](node_port)
        
        # Update the base_url in node_profile for Docker mode
        if is_docker:
            # For Docker, use the service name as host instead of 127.0.0.1
            # Convert the repo name to service name following docker-compose convention
            # koi-net-coordinator-node -> coordinator
            # koi-net-github-sensor-node -> github-sensor
            service_name = repo.replace("koi-net-", "").replace("-node", "")
            
            # Process some special cases for processor nodes to match docker-compose service names
            if service_name == "processor_gh":
                service_name = "processor-github"
            elif service_name == "processor_hackmd":
                service_name = "processor-hackmd"
            elif service_name == "hackmd_sensor":
                service_name = "hackmd-sensor"
            elif service_name == "github_sensor":
                service_name = "github-sensor"
                
            # Update both the base_url to use service name instead of IP
            config_dict["koi_net"]["node_profile"]["base_url"] = f"http://{service_name}:{node_port}/koi-net"
            
        if repo == "koi-net-coordinator-node":
            # Coordinator doesn't need a first_contact URL
            config_dict["koi_net"]["first_contact"] = ""
        else:
            # Non-coordinator nodes need to know how to contact the coordinator
            config_dict["koi_net"]["first_contact"] = COORD_URL
        node_name = config_dict["koi_net"]["node_name"]
        node_type = config_dict["koi_net"]["node_profile"]["node_type"]
        cache_path = config_dict["koi_net"]["cache_directory_path"]
        first_contact = config_dict["koi_net"].get("first_contact", "")
        config_path = write_full_config(repo_dir, config_dict)
        install_requirements(repo_dir)
        
        # Generate Dockerfile if in Docker mode
        if is_docker:
            module_name = MODULE_NAMES.get(repo, "")
            # Use the dedicated Docker port from DOCKER_PORTS
            docker_port = DOCKER_PORTS[repo]
            write_dockerfile(repo_dir, module_name, docker_port)
            
            # Also update the server host to 0.0.0.0 to allow external connections in Docker
            config_dict["server"]["host"] = "0.0.0.0"
            console.print(f"[bold green]Using Docker port {docker_port} for {repo}[/bold green]")
            
        table.add_row(
            repo_dir,
            node_name,
            str(actual_port),
            node_type,
            cache_path,
            str(config_path),
            first_contact or "-"
        )
        port += 1
    console.print(f"\nAll repos cloned, config.yaml written, and requirements installed with standard pip/venv.\n")
    console.print(table)
    
    if is_docker:
        console.print("\n[bold cyan]Port Configuration (Docker Mode):[/bold cyan]")
        console.print("[bold cyan]- Coordinator node: Fixed at port 8080[/bold cyan]")
        console.print("[bold cyan]- GitHub sensor: Fixed at port 8001[/bold cyan]")
        console.print("[bold cyan]- HackMD sensor: Fixed at port 8002[/bold cyan]")
        console.print("[bold cyan]- GitHub processor: Fixed at port 8011[/bold cyan]")
        console.print("[bold cyan]- HackMD processor: Fixed at port 8012[/bold cyan]")
    else:
        console.print("\n[bold cyan]Port Configuration (Local Mode):[/bold cyan]")
        console.print(f"[bold cyan]- Using sequential ports starting from {START_PORT}[/bold cyan]")
    console.print("\n[bold yellow]Each repository now has its own virtual environment in its '.venv/' directory.[/bold yellow]")
    console.print("[bold yellow]To manually run a node script, first 'cd' into its repository directory, then activate its venv:[/bold yellow]")
    console.print("[bold yellow]source .venv/bin/activate[/bold yellow]\n")
    
    if is_docker:
        console.print("[bold green]Docker mode enabled:[/bold green]")
        console.print("[bold green]- Dockerfiles have been generated for all repositories[/bold green]")
        console.print("[bold green]- Configuration URLs set for Docker networking[/bold green]")
        console.print("[bold green]- docker-compose.yml has been copied to project root[/bold green]")
        console.print("[bold green]- Fixed ports assigned: 8080 (coordinator), 8001 (GitHub), 8002 (HackMD), 8011/8012 (processors)[/bold green]")
        console.print("[bold green]- You can now run 'docker-compose up' to start the containers[/bold green]\n")
        console.print("[bold yellow]Important Docker run instructions:[/bold yellow]")
        console.print("[bold yellow]1. Edit global.env in the project root to set your API tokens[/bold yellow]")
        console.print("[bold yellow]2. Run 'docker-compose build' to build the containers[/bold yellow]")
        console.print("[bold yellow]3. Run 'docker-compose up -d' to start the containers in detached mode[/bold yellow]")
        console.print("[bold yellow]4. Check logs with 'docker-compose logs -f'[/bold yellow]\n")
        console.print("[bold cyan]Configuration file locations:[/bold cyan]")
        console.print("[bold cyan]- Node configs: Each repository's config.yaml[/bold cyan]")
        console.print("[bold cyan]- Docker environment: ./global.env[/bold cyan]")
        console.print("[bold cyan]- Docker compose: ./docker-compose.yml[/bold cyan]")
        console.print("[bold cyan]- Docker build files: Each repository's Dockerfile[/bold cyan]\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KOI-net orchestrator script')
    parser.add_argument('--docker', dest='is_docker', action='store_true',
                        help='Run in Docker mode - uses fixed ports (8080,8001,8002,8011,8012), changes coordinator URL format for Docker networking, and generates docker-compose.yml, global.env, and Dockerfiles (default: False)')
    args = parser.parse_args()

    main(is_docker=args.is_docker)
