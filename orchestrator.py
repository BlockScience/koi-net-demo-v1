#!/usr/bin/env python3
import subprocess
from pathlib import Path
import yaml
from rich.table import Table
from rich.console import Console
import shutil

# ---- USER CONFIG ----
START_PORT = 8000
COORD_URL = "http://127.0.0.1:{}"  # Will be formatted with coordinator port

# Templates for each node type, based on merged_config.yaml
NODE_CONFIGS = {
    "koi-net-coordinator-node": lambda port: {
        "server": {
            "host": "127.0.0.1",
            "port": port,
            "path": "/koi-net"
        },
        "koi_net": {
            "node_name": "coordinator",
            "node_rid": None,
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
            "node_name": "github_sensor",
            "node_rid": "orn:koi-net.node:github_sensor+383246c0-8c58-4331-9809-eb8ba2057204",
            "node_profile": {
                "base_url": f"http://127.0.0.1:{port}/koi-net",
                "node_type": "FULL",
                "provides": {
                    "event": ["orn:github.commit"],
                    "state": ["orn:github.commit"]
                }
            },
            "cache_directory_path": ".koi/cache",
            "event_queues_path": ".koi/github/queues.json",
            "first_contact": COORD_URL.format(START_PORT)
        },
        "identity_directory_path": ".koi/github",
        "env": {
            "github_api_token": "GITHUB_API_TOKEN",
            "github_webhook_secret": "GITHUB_WEBHOOK_SECRET"
        },
        "github": {
            "monitored_repos": [{"name": "BlockScience/koi-net"}],
            "backfill_interval_seconds": 600,
            "backfill_on_startup": True
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
            "node_rid": "orn:koi-net.node:hackmd-sensor+3ec03836-7843-4bc1-9165-b0ed2f1aa979",
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
        "identity_directory_path": ".koi/hackmd",
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
            "node_profile": {
                "node_type": "FULL",
                "provides": {
                    "event": [],
                    "state": []
                }
            },
            "cache_directory_path": ".koi/processor-github",
            "event_queues_path": ".koi/processor-github/queues.json",
            "first_contact": COORD_URL.format(START_PORT),
            "identity_directory_path": ".koi/processor_github",
            "github_sensor_rid": ""
        }
    },
    "koi-net-processor-hackmd-node": lambda port: {
        "server": {
            "host": "127.0.0.1",
            "port": port,
            "path": "/koi-net"
        },
        "koi_net": {
            "node_name": "processor_hackmd",
            "node_profile": {
                "node_type": "FULL",
                "provides": {
                    "event": [],
                    "state": []
                }
            },
            "cache_directory_path": ".koi/processor-hackmd",
            "event_queues_path": ".koi/processor-hackmd/queues.json",
            "first_contact": COORD_URL.format(START_PORT),
            "identity_directory_path": ".koi/processor_hackmd",
            "hackmd_sensor_rid": ""
        }
    }
}

REPO_ORDER = [
    "koi-net-coordinator-node",
    "koi-net-hackmd-sensor-node",
    "koi-net-github-sensor-node",
    "koi-net-processor-gh-node",
    "koi-net-processor-hackmd-node"
]

# ---------------------
def run(cmd, cwd=None):
    print(f"$ {' '.join(cmd)}" + (f" (in {cwd})" if cwd else ""))
    subprocess.run(cmd, check=True, cwd=cwd)

def clone_repo(repo):
    if not Path(repo).exists():
        run(["git", "clone", f"https://github.com/BlockScience/{repo}", repo])
    else:
        print(f"Repo {repo} already exists, skipping clone.")
    return repo

def write_full_config(repo_dir, config_dict):
    config_path = Path(repo_dir) / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    print(f"Wrote {config_path}")
    return config_path

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
        print(f"Creating venv with 'python3 -m venv' in {venv_path}...")
        try:
            run(["python3", "-m", "venv", str(venv_path.name)], cwd=str(repo_path))
        except subprocess.CalledProcessError as e_venv:
            print(f"[bold red]Error: 'python3 -m venv' command failed. Error: {e_venv}[/bold red]")
            print(f"[bold yellow]Ensure the 'python3' command can create virtual environments.[/bold yellow]")
            return # Stop if venv creation fails
        except FileNotFoundError:
            print(f"[bold red]Error: 'python3' command not found. Please install Python 3.[/bold red]")
            return
    else:
        print(f"Venv already exists in {venv_path}, skipping creation.")

    # 2. Find Python and Pip in the venv
    venv_python_executable = _get_exec_path(venv_path, "python") or _get_exec_path(venv_path, "python3")
    venv_pip_executable = _get_exec_path(venv_path, "pip") or _get_exec_path(venv_path, "pip3")
    if not venv_python_executable or not venv_pip_executable:
        print(f"[bold red]Error: Python or pip not found in venv {venv_path} after creation attempt.[/bold red]")
        print(f"DEBUG: venv_path={venv_path.resolve()}")
        print(f"DEBUG: repo_path={repo_path.resolve()}")
        print(f"DEBUG: Contents of venv_path: {list(venv_path.iterdir()) if venv_path.exists() else 'DOES NOT EXIST'}")
        bin_dir = venv_path / 'bin'
        print(f"DEBUG: Contents of bin_dir: {list(bin_dir.iterdir()) if bin_dir.exists() else 'DOES NOT EXIST'}")
        if venv_path.exists():
            print(f"[bold yellow]Attempting to remove venv at {venv_path} for a fresh start next time...[/bold yellow]")
            try:
                shutil.rmtree(venv_path)
                print(f"[bold green]Successfully removed {venv_path}. Please re-run the script.[/bold green]")
            except Exception as e_rm:
                print(f"[bold red]Failed to remove {venv_path}: {e_rm}. Please remove it manually.[/bold red]")
        return

    # 3. Install requirements using the venv's pip
    if requirements_path.exists():
        print(f"Installing requirements from {requirements_path} into {venv_path} using {venv_pip_executable} install...")
        try:
            run([
                str(venv_pip_executable), "install",
                "-r", str(requirements_path.name)
            ], cwd=str(repo_path))
        except subprocess.CalledProcessError as e_install:
            print(f"[bold red]Error during 'pip install': {e_install}. Pip executable: {venv_pip_executable}[/bold red]")
            if hasattr(e_install, 'stderr') and e_install.stderr and ("Library not loaded" in e_install.stderr.decode(errors='ignore') or "dyld" in e_install.stderr.decode(errors='ignore')):
                 print("[bold yellow]This looks like a broken Python/Pip interpreter in the venv (dylid issue).[/bold yellow]")
                 if venv_path.exists():
                    print(f"[bold yellow]Attempting to remove broken venv at {venv_path} for a fresh start next time...[/bold yellow]")
                    try:
                        shutil.rmtree(venv_path)
                        print(f"[bold green]Successfully removed {venv_path}. Please re-run the script.[/bold green]")
                    except Exception as e_rm:
                        print(f"[bold red]Failed to remove {venv_path}: {e_rm}. Please remove it manually.[/bold red]")
            else:
                 print("[bold yellow]Consider manually deleting the .venv directory in this repository and re-running the script.[/bold yellow]")            
            return # Stop processing this repo if install fails
    else:
        print(f"No requirements.txt in {repo_dir_str}, skipping install.")

def main():
    port = START_PORT
    # Determine coordinator port (in case order changes)
    coordinator_index = REPO_ORDER.index("koi-net-coordinator-node")
    coordinator_port = START_PORT + coordinator_index
    coord_url = f"http://127.0.0.1:{coordinator_port}/koi-net"
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
        config_dict = NODE_CONFIGS[repo](port)
        if repo == "koi-net-coordinator-node":
            config_dict["koi_net"]["first_contact"] = ""
        else:
            config_dict["koi_net"]["first_contact"] = coord_url
        node_name = config_dict["koi_net"]["node_name"]
        node_type = config_dict["koi_net"]["node_profile"]["node_type"]
        cache_path = config_dict["koi_net"]["cache_directory_path"]
        first_contact = config_dict["koi_net"].get("first_contact", "")
        config_path = write_full_config(repo_dir, config_dict)
        install_requirements(repo_dir)
        table.add_row(
            repo_dir,
            node_name,
            str(port),
            node_type,
            cache_path,
            str(config_path),
            first_contact or "-"
        )
        port += 1
    print("\nAll repos cloned, config.yaml written, and requirements installed with standard pip/venv.\n")
    console = Console()
    console.print(table)
    print("\n[bold yellow]Each repository now has its own virtual environment in its '.venv/' directory.[/bold yellow]")
    print("[bold yellow]To manually run a node script, first 'cd' into its repository directory, then activate its venv:[/bold yellow]")
    print("[bold yellow]source .venv/bin/activate[/bold yellow]\n")
    
    
if __name__ == "__main__":
    main()
    
    
    
       