# KOI-net Demo

## 1. Overview

This document outlines the design and user workflow of the KOI-net demo platform, focusing on the orchestration layer that facilitates setting up and running a distributed network of nodes for processing GitHub and HackMD data. The core purpose is to demonstrate a modular, event-driven microservice architecture.

Key features include:
*   Automated repository cloning and setup
*   Configuration generation for different deployment contexts (local, Docker)
*   Centralized command-line interface (`cli.py`) for common tasks
*   Decoupled nodes communicating via a Coordinator

The demo specifically highlights the flow of information from external sources (GitHub, HackMD) through dedicated sensor nodes, via a coordinator, to processor nodes where data is stored and made accessible via command-line tools. The orchestrator simplifies the deployment and interaction with this distributed system.

## System Overview

KOI-net consists of the following components:
- Coordinator node (central point for node discovery)
- GitHub Sensor node (monitors GitHub repositories)
- HackMD Sensor node (monitors HackMD notes)
- GitHub Processor node (processes GitHub events)
- HackMD Processor node (processes HackMD events)

## Prerequisites

- Python 3.12+
- Docker and Docker Compose v2+ (for Docker mode)
- Git
- Make (or see alternatives in the Implementation Details section)

## Setup Options

### Option 1: Local Development Setup

#### Option A: Using Make

```bash
# Clone repositories and generate configurations
make setup-all

# Run the coordinator node (run in a separate terminal)
make coordinator

# Run the GitHub sensor node (run in a separate terminal)
make github-sensor

# Run the HackMD sensor node (run in a separate terminal)
make hackmd-sensor

# Run the GitHub processor node (run in a separate terminal)
make github-processor

# Run the HackMD processor node (run in a separate terminal)
make hackmd-processor

# Run the HackMD processor node CLI tool to inspect the HackMD events (run in a separate terminal)
make hackmd-processor-cli

# Run the GitHub processor node CLI tool to inspect the GitHub events (run in a separate terminal)
make github-processor-cli
```

#### Option B: Using the command-line tool

The `cli.py` script provides a more direct way to run commands without using Make.

```bash
# Clone repositories and generate configurations
python cli.py setup-all

# Run the coordinator node (run in a separate terminal)
python cli.py coordinator

# Run the GitHub sensor node (run in a separate terminal)
python cli.py github-sensor

# Run the HackMD sensor node (run in a separate terminal)
python cli.py hackmd-sensor

# Run the GitHub processor node (run in a separate terminal)
python cli.py github-processor

# Run the HackMD processor node (run in a separate terminal)
python cli.py hackmd-processor

# Run the HackMD processor CLI (shorter version of hackmd-processor-cli)
python cli.py hackmd-cli

# Run the GitHub processor CLI (shorter version of github-processor-cli)
python cli.py github-cli

# Show available commands
python cli.py --help
```

### Option 2: Docker Setup (Recommended)

```bash
# All-in-one command to set up, build, and start KOI-net
make docker-demo
```

This will:
1. Clean the environment
2. Generate Docker configurations
3. Build all Docker containers
4. Start all services
5. Wait for all services to be healthy
6. Display system status using CLI tools

#### Setting up API Tokens

Before running the services, you need to add your API tokens to the `global.env` file created in the project root:

```bash
# Edit the global.env file
nano global.env
```

Add the following environment variables with your actual tokens:

```
# GitHub Personal Access Token
GITHUB_TOKEN=your_github_token_here

# GitHub Webhook Secret (any random string you create)
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# HackMD API Token
HACKMD_API_TOKEN=your_hackmd_token_here
```
These tokens are required for the sensors to access GitHub repositories and HackMD notes.

Alternatively, you can perform each step manually:

```bash
# Generate Docker configurations
make demo-orchestrator

# Build and start all services in detached mode
docker compose up -d

# Stop all services
make down
```

## Port Configuration

The system uses the following port mapping for both local and Docker modes:

```
- Coordinator: 8080
- GitHub Sensor: 8001
- HackMD Sensor: 8002
- GitHub Processor: 8011
- HackMD Processor: 8012
```

To see current port assignments:
```bash
make show-ports
```

## CLI Tools and Data Exploration

KOI-net includes powerful CLI tools for exploring GitHub repositories and HackMD notes in the system.

### GitHub CLI Operations

#### List Tracked Repositories
```bash
make demo-github-cli
```
or directly:
```bash
docker compose exec github-processor python -m cli list-repos
```

#### View GitHub Event Summary
```bash
docker compose exec github-processor python -m cli summary
```

#### Show Events for a Repository
```bash
docker compose exec github-processor python -m cli show-events BlockScience/koi-net
```

#### Add a New Repository to Track
```bash
docker compose exec github-processor python -m cli add-repo BlockScience/koios
```

#### View Details for a Specific Event
```bash
docker compose exec github-processor python -m cli event-details <event_rid>
```

### HackMD CLI Operations

#### List All Notes
```bash
make demo-hackmd-cli
```
or directly:
```bash
docker compose exec hackmd-processor python -m cli list
```

#### Display Note Statistics
```bash
docker compose exec hackmd-processor python -m cli stats
```

#### View a Specific Note
```bash
docker compose exec hackmd-processor python -m cli show C1xso4C8SH-ZzDaloTq4Uw
```

#### Show Note History
```bash
docker compose exec hackmd-processor python -m cli history C1xso4C8SH-ZzDaloTq4Uw
```

#### Search Notes by Content
```bash
docker compose exec hackmd-processor python -m cli search "koi-net"
```

#### Filter Notes by Conditions
```bash
docker compose exec hackmd-processor python -m cli list --limit 10 --search koi
```

### CLI Help

To see all available CLI commands and examples:
```bash
make cli-help
```

For detailed help on specific commands:
```bash
docker compose exec github-processor python -m cli --help
docker compose exec github-processor python -m cli show-events --help
```

## System Management

### Monitor Service Status
```bash
make docker-status
```

### View Service Logs
```bash
make docker-logs
```

### Interactive Resource Monitoring
```bash
make docker-monitor
```

### Rebuild Docker Configuration
```bash
make docker-regenerate
```

## Working with Individual Services

### Run services individually in Docker:

```bash
# Start only the coordinator
make demo-coordinator

# Start only the GitHub sensor
make demo-github-sensor

# Start only the HackMD sensor
make demo-hackmd-sensor

# Start only the GitHub processor
make demo-github-processor

# Start only the HackMD processor
make demo-hackmd-processor
```

### Rebuild Docker images:

```bash
# Rebuild all Docker images (no cache)
make docker-rebuild
```

## Environment Management

```bash
# Clean up all environments, caches, and build artifacts
make clean

# Clean only cache directories
make clean-cache

# Clean only virtual environments
make clean-venv

# Kill processes using KOI-net ports (8080, 8001, 8002, 8011, 8012)
make kill-ports
```

## Troubleshooting

If CLI commands return with "No repositories found" or "No notes found":
1. Ensure all services are healthy: `make docker-status`
2. Check service logs for errors: `make docker-logs`
3. Verify your API tokens in `global.env` are correct and have proper permissions
4. Wait a bit longer for initial data synchronization

### Common Issues

- **Authentication errors**: Check your API tokens in `global.env`. The GitHub token needs `repo` and `read:org` scopes.
- **Missing repositories**: Use `docker compose exec github-processor python -m cli add-repo owner/repo` to manually add repositories.
- **No HackMD notes**: Ensure your HackMD API token has access to the team workspace.
- **Health check failures**: Some services may fail health checks initially. Check logs with `docker logs koi-nets-demo-v1-coordinator-1` or use `make docker-logs` to troubleshoot.
- **"Unknown filter health" error**: If you see this error, your Docker Compose version might not support filtering by health status. Update Docker Compose or use `docker ps` to check container health status directly.
- **Port already in use**: If you see errors about ports being in use, run `make kill-ports` to terminate processes using the KOI-net ports.

## Implementation Details

The system is orchestrated through three main components:

1. `orchestrator.py`: Handles repository cloning, configuration generation, and Docker setup
2. `Makefile`: Provides command targets for common operations
3. `docker-compose.yml`: (Generated) Defines service configuration for Docker deployment

Each node runs as an independent service, connecting to the coordinator for network discovery.

### Alternative to Make

#### Option 1: Using the koin Command Line Tool

The project includes a convenient command line tool (`koin`) that provides all the functionality of the Makefile:

```bash
# Make the script executable (only needs to be done once)
chmod +x koi-nets-demo-v2/koin

# Generate Docker configurations
python cli.py docker-setup

# Start all services
python cli.py docker-up

# Check status
python cli.py docker-status

# Show all CLI tools available
python cli.py --help

# Stop all services
python cli.py docker-down
```

#### Option 2: Direct Docker Commands

You can also run the Docker commands directly:

```bash
# Generate configs with Docker support
python orchestrator.py --docker

# Build and start services
docker compose up -d

# Check status
docker ps

# Stop services
docker compose down
```

## Docker Technical Details

- Uses Python 3.12 slim image as base
- Installs dependencies from requirements.txt using standard pip (not editable mode)
- Configures each service with appropriate networking setup
- Uses healthchecks with path `/koi-net/health` to ensure services are properly initialized
- Preserves `global.env` file between runs to maintain API tokens
- Regenerates all other configuration files automatically
- Smart fallback to standard package installation if requirements.txt is not found

### Environment Variables

The system uses the following environment variables:

| Variable | Purpose | Required by |
|----------|---------|-------------|
| `GITHUB_TOKEN` | GitHub Personal Access Token for API access | GitHub Sensor, GitHub Processor |
| `GITHUB_WEBHOOK_SECRET` | Secret for validating GitHub webhooks | GitHub Sensor |
| `HACKMD_API_TOKEN` | HackMD API token for accessing notes | HackMD Sensor, HackMD Processor |

## Database Locations

- GitHub event database: `/app/.koi/github-processor/index.db` in the github-processor container
- HackMD note database: `/app/.koi/index_db/index.db` in the hackmd-processor container
