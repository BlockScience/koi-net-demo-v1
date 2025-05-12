# KOI-net Installation and Quickstart

This guide will help you get started with KOI-net, covering installation and basic usage examples.

## Installation

### Option 1: Install from PyPI

The simplest way to install KOI-net is via pip:

```bash
# Basic installation
pip install koi-net

# With examples dependencies
pip install koi-net[examples]

# With development dependencies
pip install koi-net[dev]
```

### Option 2: Install from Source

To install from source:

```bash
# Clone the repository
git clone https://github.com/BlockScience/koi-net.git
cd koi-net

# Create and activate a virtual environment
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/macOS
source venv/bin/activate

# Install with development dependencies
pip install -e .[dev]

# Or with example dependencies
pip install -e .[examples]
```

## Development Environment Setup

To set up a development environment:

```bash
# Clone the repository
git clone https://github.com/BlockScience/koi-net.git
cd koi-net

# Create and activate a virtual environment
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/macOS
source venv/bin/activate

# Install with development dependencies
pip install -e .[dev]
```

## Quickstart

### Hello World: Partial Node

A partial node is a web client that can communicate with full nodes. Here's a minimal example:

```python
# hello_world_partial.py
from koi_net import NodeInterface
from koi_net.protocol.node import NodeProfile, NodeType
from koi_net.config import NodeConfig, KoiNetConfig
from pydantic import Field
import time
from koi_net.processor.knowledge_object import KnowledgeSource

# Define a configuration for our node
class SimplePartialNodeConfig(NodeConfig):
    koi_net: KoiNetConfig | None = Field(default_factory = lambda:
        KoiNetConfig(
            node_name="hello_world_partial",
            node_profile=NodeProfile(
                node_type=NodeType.PARTIAL
            ),
            cache_directory_path=".hello_partial_cache",
            event_queues_path="hello_partial_event_queues.json",
            first_contact="http://127.0.0.1:8000/koi-net"  # URL of a Full node to connect to
        )
    )

# Create the node
node = NodeInterface(
    config=SimplePartialNodeConfig.load_from_yaml("hello_partial_config.yaml")
)

# Start the node
node.start()

try:
    print("Hello World! Partial node is running.")
    print(f"My RID is: {node.identity.rid}")

    # Main loop - poll for events every 5 seconds
    while True:
        print("Polling neighbors for events...")
        events = node.network.poll_neighbors()

        if events:
            print(f"Received {len(events)} events!")
            for event in events:
                print(f"Processing event: {event.event_type} for {event.rid}")
                node.processor.handle(event=event, source=KnowledgeSource.External)
        else:
            print("No events received.")

        # Process all queued knowledge objects
        node.processor.flush_kobj_queue()

        time.sleep(5)

except KeyboardInterrupt:
    print("Shutting down...")
finally:
    # Always stop the node properly
    node.stop()
```

### Hello World: Full Node

A full node is a web server that can receive requests from other nodes. It requires FastAPI and uvicorn:

```python
# hello_world_full.py
from koi_net import NodeInterface
from koi_net.protocol.node import NodeProfile, NodeProvides, NodeType
from koi_net.config import NodeConfig, KoiNetConfig
from koi_net.processor.knowledge_object import KnowledgeSource
from pydantic import Field
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from koi_net.protocol.api_models import *
from koi_net.protocol.consts import *
from rid_lib.types import KoiNetNode, KoiNetEdge

# Define a configuration for our node
class SimpleFullNodeConfig(NodeConfig):
    koi_net: KoiNetConfig | None = Field(default_factory = lambda:
        KoiNetConfig(
            node_name="hello_world_full",
            node_profile=NodeProfile(
                node_type=NodeType.FULL,
                provides=NodeProvides(
                    event=[KoiNetNode, KoiNetEdge],
                    state=[KoiNetNode, KoiNetEdge]
                )
            ),
            cache_directory_path=".hello_full_cache",
            event_queues_path="hello_full_event_queues.json"
        )
    )

# Create the node with a processor thread
node = NodeInterface(
    config=SimpleFullNodeConfig.load_from_yaml("hello_full_config.yaml"),
    use_kobj_processor_thread=True
)

# Set up the FastAPI app with a lifespan that starts/stops the node
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting node...")
    node.start()
    print(f"Full node started with RID: {node.identity.rid}")
    yield
    print("Stopping node...")
    node.stop()

app = FastAPI(lifespan=lifespan, root_path="/koi-net")

# Define API endpoints
@app.post(BROADCAST_EVENTS_PATH)
def broadcast_events(req: EventsPayload):
    print(f"Received {len(req.events)} events")
    for event in req.events:
        node.processor.handle(event=event, source=KnowledgeSource.External)
    return {}

@app.post(POLL_EVENTS_PATH)
def poll_events(req: PollEvents) -> EventsPayload:
    events = node.network.flush_poll_queue(req.rid)
    print(f"Node {req.rid} polled {len(events)} events")
    return EventsPayload(events=events)

@app.post(FETCH_RIDS_PATH)
def fetch_rids(req: FetchRids) -> RidsPayload:
    return node.network.response_handler.fetch_rids(req)

@app.post(FETCH_MANIFESTS_PATH)
def fetch_manifests(req: FetchManifests) -> ManifestsPayload:
    return node.network.response_handler.fetch_manifests(req)

@app.post(FETCH_BUNDLES_PATH)
def fetch_bundles(req: FetchBundles) -> BundlesPayload:
    return node.network.response_handler.fetch_bundles(req)

# Run the server
if __name__ == "__main__":
    print("Hello World! Starting full node server...")
    uvicorn.run("hello_world_full:app", host="127.0.0.1", port=8000)
```

## Running the Examples

### Step 1: Start the Full Node

```bash
python hello_world_full.py
```

Example output:

```
Hello World! Starting full node server...
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
Starting node...
Full node started with RID: orn:koi-net.node:hello_world_full+a1b2c3d4-e5f6-7890-abcd-1234567890ab
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Step 2: Start the Partial Node

In a separate terminal:

```bash
python hello_world_partial.py
```

Example output:

```
Hello World! Partial node is running.
My RID is: orn:koi-net.node:hello_world_partial+98f7e6d5-c4b3-2109-fedc-ba9876543210
Polling neighbors for events...
No events received.
Polling neighbors for events...
Received 1 events!
Processing event: NEW for orn:koi-net.node:hello_world_full+a1b2c3d4-e5f6-7890-abcd-1234567890ab
```

## What's Next?

After this basic setup, you can:

1. Create custom knowledge handlers
2. Implement more complex knowledge processing logic
3. Set up a network of multiple nodes
4. Build applications on top of the KOI-net infrastructure

For more details, refer to the USER_GUIDE.md and API_REFERENCE.md documents.
