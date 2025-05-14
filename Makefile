# Define all phony targets (targets that don't represent files)
.PHONY: clean clean-build clean-venv clean-cache setup install setup-all orchestrate \
        coordinator github-sensor hackmd-sensor github-processor hackmd-processor \
        run-all demo-orchestrator demo-coordinator demo-github-sensor demo-hackmd-sensor \
        demo-github-processor demo-hackmd-processor demo-cli docker-clean docker-rebuild up down docker-demo \
        docker-regenerate show-ports wait-for-service demo-github-cli demo-hackmd-cli demo-show-services \
        docker-status docker-logs docker-monitor cli-help clean-docker-containers kill-ports check-env

VENV_DIR ?= .venv
PYTHON_EXECUTABLE_FOR_VENV_CREATION ?= python3


# Setup targets
setup: $(VENV_DIR)/.pip_ready
	@echo "Root virtual environment is ready at $(VENV_DIR)"
	@echo "To activate, run: source $(VENV_DIR)/bin/activate"

install: $(VENV_DIR)/.installed_root_requirements
	@echo "Root requirements from requirements.txt are installed in $(VENV_DIR)."
	@echo "Installing/checking koi-net package into $(VENV_DIR)..."
	. $(VENV_DIR)/bin/activate && $(VENV_DIR)/bin/pip install koi-net
	@echo "koi-net installation/check complete."

# --- Helper targets for venv and root requirements ---
# Marker file indicating venv is created and base pip is ready
$(VENV_DIR)/.pip_ready:
	@echo "Creating root virtual environment in $(VENV_DIR) using $(PYTHON_EXECUTABLE_FOR_VENV_CREATION)..."
	$(PYTHON_EXECUTABLE_FOR_VENV_CREATION) -m venv $(VENV_DIR)
	@echo "Ensuring pip is installed and up-to-date in $(VENV_DIR)..."
	. $(VENV_DIR)/bin/activate && $(VENV_DIR)/bin/python3 -m ensurepip --upgrade --default-pip
	. $(VENV_DIR)/bin/activate && $(VENV_DIR)/bin/pip install --upgrade pip
	@touch $@

# Marker file indicating requirements.txt are installed
$(VENV_DIR)/.installed_root_requirements: $(VENV_DIR)/.pip_ready requirements.txt
	@echo "Installing root requirements from requirements.txt into $(VENV_DIR)..."
	. $(VENV_DIR)/bin/activate && $(VENV_DIR)/bin/pip install -r requirements.txt
	@touch $@

# --- End of modified/added section for setup and install ---

setup-all: clean install
	@echo "Setting up all node repositories..."
	$(VENV_DIR)/bin/python3 orchestrator.py

clean:
	@echo "Starting full cleanup..."
	@$(MAKE) clean-cache
	@$(MAKE) clean-venv
	@$(MAKE) clean-build
	@$(MAKE) clean-docker-containers
	@echo "Clean complete."

# Cleaning targets
clean-build:
	@echo "Removing build artifacts..."
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name 'dist' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name 'build' -exec rm -rf {} + 2>/dev/null || true
	@echo "Build artifacts removed."

clean-venv:
	@echo "Removing virtual environments..."
	@rm -rf .venv || true
	@find . -name ".venv" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Virtual environments removed."

clean-cache:
	@echo "Removing problematic files from cache directories (e.g., .DS_Store)..."
	@find . -name ".DS_Store" -type f -exec rm -f {} + 2>/dev/null || true
	@echo "Removing cache directories and files..."
	@find . -name ".koi" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".rid_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "event_queues.json" -type f -exec rm -f {} + 2>/dev/null || true
	@find . -name "config.yaml" -type f -exec rm -f {} + 2>/dev/null || true
	@find . -name "Dockerfile" -type f -exec rm -f {} + 2>/dev/null || true
	@echo "Cache, config.yaml files, and Dockerfiles removed."
	@echo "NOTE: global.env file is preserved to maintain your API tokens."

# Orchestration target
orchestrator: check-env install
	.venv/bin/python3 orchestrator.py

# Individual node runners
coordinator:
	@echo "Running Coordinator Node..."
	cd koi-net-coordinator-node && .venv/bin/python3 -m coordinator_node

github-sensor: check-env
	@echo "Running Github Sensor Node..."
	cd koi-net-github-sensor-node && .venv/bin/python3 -m github_sensor_node

hackmd-sensor: check-env
	@echo "Running HackMD Sensor Node..."
	rm -rf koi-net-hackmd-sensor-node/node.sensor.log
	cd koi-net-hackmd-sensor-node && .venv/bin/python3 -m hackmd_sensor_node

github-processor: check-env
	@echo "Running GitHub Processor Node..."
	cd koi-net-github-processor-node && .venv/bin/python3 -m github_processor_node

hackmd-processor: check-env
	@echo "Running HackMD Processor Node..."
	rm -rf koi-net-hackmd-processor-node/node.proc.log
	cd koi-net-hackmd-processor-node && .venv/bin/python3 -m hackmd_processor_node

hackmd-processor-cli: check-env
	@echo "Running HackMD Processor Node CLI..."
	cd koi-net-hackmd-processor-node && .venv/bin/python3 -m cli list

github-processor-cli: check-env
	@echo "Running GitHub Processor Node CLI..."
	cd koi-net-github-processor-node && .venv/bin/python3 -m cli list-repos
# Run all nodes in separate terminals
run-all:
	@echo "You must run each node in a separate terminal:"
	@echo "Terminal 1: make coordinator"
	@echo "Terminal 2: make github-sensor"
	@echo "Terminal 3: make hackmd-sensor"
	@echo "Terminal 4: make github-processor"
	@echo "Terminal 5: make hackmd-processor"
	@echo "\nOr use Docker mode: make docker-demo"

demo-orchestrator:
	@echo "Starting Orchestrator via Docker Compose..."
	.venv/bin/python3 orchestrator.py --docker
	@echo "Docker configurations generated. You can now run 'make up' to start all services."
	@echo "IMPORTANT: Make sure to add your API tokens to global.env before starting services!"
	@$(MAKE) check-env || true
	@$(MAKE) show-ports

# Docker commands
demo-coordinator:
	@echo "Starting Coordinator via Docker Compose..."
	docker compose build coordinator
	docker compose up -d coordinator
	@echo "Coordinator started on port 8080"

demo-github-sensor:
	@echo "Starting GitHub sensor via Docker Compose..."
	docker compose build github-sensor
	docker compose up -d github-sensor
	@echo "GitHub sensor started on port 8001"

demo-hackmd-sensor:
	@echo "Starting HackMD sensor via Docker Compose..."
	docker compose build hackmd-sensor
	docker compose up -d hackmd-sensor
	@echo "HackMD sensor started on port 8002"

demo-hackmd-processor:
	@echo "Starting HackMD processor via Docker Compose..."
	docker compose build hackmd-processor
	docker compose up -d hackmd-processor
	@echo "HackMD processor started on port 8012"

demo-github-processor:
	@echo "Starting GitHub processor via Docker Compose..."
	docker compose build github-processor
	docker compose up -d github-processor
	@echo "GitHub processor started on port 8011"

demo-cli:
	@echo "Starting HackMD CLI via Docker Compose..."
	docker compose build --no-cache hackmd-cli
	docker compose up -d demo-cli

docker-clean:
	@echo "Cleaning up all Docker containers and images..."
	docker compose down --rmi all
	@echo "Docker cleanup complete."

docker-rebuild:
	@echo "Rebuilding Docker images with no cache..."
	docker compose build --no-cache
	@echo "Starting Docker services..."
	@$(MAKE) check-env || true
	docker compose up -d
	@echo "Services started with the standard ports:"
	@$(MAKE) show-ports

up:
	@echo "Starting Docker services..."
	@$(MAKE) check-env || true
	docker compose up
	@echo "Services running on ports defined in orchestrator.py SERVICE_PORTS"

down:
	@echo "Stopping Docker services..."
	docker compose down

clean-docker-containers:
	@echo "Stopping and removing Docker containers related to KOI-net..."
	-docker compose down 2>/dev/null || true
	-docker rm -f $$(docker ps -a --filter "name=koi-nets-demo-v1" -q) 2>/dev/null || true
	@echo "Docker containers cleaned."

# Target to show service status after startup
demo-show-services:
	@echo "=== GitHub Repository Status ==="
	@cd koi-net-github-processor-node 2>/dev/null && .venv/bin/python3 -m cli list-repos 2>/dev/null || echo "GitHub processor not initialized yet"
	@echo "\n=== HackMD Notes Status ==="
	@cd koi-net-hackmd-processor-node 2>/dev/null && .venv/bin/python3 -m cli list 2>/dev/null || echo "HackMD processor not initialized yet"

# Individual demo CLI commands for each node type

# Docker CLI demonstration targets
demo-github-cli:
	@echo "Running GitHub CLI in Docker..."
	docker compose exec github-processor python3 -m cli list-repos
	@echo "\nFor more commands try:"
	@echo "docker compose exec github-processor python3 -m cli summary"
	@echo "docker compose exec github-processor python3 -m cli show-events BlockScience/koi-net"
	@echo "docker compose exec github-processor python3 -m cli event-details <event_rid>"
	@echo "docker compose exec github-processor python3 -m cli add-repo BlockScience/koios"

demo-hackmd-cli:
	@echo "Running HackMD CLI in Docker..."
	docker compose exec hackmd-processor python3 -m cli list
	@echo "\nFor more commands try:"
	@echo "docker compose exec hackmd-processor python3 -m cli stats"
	@echo "docker compose exec hackmd-processor python3 -m cli search koi-net"
	@echo "docker compose exec hackmd-processor python3 -m cli show C1xso4C8SH-ZzDaloTq4Uw"
	@echo "docker compose exec hackmd-processor python3 -m cli history C1xso4C8SH-ZzDaloTq4Uw"
	@echo "docker compose exec hackmd-processor python3 -m cli list --limit 10 --search koi"

# Docker monitoring commands
docker-status:
	@echo "========== KOI-NET SERVICES STATUS =========="
	@docker compose ps
	@echo "\n========== HEALTH CHECKS =========="
	@for svc in coordinator github-sensor hackmd-sensor github-processor hackmd-processor ; do \
		echo "$$svc: $$(docker compose ps --services --filter "health=healthy" | grep -q $$svc && echo "✅ HEALTHY" || echo "❌ UNHEALTHY")"; \
	done

docker-logs:
	@echo "Viewing logs from all services (press Ctrl+C to exit)..."
	@docker compose logs -f

docker-monitor:
	@echo "Starting interactive monitoring dashboard (press Ctrl+C to exit)..."
	@watch -n 5 "docker compose ps && echo '' && docker stats --no-stream"

# Show all available CLI commands and examples
cli-help:
	@echo "========== KOI-NET CLI COMMANDS =========="
	@echo "\n=== GitHub CLI Commands ==="
	@echo "List all tracked repos:           docker compose exec github-processor python3 -m cli list-repos"
	@echo "Show repository events:           docker compose exec github-processor python3 -m cli show-events BlockScience/koi-net [--limit 20]"
	@echo "View event details:               docker compose exec github-processor python3 -m cli event-details <event_rid>"
	@echo "Add a new repository:             docker compose exec github-processor python3 -m cli add-repo BlockScience/koios"
	@echo "Show events summary:              docker compose exec github-processor python3 -m cli summary"
	@echo "\n=== HackMD CLI Commands ==="
	@echo "List all notes:                   docker compose exec hackmd-processor python3 -m cli list [--limit 20] [--offset 0] [--search query]"
	@echo "Show note details:                docker compose exec hackmd-processor python3 -m cli show C1xso4C8SH-ZzDaloTq4Uw"
	@echo "Show note history:                docker compose exec hackmd-processor python3 -m cli history C1xso4C8SH-ZzDaloTq4Uw [--limit 20]"
	@echo "Search notes by content:          docker compose exec hackmd-processor python3 -m cli search 'koi-net' [--limit 20]"
	@echo "Show note statistics:             docker compose exec hackmd-processor python3 -m cli stats"
	@echo "\n(To get help on the CLI itself, append '--help' to any command)"

# Kill processes using KOI-net ports
kill-ports:
	@echo "Killing processes using KOI-net ports..."
	-@lsof -ti:8080 | xargs kill -9 2>/dev/null || echo "No process on port 8080"
	-@lsof -ti:8001 | xargs kill -9 2>/dev/null || echo "No process on port 8001"
	-@lsof -ti:8002 | xargs kill -9 2>/dev/null || echo "No process on port 8002"
	-@lsof -ti:8011 | xargs kill -9 2>/dev/null || echo "No process on port 8011"
	-@lsof -ti:8012 | xargs kill -9 2>/dev/null || echo "No process on port 8012"
	@echo "All processes on KOI-net ports have been terminated."


# Wait with timeout for a service to be healthy
wait-for-service:
	@timeout=180; \
	echo "Waiting for $(SERVICE) (timeout: $${timeout}s)..."; \
	start_time=$$(date +%s); \
	container_name="koi-nets-demo-v1-$(SERVICE)-1"; \
	until docker ps --filter "name=$$container_name" --format "{{.Status}}" | grep -q "healthy"; do \
		status=$$(docker ps --filter "name=$$container_name" --format "{{.Status}}" || echo "Unknown"); \
		current_time=$$(date +%s); \
		elapsed_time=$$((current_time - start_time)); \
		if [ $$elapsed_time -ge $$timeout ]; then \
			echo "Timeout waiting for $(SERVICE) after $${timeout}s"; \
			echo "Current status: $$status"; \
			docker logs $$container_name --tail 20; \
			exit 1; \
		fi; \
		sleep 5; \
		echo "Still waiting for $(SERVICE) ($${elapsed_time}s elapsed)... Current status: $$status"; \
	done; \
	echo "$(SERVICE) is healthy after $$(($$(date +%s) - start_time))s!"

docker-regenerate:
	@echo "Regenerating Docker configuration files..."
	@echo "Cleaning previous configuration files first..."
	@find . -name "config.yaml" -type f -exec rm -f {} + 2>/dev/null || true
	@find . -name "Dockerfile" -type f -exec rm -f {} + 2>/dev/null || true
	@rm -f docker-compose.yml 2>/dev/null || true
	@echo "Preserving global.env file with API tokens..."
	@$(MAKE) demo-orchestrator
	@echo "Rebuilding Docker images with new configuration..."
	@$(MAKE) docker-rebuild
	@echo "Docker regeneration complete. Use 'make up' to start services."

show-ports:
	@echo "Port mappings for all modes (Docker and local):"
	@echo "- Coordinator: 8080"
	@echo "- GitHub Sensor: 8001"
	@echo "- HackMD Sensor: 8002"
	@echo "- GitHub Processor: 8011"
	@echo "- HackMD Processor: 8012"
	@grep -A 5 "SERVICE_PORTS = {" orchestrator.py || echo "Could not find port definitions in orchestrator.py"

check-env:
	@if [ -f global.env ]; then \
		missing_vars=""; \
		if ! grep -q "GITHUB_TOKEN=.*[^[:space:]]" global.env; then \
			missing_vars="$$missing_vars GITHUB_TOKEN"; \
		fi; \
		if ! grep -q "GITHUB_WEBHOOK_SECRET=.*[^[:space:]]" global.env; then \
			missing_vars="$$missing_vars GITHUB_WEBHOOK_SECRET"; \
		fi; \
		if ! grep -q "HACKMD_API_TOKEN=.*[^[:space:]]" global.env; then \
			missing_vars="$$missing_vars HACKMD_API_TOKEN"; \
		fi; \
		if [ -n "$$missing_vars" ]; then \
			echo "⚠️  [ERROR] The following environment variables are not set in global.env:"; \
			echo "$$missing_vars"; \
			echo ""; \
			echo "Please edit global.env to set your API tokens before continuing."; \
			echo "You can use your favorite text editor:"; \
			echo "    nano global.env"; \
			echo ""; \
			false; \
		else \
			echo "✅ Environment variables validated successfully."; \
		fi; \
	else \
		echo "⚠️  [ERROR] global.env file not found!"; \
		echo "Please run 'make demo-orchestrator' first to generate it."; \
		false; \
	fi

docker-demo: check-env kill-ports install
	@echo "========== STARTING KOI-NET DOCKER WORKFLOW =========="
	@echo "Step 1: Generate Docker configurations..."
	@$(MAKE) demo-orchestrator
	@echo "Step 2: Building all services..."
	docker compose build
	@echo "Step 3: Validating environment variables..."
	@$(MAKE) check-env || true
	@echo "Step 4: Starting all services..."
	docker compose up -d
	@echo "All services are now running with the following ports:"
	@$(MAKE) show-ports
	@echo "\n========== WAITING FOR SERVICES TO BE HEALTHY =========="
	@$(MAKE) wait-for-service SERVICE=coordinator
	@$(MAKE) wait-for-service SERVICE=github-sensor
	@$(MAKE) wait-for-service SERVICE=hackmd-sensor
	@$(MAKE) wait-for-service SERVICE=github-processor
	@$(MAKE) wait-for-service SERVICE=hackmd-processor
	@echo "\n========== ALL SERVICES ARE HEALTHY =========="
	@echo "\n========== SYSTEM STATUS REPORTS =========="
	@echo "\n=== GitHub Repository Status ==="
	-@docker compose exec github-processor python3 -m cli list-repos 2>/dev/null || echo "GitHub processor not initialized yet"
	@echo "\n=== GitHub Events Summary ==="
	-@docker compose exec github-processor python3 -m cli summary 2>/dev/null || echo "GitHub processor not initialized yet"
	@echo "\n=== HackMD Notes Status ==="
	-@docker compose exec hackmd-processor python3 -m cli list 2>/dev/null || echo "HackMD processor not initialized yet"
	@echo "\n=== HackMD Notes Statistics ==="
	-@docker compose exec hackmd-processor python3 -m cli stats 2>/dev/null || echo "HackMD processor not initialized yet"
	@echo "\n========== KOI-NET SYSTEM READY =========="
	@echo "Use 'make down' to stop all services when done."
	@echo "Use 'make demo-github-cli' or 'make demo-hackmd-cli' to run more CLI commands."
	@echo "Use 'make docker-status' to check service health."
	@echo "Use 'make docker-logs' to view service logs."
	@echo "Use 'make docker-monitor' to start an interactive monitoring session."
	@echo "Use 'make cli-help' to see all available CLI commands and examples."
