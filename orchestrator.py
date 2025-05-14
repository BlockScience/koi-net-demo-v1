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
# Port configuration for all modes (local and Docker)
SERVICE_PORTS = {
    "koi-net-coordinator-node": 8080,   # Coordinator uses port 8080
    "koi-net-github-sensor-node": 8001, # GitHub sensor uses port 8001
    "koi-net-hackmd-sensor-node": 8002, # HackMD sensor uses port 8002
    "koi-net-github-processor-node": 8011,  # GitHub processor uses port 8011
    "koi-net-hackmd-processor-node": 8012  # HackMD processor uses port 8012
}

MODULE_NAMES = {
    "koi-net-coordinator-node": "coordinator_node",
    "koi-net-github-sensor-node": "github_sensor_node",
    "koi-net-hackmd-sensor-node": "hackmd_sensor_node",
    "koi-net-github-processor-node": "github_processor_node",  # Keep as github_processor_node for backwards compatibility
    "koi-net-hackmd-processor-node": "hackmd_processor_node"
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
            "first_contact": ""  # Will be set properly in the main function
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
            "first_contact": ""  # Will be set properly in the main function
        },
        "env": {
            "hackmd_api_token": "HACKMD_API_TOKEN"
        },
        "hackmd": {
            "team_path": "blockscience",
            "target_note_ids": ["C1xso4C8SH-ZzDaloTq4Uw"]
        }
    },
    "koi-net-github-processor-node": lambda port: {
        "server": {
            "host": "127.0.0.1",
            "port": port,
            "path": "/koi-net"
        },
        "koi_net": {
            "node_name": "github-processor",
            "node_rid": "orn:koi-net.node:github-processor+0bf78f28-9f56-4d31-8377-a33f49a0828e",
            "node_profile": {
                "base_url": f"http://127.0.0.1:{port}/koi-net",
                "node_type": "FULL",
                "provides": {
                    "event": [],
                    "state": []
                }
            },
            "cache_directory_path": ".koi/github-processor/cache",
            "event_queues_path": ".koi/github-processor/queues.json",
            "first_contact": ""  # Will be set properly in the main function
        },
        "index_db_path": ".koi/github-processor/index.db",
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
            "node_name": "hackmd-processor",
            "node_rid": "orn:koi-net.node:hackmd-processor+62eabec3-ed43-4122-94cc-ea7aa8701fde",
            "node_profile": {
                "base_url": f"http://127.0.0.1:{port}/koi-net",
                "node_type": "FULL",
                "provides": {
                    "event": [],
                    "state": []
                }
            },
            "cache_directory_path": ".koi/hackmd-processor",
            "event_queues_path": ".koi/hackmd-processor/queues.json",
            "first_contact": ""  # Will be set properly in the main function
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
    "koi-net-github-processor-node",
    "koi-net-hackmd-processor-node"
]

# ---------------------
def run(cmd, cwd=None):
    console.print(f"$ {' '.join(cmd)}" + (f" (in {cwd})" if cwd else ""))
    subprocess.run(cmd, check=True, cwd=cwd)

def clone_repo(repo, branch="demo-1"):
    """
    Clone a repository and checkout a specific branch

    Args:
        repo (str): Repository name to clone
        branch (str): Branch name to checkout (default: demo-1)

    Returns:
        str: Repository directory name
    """
    # Handle legacy repo name in case it's still used elsewhere
    if repo == "koi-net-processor-gh-node":
        target_repo = "koi-net-github-processor-node"
        if Path(target_repo).exists():
            console.print(f"Using {target_repo} instead of {repo}")
            return target_repo
        elif Path(repo).exists():
            console.print(f"Renaming {repo} to {target_repo}")
            shutil.move(repo, target_repo)
            return target_repo
        else:
            repo = target_repo

    if not Path(repo).exists():
        try:
            # First try to clone with the specific branch
            console.print(f"[bold cyan]Cloning {repo} with branch {branch}...[/bold cyan]")
            run(["git", "clone", "-b", branch, f"https://github.com/BlockScience/{repo}", repo])
            console.print(f"[bold green]Successfully cloned {repo} with branch {branch}[/bold green]")
        except subprocess.CalledProcessError:
            # If branch doesn't exist, fall back to default branch
            console.print(f"[bold yellow]Branch {branch} not found in {repo}, falling back to default branch[/bold yellow]")
            run(["git", "clone", f"https://github.com/BlockScience/{repo}", repo])
            console.print(f"[bold green]Successfully cloned {repo} with default branch[/bold green]")
    else:
        console.print(f"Repo {repo} already exists, will try to update to {branch} branch.")
        # Try to fetch and checkout the specified branch for existing repos
        try:
            run(["git", "fetch"], cwd=repo)
            # Check if the branch exists remotely
            result = subprocess.run(
                ["git", "ls-remote", "--heads", "origin", branch],
                cwd=repo,
                capture_output=True,
                text=True
            )
            if branch in result.stdout:
                # Branch exists, try to check it out
                run(["git", "checkout", branch], cwd=repo)
                console.print(f"[bold green]Successfully checked out {branch} branch in {repo}[/bold green]")
            else:
                console.print(f"[bold yellow]Branch {branch} does not exist in remote for {repo}[/bold yellow]")
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Error updating {repo} to {branch} branch: {e}[/bold red]")
            console.print(f"[bold yellow]Using existing repo state for {repo}[/bold yellow]")
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

def create_env_files(repo_dir, config_dict):
    """
    Create or update .env files in the repository directory

    This function creates .env files in each repository with the necessary
    environment variables such as GitHub tokens and HackMD API tokens.

    Args:
        repo_dir: Repository directory path
        config_dict: Configuration dictionary containing environment variables

    Returns:
        Path to the created .env file or None if no env variables exist
    """
    # Check if the config has env settings
    if 'env' not in config_dict:
        return None

    env_path = Path(repo_dir) / ".env"
    env_content = []

    # Create or read existing .env file
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.readlines()
            # Remove trailing newlines
            env_content = [line.rstrip() for line in env_content]

    # Get global.env to extract token values
    global_env_path = Path(__file__).parent / "global.env"
    global_env_vars = {}

    if global_env_path.exists():
        with open(global_env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    global_env_vars[key] = value

    # Process environment variables from the config
    for env_var_name, env_var_key in config_dict['env'].items():
        # Check if the env var already exists in the .env file
        var_exists = False
        for i, line in enumerate(env_content):
            if line.startswith(f"{env_var_key}="):
                # Update existing entry if we have a value from global.env
                if env_var_key in global_env_vars and global_env_vars[env_var_key]:
                    env_content[i] = f"{env_var_key}={global_env_vars[env_var_key]}"
                var_exists = True
                break

        # Add new entry if it doesn't exist
        if not var_exists:
            # Use value from global.env if available
            value = global_env_vars.get(env_var_key, "")
            env_content.append(f"{env_var_key}={value}")

    # Write the updated .env file
    with open(env_path, 'w') as f:
        for line in env_content:
            f.write(line + '\n')

    console.print(f"[bold green]Created/updated .env file at {env_path}[/bold green]")
    return env_path

def copy_docker_compose_template():
    """
    Copy the docker-compose template to the project root

    This generates a docker-compose.yml file with the correct ports
    and service names matching the node configuration.

    The service names and ports in docker-compose.yml are:
    - coordinator: Port 8080
    - github-sensor: Port 8001
    - hackmd-sensor: Port 8002
    - github-processor: Port 8011
    - hackmd-processor: Port 8012

    File locations:
    - docker-compose.yml: Created in the project root
    - global.env: Created in the project root with environment variables
    - config/ directory: Created in the project root for mounted volumes

    Note: These port assignments are the same in both Docker and local modes and
    match the SERVICE_PORTS configuration.

    Returns:
        bool: True if environment variables are properly set up, False otherwise
    """
    templates_dir = Path(__file__).parent / "templates"
    docker_compose_template = templates_dir / "docker-compose.template.yml"
    docker_compose_dest = Path(__file__).parent / "docker-compose.yml"

    # Remove existing docker-compose.yml if it exists
    if docker_compose_dest.exists():
        docker_compose_dest.unlink()
        console.print(f"[bold yellow]Removed existing docker-compose.yml[/bold yellow]")

    console.print(f"[bold cyan]Checking existence of docker-compose template at {docker_compose_template}[/bold cyan]")
    if not docker_compose_template.exists():
        console.print(f"[bold red]ERROR: docker-compose template not found at {docker_compose_template}[/bold red]")
        console.print("[bold yellow]This file should be part of the repository in the templates directory.[/bold yellow]")
        return False

    # Create a modified copy of the docker-compose template with the correct ports
    with open(docker_compose_template, 'r') as src_file:
        template_content = src_file.read()

    # Replace port placeholders with actual values from SERVICE_PORTS
    for repo, port in SERVICE_PORTS.items():
        # Replace ports in all relevant places
        template_content = template_content.replace(f"PORT={port}", f"PORT={port}")
        template_content = template_content.replace(f"\"{port}:{port}\"", f"\"{port}:{port}\"")
        template_content = template_content.replace(f"localhost:{port}", f"localhost:{port}")

    # Write the modified template to the destination
    with open(docker_compose_dest, 'w') as dest_file:
        dest_file.write(template_content)

    console.print(f"[bold green]Copied docker-compose.yml to {docker_compose_dest} with ports from SERVICE_PORTS[/bold green]")
    console.print(f"[bold green]Volume mounts in docker-compose.yml are configured based on cache_directory_path in node configs[/bold green]")

    return True

def main(is_docker=False, branch="demo-1"):
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
        branch (str): Git branch to checkout for each repository (default: demo-1)

    Configuration files created:
    - Each repo/config.yaml: Node configuration files
    - ./docker-compose.yml: Docker Compose configuration (in Docker mode)
    - ./global.env: Environment variables for Docker (in Docker mode)
    - Each repo/Dockerfile: Docker build instructions (in Docker mode)
    """
    global COORD_URL

    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / "templates"
    if not templates_dir.exists():
        os.makedirs(templates_dir)
        console.print(f"Created templates directory at {templates_dir}")

    # Define global.env paths
    global_env = Path(__file__).parent / "global.env"
    global_env_example = Path(__file__).parent / "global.env.example"

    # Always create global.env if it doesn't exist
    try:
        # Ensure the directory for global.env exists
        console.print(f"[bold cyan]Ensuring directory exists for global.env: {global_env.parent}[/bold cyan]")
        global_env.parent.mkdir(parents=True, exist_ok=True)

        # Check if we already have existing values from an older global.env
        existing_values = {}
        if global_env.exists():
            with open(global_env, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if value:  # Only store non-empty values
                            existing_values[key] = value

        if not global_env.exists():
            # First check if we have an example file to copy from
            console.print(f"[bold cyan]Checking existence of global.env.example at {global_env_example}[/bold cyan]")
            if global_env_example.exists():
                shutil.copy2(global_env_example, global_env)
                console.print(f"[bold green]Copied global.env.example to {global_env}[/bold green]")
            else:
                # Generate a new file with helpful comments if no example exists
                console.print(f"[bold cyan]Creating a new global.env file at {global_env}[/bold cyan]")
                with open(global_env, "w") as f:
                    f.write("""# Global environment variables for all KOI-net containers
# This file is used by all Docker containers via the 'env_file' setting in docker-compose.yml
# You MUST edit this file to add your actual API tokens before running the containers

# GitHub API token for accessing repository data
# Create one at: https://github.com/settings/tokens
# Required scopes: repo, read:org
GITHUB_TOKEN""" + (f"={existing_values.get('GITHUB_TOKEN', '')}" if 'GITHUB_TOKEN' in existing_values else "=") + """

# GitHub webhook secret for validating incoming webhooks
# Can be any random string you create
GITHUB_WEBHOOK_SECRET""" + (f"={existing_values.get('GITHUB_WEBHOOK_SECRET', '')}" if 'GITHUB_WEBHOOK_SECRET' in existing_values else "=") + """

# HackMD API token for accessing note data
# Get this from your HackMD account settings
HACKMD_API_TOKEN""" + (f"={existing_values.get('HACKMD_API_TOKEN', '')}" if 'HACKMD_API_TOKEN' in existing_values else "=") + """
""")
                console.print(f"[bold green]Created sample environment file: {global_env}[/bold green]")
        else:
            console.print(f"[bold green]Using existing environment file: {global_env}[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error creating global.env file: {e}[/bold red]")
        console.print("[bold cyan]Please ensure the script has permissions and the directory paths are correct.[/bold cyan]")
        # Allow other setup steps to continue even if global.env creation/check fails
        pass

    # Set the coordinator URL based on whether we're in docker mode
    coordinator_port = SERVICE_PORTS["koi-net-coordinator-node"]
    if is_docker:
        # In Docker mode, use the service name (always "coordinator") and the port
        COORD_URL = f"http://coordinator:{coordinator_port}/koi-net"
        console.print(f"[bold green]Using Docker coordinator URL: {COORD_URL}[/bold green]")
    else:
        # In local mode, use localhost and the same port
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
        repo_dir = clone_repo(repo, branch)
        # Use the same port for both Docker and local mode
        node_port = SERVICE_PORTS[repo]
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
        if not is_docker:
            install_requirements(repo_dir)
        else:
            console.print(f"[bold yellow]Skipping dependency installation for {repo_dir} (Docker mode)[/bold yellow]")

        # Create or update .env file for the repository
        create_env_files(repo_dir, config_dict)

        # Generate Dockerfile if in Docker mode
        if is_docker:
            module_name = MODULE_NAMES.get(repo, "")
            # Use the dedicated Docker port from SERVICE_PORTS
            docker_port = SERVICE_PORTS[repo]
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

    console.print("\nAll repos cloned and config.yaml written. Requirements installed with standard pip/venv (skipped under Docker mode).\n")
    console.print(table)

    console.print("\n[bold cyan]Port Configuration (All Modes):[/bold cyan]")
    console.print("[bold cyan]- Coordinator node: Port 8080[/bold cyan]")
    console.print("[bold cyan]- GitHub sensor: Port 8001[/bold cyan]")
    console.print("[bold cyan]- HackMD sensor: Port 8002[/bold cyan]")
    console.print("[bold cyan]- GitHub processor: Port 8011[/bold cyan]")
    console.print("[bold cyan]- HackMD processor: Port 8012[/bold cyan]")
    console.print("\n[bold yellow]Each repository now has its own virtual environment in its '.venv/' directory.[/bold yellow]")
    console.print("[bold yellow]To manually run a node script, first 'cd' into its repository directory, then activate its venv:[/bold yellow]")
    console.print("[bold yellow]source .venv/bin/activate[/bold yellow]\n")

    # Clean up existing configuration if in Docker mode
    # Handle Docker-specific setup
    if is_docker:
        console.print("[bold yellow]Docker mode enabled - will create Docker configuration files[/bold yellow]")

        # Remove existing docker-compose.yml
        docker_compose_path = Path(__file__).parent / "docker-compose.yml"
        if docker_compose_path.exists():
            docker_compose_path.unlink()
            console.print("[bold yellow]Removed existing docker-compose.yml[/bold yellow]")

        # Create global.env.example if it doesn't exist
        if not global_env_example.exists():
            with open(global_env_example, "w") as f:
                f.write("""GITHUB_TOKEN=
HACKMD_API_TOKEN=
GITHUB_WEBHOOK_SECRET=
""")
            console.print("[bold green]Created global.env.example template[/bold green]")

        # Validate that environment variables are set in global.env
        # This checks the file that should have been created by the logic above the docker block
        try:
            with open(global_env, 'r') as env_file:
                env_content = env_file.read()
                missing_vars = []

                # Check for empty variables
                if "GITHUB_TOKEN=" in env_content or "GITHUB_TOKEN=\n" in env_content:
                    missing_vars.append("GITHUB_TOKEN")
                if "GITHUB_WEBHOOK_SECRET=" in env_content or "GITHUB_WEBHOOK_SECRET=\n" in env_content:
                    missing_vars.append("GITHUB_WEBHOOK_SECRET")
                if "HACKMD_API_TOKEN=" in env_content or "HACKMD_API_TOKEN=\n" in env_content:
                    missing_vars.append("HACKMD_API_TOKEN")

                if missing_vars:
                    console.print(f"[bold red]WARNING: The following required environment variables are not set in {global_env}:[/bold red]")
                    for var in missing_vars:
                        console.print(f"[bold red]  - {var}[/bold red]")
                    console.print(f"[bold yellow]Please edit {global_env} to add your API tokens before running the containers[/bold yellow]")
                else:
                    console.print(f"[bold green]All required environment variables are set in {global_env}[/bold green]")
        except FileNotFoundError:
             console.print(f"[bold red]ERROR: global.env file not found for validation at {global_env}.[/bold red]")
             # This case should theoretically be handled by the creation block above,
             # but adding a check here makes it more robust.

        # Check if Dockerfile template exists
        dockerfile_template = templates_dir / "Dockerfile.template"
        if not dockerfile_template.exists():
            console.print(f"[bold red]ERROR: Dockerfile template not found at {dockerfile_template}[/bold red]")
            console.print("[bold yellow]This file should be part of the repository in the templates directory.[/bold yellow]")
            return # Exit if Dockerfile template is missing
        console.print(f"[bold green]Using Dockerfile template: {dockerfile_template}[/bold green]")

        # Generate docker-compose.yml with ports from SERVICE_PORTS
        docker_compose_copied = copy_docker_compose_template() # Call the simplified function
        if not docker_compose_copied:
            console.print("[bold red]ERROR: Failed to copy docker-compose template.[/bold red]")
            return # Exit if docker-compose copy fails

        console.print("[bold green]docker-compose.yml template copied and configured![/bold green]") # Add this message here

        # Final Docker message block
        console.print("[bold green]Docker mode enabled:[/bold green]")
        console.print("[bold green]- Dockerfiles have been generated for all repositories[/bold green]")
        console.print("[bold green]- Configuration URLs set for Docker networking[/bold green]")
        console.print("[bold green]- docker-compose.yml has been copied to project root[/bold green]")
        console.print("[bold green]- Ports assigned: 8080 (coordinator), 8001 (GitHub), 8002 (HackMD), 8011/8012 (processors)[/bold green]")

        # # Check if any global.env file exists and has been validated
        # if global_env.exists():
        #     with open(global_env, 'r') as env_file:
        #         env_content = env_file.read()
        #         if "GITHUB_TOKEN=" in env_content or "HACKMD_API_TOKEN=" in env_content or "GITHUB_WEBHOOK_SECRET=" in env_content:
        #             console.print("[bold red]⚠️  WARNING: One or more environment variables in global.env are not set![/bold red]")
        #             console.print("[bold red]The system will not work correctly without proper API tokens.[/bold red]")
        #             console.print("[bold yellow]- You can now run 'docker-compose up' to start the containers, but you MUST edit global.env first[/bold yellow]\n")
        #         else:
        #             console.print("[bold green]- You can now run 'docker-compose up' to start the containers[/bold green]\n")
        # else:
        #     console.print("[bold red]⚠️  WARNING: global.env file is missing! The system will not work correctly.[/bold red]")
        #     console.print("[bold yellow]- Create a global.env file with your API tokens before running docker-compose[/bold yellow]\n")

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
    parser.add_argument('--branch', dest='branch', default='demo-1',
                        help='Git branch to checkout for each repository (default: demo-1)')
    args = parser.parse_args()

    main(is_docker=args.is_docker, branch=args.branch)
