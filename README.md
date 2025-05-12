# KOI-net Demo

This document provides a straightforward guide for setting up and running the KOI-net distributed system.

## System Overview

KOI-net consists of the following components:
- Coordinator node (central point for node discovery)
- GitHub Sensor node (monitors GitHub repositories)
- HackMD Sensor node (monitors HackMD notes)
- GitHub Processor node (processes GitHub events)
- HackMD Processor node (processes HackMD events)

## Prerequisites

- Python 3.12+
- Docker and Docker Compose (for Docker mode)
- Git

## Setup Options

### Option 1: Local Development Setup

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
make processor-gh

# Run the HackMD processor node (run in a separate terminal)
make processor-hackmd
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

The system uses the following port mapping:

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
docker compose exec processor-github python -m cli list-repos
```

#### View GitHub Event Summary
```bash
docker compose exec processor-github python -m cli summary
```

#### Show Events for a Repository
```bash
docker compose exec processor-github python -m cli show-events BlockScience/koi-net
```

#### Add a New Repository to Track
```bash
docker compose exec processor-github python -m cli add-repo BlockScience/koios
```

#### View Details for a Specific Event
```bash
docker compose exec processor-github python -m cli event-details <event_rid>
```

### HackMD CLI Operations

#### List All Notes
```bash
make demo-hackmd-cli
```
or directly:
```bash
docker compose exec processor-hackmd python -m cli list
```

#### Display Note Statistics
```bash
docker compose exec processor-hackmd python -m cli stats
```

#### View a Specific Note
```bash
docker compose exec processor-hackmd python -m cli show C1xso4C8SH-ZzDaloTq4Uw
```

#### Show Note History
```bash
docker compose exec processor-hackmd python -m cli history C1xso4C8SH-ZzDaloTq4Uw
```

#### Search Notes by Content
```bash
docker compose exec processor-hackmd python -m cli search "koi-net"
```

#### Filter Notes by Conditions
```bash
docker compose exec processor-hackmd python -m cli list --limit 10 --search koi
```

### CLI Help

To see all available CLI commands and examples:
```bash
make cli-help
```

For detailed help on specific commands:
```bash
docker compose exec processor-github python -m cli --help
docker compose exec processor-github python -m cli show-events --help
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
```

## Troubleshooting

If CLI commands return with "No repositories found" or "No notes found":
1. Ensure all services are healthy: `make docker-status`
2. Check service logs for errors: `make docker-logs`
3. Verify your API tokens in `global.env` are correct and have proper permissions
4. Wait a bit longer for initial data synchronization

### Common Issues

- **Authentication errors**: Check your API tokens in `global.env`. The GitHub token needs `repo` and `read:org` scopes.
- **Missing repositories**: Use `docker compose exec processor-github python -m cli add-repo owner/repo` to manually add repositories.
- **No HackMD notes**: Ensure your HackMD API token has access to the team workspace.

## Implementation Details

The system is orchestrated through three main components:

1. `orchestrator.py`: Handles repository cloning, configuration generation, and Docker setup
2. `Makefile`: Provides command targets for common operations
3. `docker-compose.yml`: (Generated) Defines service configuration for Docker deployment

Each node runs as an independent service, connecting to the coordinator for network discovery.

## Docker Technical Details

- Uses Python 3.12 slim image as base
- Installs dependencies from requirements.txt using standard pip (not editable mode)
- Configures each service with appropriate networking setup
- Uses healthchecks to ensure services are properly initialized
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

- GitHub event database: `/app/.koi/processor-github/index.db` in the processor-github container
- HackMD note database: `/app/.koi/index_db/index.db` in the processor-hackmd container