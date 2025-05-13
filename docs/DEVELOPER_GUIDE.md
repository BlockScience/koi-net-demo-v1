# KOI-net Developer Guide

This guide is intended for developers who want to understand, extend, or contribute to the KOI-net project.

## Project Layout

The KOI-net project follows a standard Python package structure:

```
└── blockscience-koi-net/
    ├── README.md                    # Main documentation
    ├── koi-net-protocol-openapi.json # API specification
    ├── LICENSE                      # MIT License
    ├── pyproject.toml               # Project metadata and dependencies
    ├── requirements.txt             # Direct dependencies
    ├── examples/                    # Example applications
    │   ├── basic_coordinator_node.py # Full node example
    │   └── basic_partial_node.py    # Partial node example
    ├── src/                         # Source code
    │   └── koi_net/                 # Main package
    │       ├── __init__.py          # Package exports
    │       ├── config.py            # Configuration classes
    │       ├── core.py              # Core NodeInterface
    │       ├── identity.py          # Node identity
    │       ├── network/             # Network functionality
    │       │   ├── __init__.py
    │       │   ├── graph.py         # Network graph
    │       │   ├── interface.py     # Network interface
    │       │   ├── request_handler.py # Outgoing requests
    │       │   └── response_handler.py # Incoming requests
    │       ├── processor/           # Knowledge processing
    │       │   ├── __init__.py
    │       │   ├── default_handlers.py # Default behavior
    │       │   ├── handler.py       # Handler classes
    │       │   ├── interface.py     # Processor interface
    │       │   └── knowledge_object.py # Knowledge representation
    │       └── protocol/            # Protocol definitions
    │           ├── __init__.py
    │           ├── api_models.py    # API models
    │           ├── consts.py        # Constants
    │           ├── edge.py          # Edge classes
    │           ├── event.py         # Event classes
    │           ├── helpers.py       # Helper functions
    │           └── node.py          # Node classes
    └── .github/
        └── workflows/
            └── publish-to-pypi.yml  # CI/CD for publishing
```

### Key Folders and Files

- **examples/**: Contains example implementations of KOI-net nodes
- **src/koi_net/**: The main package source code
  - **config.py**: Configuration classes for nodes
  - **core.py**: The main NodeInterface implementation
  - **identity.py**: Node identity management
  - **network/**: Network communication components
  - **processor/**: Knowledge processing pipeline
  - **protocol/**: Protocol definitions and API models

## Customizing Knowledge Handlers

The behavior of a KOI-net node is largely defined by its knowledge handlers. You can customize node behavior by creating and registering your own handlers.

### Creating a Custom Handler

Handlers are functions that receive a processor interface and a knowledge object, and can return:

- The modified knowledge object
- None (to pass the original object to the next handler)
- STOP_CHAIN (to stop processing)

Each handler is associated with a specific phase in the processing pipeline:

- `RID` - Initial filtering based on RID
- `Manifest` - Processing with manifest available
- `Bundle` - Decision making with complete bundle
- `Network` - Determine network broadcast targets
- `Final` - Final actions after processing

Here's how to create and register a custom handler:

```python
from koi_net.processor.handler import HandlerType, STOP_CHAIN
from koi_net.processor.knowledge_object import KnowledgeObject, KnowledgeSource
from koi_net.processor import ProcessorInterface
from koi_net.protocol.event import EventType
from rid_lib.types import KoiNetNode
from my_app import MyCustomRID

# Create a handler for a specific RID type
@node.processor.register_handler(
    handler_type=HandlerType.Bundle,
    rid_types=[MyCustomRID],  # Only handle MyCustomRID types
    source=KnowledgeSource.External,  # Only handle external knowledge
    event_types=[EventType.NEW, EventType.UPDATE]  # Only handle NEW and UPDATE events
)
def my_custom_handler(processor: ProcessorInterface, kobj: KnowledgeObject):
    """Custom handler for processing MyCustomRID objects."""
    print(f"Processing {kobj.rid} in custom handler")

    # Validate the contents
    if not is_valid_content(kobj.contents):
        print(f"Invalid content for {kobj.rid}, rejecting")
        return STOP_CHAIN  # Reject this knowledge object

    # Process and update the content if needed
    if needs_enrichment(kobj.contents):
        kobj.contents = enrich_content(kobj.contents)

    # Set the normalized event type to determine cache action
    kobj.normalized_event_type = EventType.NEW

    # Return the modified knowledge object
    return kobj
```

### Registering Handlers

There are two ways to register handlers:

#### 1. Using the Decorator

This is the simplest approach and works well when defining handlers within your application:

```python
@node.processor.register_handler(HandlerType.Network)
def my_network_handler(processor: ProcessorInterface, kobj: KnowledgeObject):
    # Handler logic here
    return kobj
```

#### 2. Creating Portable Handlers

You can create handlers that can be reused across different nodes:

```python
from koi_net.processor.handler import KnowledgeHandler, HandlerType

@KnowledgeHandler.create(HandlerType.Bundle)
def portable_bundle_handler(processor: ProcessorInterface, kobj: KnowledgeObject):
    # Handler logic here
    return kobj

# Later, in application code:
from my_handlers import portable_bundle_handler
node.processor.add_handler(portable_bundle_handler)
```

### Handler Order

Handlers are executed in the order they are registered. If multiple handlers match a knowledge object, they form a processing chain, with each handler receiving the output of the previous one.

To override the default handlers, you can create a node with your own handlers list:

```python
from koi_net import NodeInterface
from koi_net.processor.default_handlers import (
    basic_rid_handler,
    basic_manifest_handler,
    # Skip edge_negotiation_handler
    basic_network_output_filter
)
from my_handlers import my_edge_handler

# Create a node with custom handlers
node = NodeInterface(
    config=my_config,
    handlers=[
        basic_rid_handler,
        basic_manifest_handler,
        my_edge_handler,  # Use our handler instead of the default
        basic_network_output_filter
    ]
)
```

## Running and Extending the Examples

The KOI-net repository includes two example implementations:

- **basic_coordinator_node.py**: A full node that coordinates the network
- **basic_partial_node.py**: A partial node that connects to the coordinator

### Running the Examples

To run the examples, you'll need to install the package with the examples dependencies:

```bash
pip install koi-net[examples]
```

Then you can run each example in a separate terminal:

```bash
# Terminal 1: Start the coordinator node
python -m examples.basic_coordinator_node

# Terminal 2: Start the partial node
python -m examples.basic_partial_node
```

The coordinator node will start a web server on port 8080, and the partial node will connect to it.

### Extending the Examples

#### Adding Custom RID Types

Create your own RID types by subclassing `RIDType`:

```python
from rid_lib import RIDType

class DocumentRID(RIDType):
    """A custom RID type for documents."""

    @classmethod
    def generate(cls, document_id: str):
        """Generate a new RID with the given document ID."""
        return cls.from_string(f"orn:my-app:document:{document_id}")
```

#### Adding Custom Handlers for Your RID Types

```python
@node.processor.register_handler(
    handler_type=HandlerType.Bundle,
    rid_types=[DocumentRID]
)
def document_handler(processor: ProcessorInterface, kobj: KnowledgeObject):
    """Process document knowledge objects."""

    # Extract document content
    document = kobj.contents

    # Process document
    process_document(document)

    # Set normalized event type
    kobj.normalized_event_type = kobj.event_type

    return kobj
```

#### Extending the Coordinator Node

You might want to extend the coordinator node to handle your custom RID types:

```python
# In your extended coordinator node
from my_app import DocumentRID

# Modify the node's provides to include your RID type
node = NodeInterface(
    config=CoordinatorNodeConfig(
        koi_net=KoiNetConfig(
            node_profile=NodeProfile(
                node_type=NodeType.FULL,
                provides=NodeProvides(
                    event=[KoiNetNode, KoiNetEdge, DocumentRID],
                    state=[KoiNetNode, KoiNetEdge, DocumentRID]
                )
            )
        )
    )
)
```

## Debugging Tips

### Enabling Debug Logging

KOI-net uses Python's standard logging system. To enable debug logs:

```python
import logging
from rich.logging import RichHandler  # Optional, for nicer formatting

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[RichHandler()]
)

# Set debug level for KOI-net packages
logging.getLogger("koi_net").setLevel(logging.DEBUG)
```

### Common Issues and Solutions

#### 1. Nodes Not Connecting

- Check that the first_contact URL is correct and accessible
- Ensure the coordinator node is running
- Check if there are any firewall issues blocking connections
- Verify that the coordinator's provides field includes the necessary RID types

#### 2. Events Not Being Processed

- Check that the handler for the RID type is registered
- Make sure the source (Internal/External) is set correctly
- Verify that the event_type matches what your handlers expect
- Check that no handler is returning STOP_CHAIN unexpectedly

#### 3. Cache Problems

- Ensure the cache_directory_path is writable
- Check if the normalized_event_type is being set correctly in Bundle handlers
- Verify that RID and manifest are valid

### Inspecting the Network Graph

You can inspect the network graph to see how nodes are connected:

```python
# Print all nodes in the graph
print("Nodes:", node.network.graph.dg.nodes())

# Print all edges in the graph
print("Edges:", node.network.graph.dg.edges())

# Print a specific node's profile
node_rid = list(node.network.graph.dg.nodes())[0]
profile = node.network.graph.get_node_profile(node_rid)
print(f"Node {node_rid} profile:", profile)
```

### Examining the Processing Pipeline

To understand what's happening in the processing pipeline, you can add a debug handler:

```python
@node.processor.register_handler(HandlerType.RID)
def debug_handler(processor: ProcessorInterface, kobj: KnowledgeObject):
    """Debug handler to log all knowledge objects."""
    print(f"Processing {kobj.rid} with event_type={kobj.event_type}, source={kobj.source}")
    return None  # Pass unmodified to the next handler
```

## Contributing to KOI-net

### Setting Up for Development

Clone the repository and install in development mode:

```bash
git clone https://github.com/BlockScience/koi-net.git
cd koi-net
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .[dev]
```

### Building and Distributing

To build the package:

```bash
python -m build
```

To publish to PyPI (requires credentials):

```bash
python -m twine upload --skip-existing dist/*
```

The package is also automatically published to PyPI when a new tag is pushed to the repository (see `.github/workflows/publish-to-pypi.yml`).

## Creating a Custom Node

To create a more complex node, you might need to extend beyond the basic examples. Here's a pattern for a more complete implementation:

```python
import logging
from koi_net import NodeInterface
from koi_net.protocol.node import NodeProfile, NodeProvides, NodeType
from koi_net.config import NodeConfig, KoiNetConfig
from koi_net.processor.handler import HandlerType
from koi_net.processor.knowledge_object import KnowledgeSource
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from my_app.rid_types import MyCustomRID
from my_app.handlers import (
    my_custom_rid_handler,
    my_custom_bundle_handler,
    my_custom_network_handler
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define node configuration
class MyNodeConfig(NodeConfig):
    koi_net: KoiNetConfig | None = Field(default_factory = lambda:
        KoiNetConfig(
            node_name="my_custom_node",
            node_profile=NodeProfile(
                node_type=NodeType.FULL,
                provides=NodeProvides(
                    event=[KoiNetNode, KoiNetEdge, MyCustomRID],
                    state=[KoiNetNode, KoiNetEdge, MyCustomRID]
                )
            ),
            cache_directory_path=".my_node_cache",
            event_queues_path="my_node_event_queues.json"
        )
    )

# Create node
node = NodeInterface(
    config=MyNodeConfig.load_from_yaml("my_node_config.yaml"),
    use_kobj_processor_thread=True,
    handlers=[
        # Mix of default and custom handlers
        basic_rid_handler,
        my_custom_rid_handler,
        basic_manifest_handler,
        my_custom_bundle_handler,
        my_custom_network_handler
    ]
)

# Register additional handlers directly
@node.processor.register_handler(HandlerType.Final)
def my_final_handler(processor: ProcessorInterface, kobj: KnowledgeObject):
    # Take some final action
    logger.info(f"Processed {kobj.rid} with event_type={kobj.normalized_event_type}")
    return None

# Setup FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting node...")
    node.start()
    yield
    logger.info("Stopping node...")
    node.stop()

app = FastAPI(lifespan=lifespan, root_path="/koi-net")

# Define API endpoints
# ... Standard KOI-net endpoints ...

# Add custom application endpoints
@app.get("/my-app/documents")
def list_documents():
    # Get all document RIDs from cache
    rids = node.cache.list_rids(rid_types=[MyCustomRID])
    return {"documents": rids}

# Run server
if __name__ == "__main__":
    uvicorn.run("my_app.node:app", host="0.0.0.0", port=8000)
```

This pattern allows you to build more complex applications on top of the KOI-net protocol.
