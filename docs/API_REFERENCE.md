# KOI-net API Reference

This document provides a comprehensive reference for all public classes, functions, and constants in the KOI-net package.

## Table of Contents

- [koi_net](#koi_net)
- [koi_net.config](#koi_netconfig)
- [koi_net.core](#koi_netcore)
- [koi_net.identity](#koi_netidentity)
- [koi_net.network](#koi_netnetwork)
  - [koi_net.network.graph](#koi_netnetworkgraph)
  - [koi_net.network.interface](#koi_netnetworkinterface)
  - [koi_net.network.request_handler](#koi_netnetworkrequest_handler)
  - [koi_net.network.response_handler](#koi_netnetworkresponse_handler)
- [koi_net.processor](#koi_netprocessor)
  - [koi_net.processor.handler](#koi_netprocessorhandler)
  - [koi_net.processor.interface](#koi_netprocessorinterface)
  - [koi_net.processor.knowledge_object](#koi_netprocessorknowledge_object)
  - [koi_net.processor.default_handlers](#koi_netprocessordefault_handlers)
- [koi_net.protocol](#koi_netprotocol)
  - [koi_net.protocol.api_models](#koi_netprotocolapi_models)
  - [koi_net.protocol.consts](#koi_netprotocolconsts)
  - [koi_net.protocol.edge](#koi_netprotocoledge)
  - [koi_net.protocol.event](#koi_netprotocolevent)
  - [koi_net.protocol.helpers](#koi_netprotocolhelpers)
  - [koi_net.protocol.node](#koi_netprotocolnode)

## koi_net

The root package that exposes the main `NodeInterface` class.

### Functions

None

### Classes

#### `NodeInterface`

```python
class NodeInterface(Generic[ConfigType])
```

The main interface class for a KOI-net node, integrating cache, identity, network, and processor components.

**Parameters:**

- `config: ConfigType` - Configuration for the node
- `use_kobj_processor_thread: bool = False` - Whether to use a separate thread for processing knowledge objects
- `handlers: list[KnowledgeHandler] | None = None` - Custom knowledge handlers to use
- `cache: Cache | None = None` - Optional custom cache implementation
- `network: NetworkInterface | None = None` - Optional custom network implementation
- `processor: ProcessorInterface | None = None` - Optional custom processor implementation

**Attributes:**

- `config: ConfigType` - Node configuration
- `cache: Cache` - RID cache for storing knowledge
- `identity: NodeIdentity` - Node identity information
- `network: NetworkInterface` - Network communication interface
- `processor: ProcessorInterface` - Knowledge processing interface
- `use_kobj_processor_thread: bool` - Whether a processor thread is being used

**Methods:**

`start() -> None`

Starts the node by initializing all components, loading event queues, generating the network graph, and (if needed) contacting a first contact node.

Example:

```python
node = NodeInterface(config=my_config)
node.start()  # Node is now running
```

`stop() -> None`

Stops the node by finishing processing and saving event queues.

Example:

```python
try:
    node.start()
    # Do node operations
finally:
    node.stop()  # Always stop properly
```

## koi_net.config

Configuration-related classes for KOI-net nodes.

### Functions

None

### Classes

#### `ServerConfig`

```python
class ServerConfig(BaseModel)
```

Server configuration for KOI-net nodes.

**Parameters:**

- `host: str | None = "127.0.0.1"` - Server host address
- `port: int | None = 8000` - Server port
- `path: str | None = "/koi-net"` - Base path for API endpoints

**Attributes:**

- `host: str | None` - Server host address
- `port: int | None` - Server port
- `path: str | None` - Base path for API endpoints

**Properties:**

`url`

Returns the complete URL for the server including host, port, and path.

Example:

```python
config = ServerConfig(host="example.com", port=8080)
print(config.url)  # "http://example.com:8080/koi-net"
```

#### `KoiNetConfig`

```python
class KoiNetConfig(BaseModel)
```

Configuration for a KOI-net node.

**Parameters:**

- `node_name: str` - The name of the node
- `node_rid: KoiNetNode | None = None` - Node RID, generated if not provided
- `node_profile: NodeProfile` - Node profile containing type and capabilities
- `cache_directory_path: str | None = ".rid_cache"` - Path to store RID cache
- `event_queues_path: str | None = "event_queues.json"` - Path to store event queues
- `first_contact: str | None = None` - URL of another node to contact initially

**Attributes:**

- `node_name: str` - The name of the node
- `node_rid: KoiNetNode | None` - Node RID
- `node_profile: NodeProfile` - Node profile
- `cache_directory_path: str | None` - Path to store RID cache
- `event_queues_path: str | None` - Path to store event queues
- `first_contact: str | None` - First contact URL

#### `EnvConfig`

```python
class EnvConfig(BaseModel)
```

Configuration for loading values from environment variables.

**Methods:**

`__getattribute__(name)`

Overridden to check for environment variables with the same name.

#### `NodeConfig`

```python
class NodeConfig(BaseModel)
```

Complete configuration for a KOI-net node.

**Parameters:**

- `server: ServerConfig | None` - Server configuration
- `koi_net: KoiNetConfig` - KOI-net node configuration

**Attributes:**

- `server: ServerConfig | None` - Server configuration
- `koi_net: KoiNetConfig` - KOI-net node configuration

**Methods:**

`load_from_yaml(file_path: str = "config.yaml", generate_missing: bool = True) -> NodeConfig`

Class method to load configuration from a YAML file.

Example:

```python
config = NodeConfig.load_from_yaml("my_config.yaml")
```

`save_to_yaml()`

Saves the configuration to the YAML file it was loaded from.

Example:

```python
config = NodeConfig.load_from_yaml("my_config.yaml")
config.koi_net.node_name = "new_name"
config.save_to_yaml()  # Changes are saved to my_config.yaml
```

## koi_net.core

Contains the core `NodeInterface` implementation.

### Functions

None

### Classes

#### `NodeInterface`

```python
class NodeInterface(Generic[ConfigType])
```

The main interface class for a KOI-net node, integrating cache, identity, network, and processor components.

This is the same class that is exposed at the package level. See [koi_net](#koi_net) for documentation.

## koi_net.identity

Contains classes for managing node identity.

### Functions

None

### Classes

#### `NodeIdentity`

```python
class NodeIdentity
```

Represents a node's identity (RID, profile, bundle).

**Parameters:**

- `config: NodeConfig` - Node configuration
- `cache: Cache` - RID cache for storing knowledge

**Attributes:**

- `config: NodeConfig` - Node configuration
- `cache: Cache` - RID cache

**Properties:**

`rid -> KoiNetNode`

Returns the node's RID.

Example:

```python
identity = NodeIdentity(config, cache)
print(identity.rid)  # orn:koi-net.node:node_name+uuid
```

`profile -> NodeProfile`

Returns the node's profile.

Example:

```python
identity = NodeIdentity(config, cache)
print(identity.profile.node_type)  # FULL or PARTIAL
```

`bundle -> Bundle`

Returns the node's bundle (RID + profile).

Example:

```python
identity = NodeIdentity(config, cache)
bundle = identity.bundle
print(bundle.manifest.rid)  # Same as identity.rid
print(bundle.contents)     # Same as identity.profile (as dict)
```

## koi_net.network

Package containing networking functionality.

### Functions

None

### Classes

#### `NetworkInterface`

```python
class NetworkInterface(Generic[ConfigType])
```

The main interface for network operations. See [koi_net.network.interface](#koi_netnetworkinterface) for details.

### koi_net.network.graph

Contains the `NetworkGraph` class for maintaining a graph view of the node's network.

#### Classes

##### `NetworkGraph`

```python
class NetworkGraph
```

Graph functions for this node's view of its network.

**Parameters:**

- `cache: Cache` - RID cache for storing knowledge
- `identity: NodeIdentity` - Node identity information

**Attributes:**

- `cache: Cache` - RID cache
- `identity: NodeIdentity` - Node identity
- `dg: nx.DiGraph` - NetworkX directed graph representation of the network

**Methods:**

`generate()`

Generates the directed graph from cached KoI nodes and edges.

Example:

```python
graph = NetworkGraph(cache, identity)
graph.generate()  # Builds graph from cached nodes and edges
```

`get_node_profile(rid: KoiNetNode) -> NodeProfile | None`

Returns the profile for a node RID.

Example:

```python
profile = graph.get_node_profile(node_rid)
if profile:
    print(f"Node type: {profile.node_type}")
```

`get_edge_profile(rid: KoiNetEdge | None = None, source: KoiNetNode | None = None, target: KoiNetNode | None = None) -> EdgeProfile | None`

Returns the profile for an edge RID or a source-target pair.

Example:

```python
# By edge RID
profile = graph.get_edge_profile(edge_rid)

# By source and target
profile = graph.get_edge_profile(source=my_node, target=other_node)
```

`get_edges(direction: Literal["in", "out"] | None = None) -> list[KoiNetEdge]`

Returns edges this node belongs to, optionally filtered by direction.

Example:

```python
# All edges
all_edges = graph.get_edges()

# Only incoming edges
incoming_edges = graph.get_edges(direction="in")

# Only outgoing edges
outgoing_edges = graph.get_edges(direction="out")
```

`get_neighbors(direction: Literal["in", "out"] | None = None, status: EdgeStatus | None = None, allowed_type: RIDType | None = None) -> list[KoiNetNode]`

Returns neighboring nodes, optionally filtered by edge direction, status, or RID type.

Example:

```python
# All neighbors
all_neighbors = graph.get_neighbors()

# Only neighbors connected by incoming edges
incoming_neighbors = graph.get_neighbors(direction="in")

# Only neighbors with approved edges
approved_neighbors = graph.get_neighbors(status=EdgeStatus.APPROVED)

# Only neighbors interested in a specific RID type
type_neighbors = graph.get_neighbors(allowed_type=MyCustomRID)
```

### koi_net.network.interface

Contains the `NetworkInterface` class for network communication.

#### Classes

##### `EventQueueModel`

```python
class EventQueueModel(BaseModel)
```

Model for event queues stored on disk.

**Attributes:**

- `webhook: dict[KoiNetNode, list[Event]]` - Events to send via webhook
- `poll: dict[KoiNetNode, list[Event]]` - Events to deliver via polling

##### `NetworkInterface`

```python
class NetworkInterface(Generic[ConfigType])
```

A collection of functions and classes to interact with the KOI network.

**Parameters:**

- `config: ConfigType` - Node configuration
- `cache: Cache` - RID cache for storing knowledge
- `identity: NodeIdentity` - Node identity information

**Attributes:**

- `config: ConfigType` - Node configuration
- `identity: NodeIdentity` - Node identity
- `cache: Cache` - RID cache
- `graph: NetworkGraph` - Network graph
- `request_handler: RequestHandler` - Handles outgoing requests
- `response_handler: ResponseHandler` - Handles incoming requests
- `poll_event_queue: EventQueue` - Queue for events to be polled
- `webhook_event_queue: EventQueue` - Queue for events to be sent via webhook

**Methods:**

`push_event_to(event: Event, node: KoiNetNode, flush=False)`

Pushes an event to the queue of the specified node.

Example:

```python
# Create and push an event
event = Event.from_rid(EventType.NEW, my_rid)
network.push_event_to(event, target_node)

# Create, push, and immediately send
network.push_event_to(event, target_node, flush=True)
```

`flush_poll_queue(node: KoiNetNode) -> list[Event]`

Flushes a node's poll queue, returning list of events.

Example:

```python
# Called by API endpoint when a node polls for events
events = network.flush_poll_queue(polling_node_rid)
return EventsPayload(events=events)
```

`flush_webhook_queue(node: KoiNetNode) -> bool`

Flushes a node's webhook queue, and broadcasts events.

Example:

```python
# Send all queued events to a node
success = network.flush_webhook_queue(target_node_rid)
```

`get_state_providers(rid_type: RIDType) -> list[KoiNetNode]`

Returns list of node RIDs which provide state for the specified RID type.

Example:

```python
# Find nodes that can provide state for MyCustomRID
providers = network.get_state_providers(MyCustomRID)
```

`fetch_remote_bundle(rid: RID) -> Bundle | None`

Attempts to fetch a bundle by RID from known peer nodes.

Example:

```python
# Try to fetch a bundle from any suitable node
bundle = network.fetch_remote_bundle(my_rid)
if bundle:
    print(f"Found bundle: {bundle.contents}")
```

`fetch_remote_manifest(rid: RID) -> Manifest | None`

Attempts to fetch a manifest by RID from known peer nodes.

Example:

```python
# Try to fetch a manifest from any suitable node
manifest = network.fetch_remote_manifest(my_rid)
if manifest:
    print(f"Found manifest: {manifest.timestamp}")
```

`poll_neighbors() -> list[Event]`

Polls all neighboring nodes and returns compiled list of events.

Example:

```python
# Poll all neighbors for events
events = network.poll_neighbors()
for event in events:
    node.processor.handle(event=event, source=KnowledgeSource.External)
```

### koi_net.network.request_handler

Contains the `RequestHandler` class for making requests to other nodes.

#### Classes

##### `RequestHandler`

```python
class RequestHandler
```

Handles making requests to other KOI nodes.

**Parameters:**

- `cache: Cache` - RID cache for storing knowledge
- `graph: NetworkGraph` - Network graph

**Attributes:**

- `cache: Cache` - RID cache
- `graph: NetworkGraph` - Network graph

**Methods:**

`make_request(url: str, request: RequestModels, response_model: type[ResponseModels] | None = None) -> ResponseModels | None`

Makes a request to the specified URL with the given request model.

`get_url(node_rid: KoiNetNode, url: str) -> str`

Retrieves URL of a node, or returns provided URL.

`broadcast_events(node: RID = None, url: str = None, req: EventsPayload | None = None, **kwargs) -> None`

Broadcasts events to another node.

Example:

```python
# Broadcast events to a specific node
handler.broadcast_events(
    node=target_node_rid,
    events=[event1, event2]
)

# Broadcast to a URL
handler.broadcast_events(
    url="http://example.com/koi-net/events/broadcast",
    events=[event1, event2]
)
```

`poll_events(node: RID = None, url: str = None, req: PollEvents | None = None, **kwargs) -> EventsPayload`

Polls for events from another node.

Example:

```python
# Poll for events from a specific node
payload = handler.poll_events(
    node=target_node_rid,
    rid=my_node_rid
)
events = payload.events
```

`fetch_rids(node: RID = None, url: str = None, req: FetchRids | None = None, **kwargs) -> RidsPayload`

Fetches RIDs from another node.

Example:

```python
# Fetch all RIDs of a certain type
payload = handler.fetch_rids(
    node=target_node_rid,
    rid_types=[MyCustomRID]
)
rids = payload.rids
```

`fetch_manifests(node: RID = None, url: str = None, req: FetchManifests | None = None, **kwargs) -> ManifestsPayload`

Fetches manifests from another node.

Example:

```python
# Fetch manifests for specific RIDs
payload = handler.fetch_manifests(
    node=target_node_rid,
    rids=[rid1, rid2]
)
manifests = payload.manifests
```

`fetch_bundles(node: RID = None, url: str = None, req: FetchBundles | None = None, **kwargs) -> BundlesPayload`

Fetches bundles from another node.

Example:

```python
# Fetch bundles for specific RIDs
payload = handler.fetch_bundles(
    node=target_node_rid,
    rids=[rid1, rid2]
)
bundles = payload.bundles
```

### koi_net.network.response_handler

Contains the `ResponseHandler` class for responding to requests from other nodes.

#### Classes

##### `ResponseHandler`

```python
class ResponseHandler
```

Handles generating responses to requests from other KOI nodes.

**Parameters:**

- `cache: Cache` - RID cache for storing knowledge

**Attributes:**

- `cache: Cache` - RID cache

**Methods:**

`fetch_rids(req: FetchRids) -> RidsPayload`

Generates response to a request to fetch RIDs.

Example:

```python
# In a FastAPI endpoint
@app.post(FETCH_RIDS_PATH)
def fetch_rids(req: FetchRids) -> RidsPayload:
    return node.network.response_handler.fetch_rids(req)
```

`fetch_manifests(req: FetchManifests) -> ManifestsPayload`

Generates response to a request to fetch manifests.

Example:

```python
# In a FastAPI endpoint
@app.post(FETCH_MANIFESTS_PATH)
def fetch_manifests(req: FetchManifests) -> ManifestsPayload:
    return node.network.response_handler.fetch_manifests(req)
```

`fetch_bundles(req: FetchBundles) -> BundlesPayload`

Generates response to a request to fetch bundles.

Example:

```python
# In a FastAPI endpoint
@app.post(FETCH_BUNDLES_PATH)
def fetch_bundles(req: FetchBundles) -> BundlesPayload:
    return node.network.response_handler.fetch_bundles(req)
```

## koi_net.processor

Package containing knowledge processing functionality.

### Functions

None

### Classes

#### `ProcessorInterface`

```python
class ProcessorInterface
```

The main interface for knowledge processing. See [koi_net.processor.interface](#koi_netprocessorinterface) for details.

### koi_net.processor.handler

Contains classes and constants for knowledge handlers.

#### Classes

##### `StopChain`

```python
class StopChain
```

Class for a sentinel value used by knowledge handlers to stop processing.

##### `HandlerType`

```python
class HandlerType(StrEnum)
```

Enum of handler types used in the knowledge processing pipeline.

**Values:**

- `RID = "rid"` - RID handler type
- `Manifest = "manifest"` - Manifest handler type
- `Bundle = "bundle"` - Bundle handler type
- `Network = "network"` - Network handler type
- `Final = "final"` - Final handler type

##### `KnowledgeHandler`

```python
class KnowledgeHandler
```

Handles knowledge processing events of the provided types.

**Attributes:**

- `func: Callable` - Handler function
- `handler_type: HandlerType` - Type of handler
- `rid_types: list[RIDType] | None` - RID types to handle (None = all)
- `source: KnowledgeSource | None` - Source to handle (None = all)
- `event_types: list[KnowledgeEventType] | None` - Event types to handle (None = all)

**Methods:**

`create(handler_type: HandlerType, rid_types: list[RIDType] | None = None, source: KnowledgeSource | None = None, event_types: list[KnowledgeEventType] | None = None)`

Class method decorator that returns a `KnowledgeHandler` instead of a function.

Example:

```python
@KnowledgeHandler.create(HandlerType.Bundle)
def my_handler(processor: ProcessorInterface, kobj: KnowledgeObject):
    # Handler logic
    return kobj
```

#### Constants

##### `STOP_CHAIN`

```python
STOP_CHAIN = StopChain()
```

Sentinel value used by knowledge handlers to stop the processing chain.

Example:

```python
@node.processor.register_handler(HandlerType.RID)
def filter_handler(processor: ProcessorInterface, kobj: KnowledgeObject):
    if should_block(kobj.rid):
        return STOP_CHAIN  # Stop processing this knowledge object
    return kobj
```

### koi_net.processor.interface

Contains the `ProcessorInterface` class for knowledge processing.

#### Classes

##### `ProcessorInterface`

```python
class ProcessorInterface
```

Provides access to this node's knowledge processing pipeline.

**Parameters:**

- `config: NodeConfig` - Node configuration
- `cache: Cache` - RID cache for storing knowledge
- `network: NetworkInterface` - Network interface
- `identity: NodeIdentity` - Node identity
- `use_kobj_processor_thread: bool` - Whether to use a separate thread
- `default_handlers: list[KnowledgeHandler] = []` - Default handlers to use

**Attributes:**

- `config: NodeConfig` - Node configuration
- `cache: Cache` - RID cache
- `network: NetworkInterface` - Network interface
- `identity: NodeIdentity` - Node identity
- `handlers: list[KnowledgeHandler]` - Knowledge handlers
- `kobj_queue: queue.Queue[KnowledgeObject]` - Queue of knowledge objects
- `use_kobj_processor_thread: bool` - Whether a processor thread is used
- `worker_thread: threading.Thread | None` - Worker thread for processing

**Methods:**

`add_handler(handler: KnowledgeHandler)`

Adds a handler to this processor.

Example:

```python
from koi_net.processor.default_handlers import basic_rid_handler
processor.add_handler(basic_rid_handler)
```

`register_handler(handler_type: HandlerType, rid_types: list[RIDType] | None = None, source: KnowledgeSource | None = None, event_types: list[KnowledgeEventType] | None = None)`

Decorator to register a function as a handler.

Example:

```python
@processor.register_handler(HandlerType.Bundle)
def my_handler(processor: ProcessorInterface, kobj: KnowledgeObject):
    # Handler logic
    return kobj
```

`call_handler_chain(handler_type: HandlerType, kobj: KnowledgeObject) -> KnowledgeObject | StopChain`

Calls handlers of provided type, chaining their inputs and outputs together.

`process_kobj(kobj: KnowledgeObject) -> None`

Processes a knowledge object through the pipeline phases.

`flush_kobj_queue()`

Flushes all knowledge objects from queue and processes them.

Example:

```python
# For single-threaded nodes
processor.flush_kobj_queue()
```

`kobj_processor_worker(timeout=0.1)`

Worker function for the processor thread.

`handle(rid: RID | None = None, manifest: Manifest | None = None, bundle: Bundle | None = None, event: Event | None = None, kobj: KnowledgeObject | None = None, event_type: KnowledgeEventType = None, source: KnowledgeSource = KnowledgeSource.Internal)`

Queues provided knowledge to be handled by processing pipeline.

Example:

```python
# Handle an RID
processor.handle(rid=my_rid)

# Handle a bundle with event type
processor.handle(bundle=my_bundle, event_type=EventType.NEW)

# Handle an event from another node
processor.handle(event=event, source=KnowledgeSource.External)
```

### koi_net.processor.knowledge_object

Contains classes related to knowledge objects.

#### Classes

##### `KnowledgeSource`

```python
class KnowledgeSource(StrEnum)
```

Enum for knowledge sources.

**Values:**

- `Internal = "INTERNAL"` - Knowledge generated internally
- `External = "EXTERNAL"` - Knowledge received from another node

##### `KnowledgeObject`

```python
class KnowledgeObject(BaseModel)
```

A normalized knowledge representation for internal processing.

**Parameters:**

- `rid: RID` - Resource identifier
- `manifest: Manifest | None = None` - Manifest
- `contents: dict | None = None` - Contents
- `event_type: KnowledgeEventType = None` - Event type
- `source: KnowledgeSource` - Knowledge source
- `normalized_event_type: KnowledgeEventType = None` - Normalized event type
- `network_targets: set[KoiNetNode] = set()` - Nodes to broadcast to

**Attributes:**

- `rid: RID` - Resource identifier
- `manifest: Manifest | None` - Manifest
- `contents: dict | None` - Contents
- `event_type: KnowledgeEventType` - Event type
- `source: KnowledgeSource` - Knowledge source
- `normalized_event_type: KnowledgeEventType` - Normalized event type
- `network_targets: set[KoiNetNode]` - Nodes to broadcast to

**Methods:**

`from_rid(rid: RID, event_type: KnowledgeEventType = None, source: KnowledgeSource = KnowledgeSource.Internal) -> "KnowledgeObject"`

Creates a knowledge object from an RID.

Example:

```python
kobj = KnowledgeObject.from_rid(my_rid, EventType.NEW)
```

`from_manifest(manifest: Manifest, event_type: KnowledgeEventType = None, source: KnowledgeSource = KnowledgeSource.Internal) -> "KnowledgeObject"`

Creates a knowledge object from a manifest.

Example:

```python
kobj = KnowledgeObject.from_manifest(my_manifest, EventType.UPDATE)
```

`from_bundle(bundle: Bundle, event_type: KnowledgeEventType = None, source: KnowledgeSource = KnowledgeSource.Internal) -> "KnowledgeObject"`

Creates a knowledge object from a bundle.

Example:

```python
kobj = KnowledgeObject.from_bundle(my_bundle, EventType.NEW)
```

`from_event(event: Event, source: KnowledgeSource = KnowledgeSource.Internal) -> "KnowledgeObject"`

Creates a knowledge object from an event.

Example:

```python
kobj = KnowledgeObject.from_event(event, KnowledgeSource.External)
```

**Properties:**

`bundle`

Returns the bundle representation (manifest + contents).

`normalized_event`

Returns an event object with the normalized event type.

### koi_net.processor.default_handlers

Contains default knowledge handlers.

#### Functions

##### `basic_rid_handler(processor: ProcessorInterface, kobj: KnowledgeObject)`

Default RID handler that blocks external events about this node and allows `FORGET` events if RID is known.

##### `basic_manifest_handler(processor: ProcessorInterface, kobj: KnowledgeObject)`

Default manifest handler that blocks duplicates and sets normalized event type.

##### `edge_negotiation_handler(processor: ProcessorInterface, kobj: KnowledgeObject)`

Handles edge negotiation by approving valid edge requests and rejecting invalid ones.

##### `coordinator_contact(processor: ProcessorInterface, kobj: KnowledgeObject)`

Identifies coordinator nodes and proposes edges to them.

##### `basic_network_output_filter(processor: ProcessorInterface, kobj: KnowledgeObject)`

Default network handler that determines which nodes to broadcast events to.

## koi_net.protocol

Package containing protocol-related classes and constants.

### koi_net.protocol.api_models

Contains Pydantic models for API requests and responses.

#### Classes

##### Request Models

###### `PollEvents`

```python
class PollEvents(BaseModel)
```

Request model for polling events.

**Attributes:**

- `rid: RID` - The RID of the node polling for events
- `limit: int = 0` - Optional limit on number of events to return

###### `FetchRids`

```python
class FetchRids(BaseModel)
```

Request model for fetching RIDs.

**Attributes:**

- `rid_types: list[RIDType] = []` - RID types to fetch

###### `FetchManifests`

```python
class FetchManifests(BaseModel)
```

Request model for fetching manifests.

**Attributes:**

- `rid_types: list[RIDType] = []` - RID types to fetch manifests for
- `rids: list[RID] = []` - Specific RIDs to fetch manifests for

###### `FetchBundles`

```python
class FetchBundles(BaseModel)
```

Request model for fetching bundles.

**Attributes:**

- `rids: list[RID]` - RIDs to fetch bundles for

##### Response Models

###### `RidsPayload`

```python
class RidsPayload(BaseModel)
```

Response model for fetching RIDs.

**Attributes:**

- `rids: list[RID]` - List of RIDs

###### `ManifestsPayload`

```python
class ManifestsPayload(BaseModel)
```

Response model for fetching manifests.

**Attributes:**

- `manifests: list[Manifest]` - List of manifests
- `not_found: list[RID] = []` - RIDs that were not found

###### `BundlesPayload`

```python
class BundlesPayload(BaseModel)
```

Response model for fetching bundles.

**Attributes:**

- `bundles: list[Bundle]` - List of bundles
- `not_found: list[RID] = []` - RIDs that were not found
- `deferred: list[RID] = []` - RIDs that will be processed later

###### `EventsPayload`

```python
class EventsPayload(BaseModel)
```

Model for sending or receiving events.

**Attributes:**

- `events: list[Event]` - List of events

### koi_net.protocol.consts

Contains constants for API paths.

#### Constants

```python
BROADCAST_EVENTS_PATH = "/events/broadcast"
POLL_EVENTS_PATH      = "/events/poll"
FETCH_RIDS_PATH       = "/rids/fetch"
FETCH_MANIFESTS_PATH  = "/manifests/fetch"
FETCH_BUNDLES_PATH    = "/bundles/fetch"
```

### koi_net.protocol.edge

Contains classes related to edges between nodes.

#### Classes

##### `EdgeStatus`

```python
class EdgeStatus(StrEnum)
```

Enum for edge status.

**Values:**

- `PROPOSED = "PROPOSED"` - Edge has been proposed but not approved
- `APPROVED = "APPROVED"` - Edge has been approved

##### `EdgeType`

```python
class EdgeType(StrEnum)
```

Enum for edge type.

**Values:**

- `WEBHOOK = "WEBHOOK"` - Edge uses webhooks for event delivery
- `POLL = "POLL"` - Edge uses polling for event delivery

##### `EdgeProfile`

```python
class EdgeProfile(BaseModel)
```

Profile for an edge between nodes.

**Attributes:**

- `source: KoiNetNode` - Source node RID
- `target: KoiNetNode` - Target node RID
- `edge_type: EdgeType` - Type of edge
- `status: EdgeStatus` - Status of edge
- `rid_types: list[RIDType]` - RID types allowed on this edge

### koi_net.protocol.event

Contains classes related to events.

#### Classes

##### `EventType`

```python
class EventType(StrEnum)
```

Enum for event types.

**Values:**

- `NEW = "NEW"` - New knowledge
- `UPDATE = "UPDATE"` - Updated knowledge
- `FORGET = "FORGET"` - Forgotten knowledge

##### `Event`

```python
class Event(BaseModel)
```

Event representing a change in a node's knowledge state.

**Attributes:**

- `rid: RID` - Resource identifier
- `event_type: EventType` - Type of event
- `manifest: Manifest | None = None` - Optional manifest
- `contents: dict | None = None` - Optional contents

**Methods:**

`from_bundle(event_type: EventType, bundle: Bundle) -> Event`

Creates an event from a bundle.

`from_manifest(event_type: EventType, manifest: Manifest) -> Event`

Creates an event from a manifest.

`from_rid(event_type: EventType, rid: RID) -> Event`

Creates an event from an RID only.

**Properties:**

`bundle`

Returns the bundle representation, if available.

### koi_net.protocol.helpers

Contains helper functions for the protocol.

#### Functions

##### `generate_edge_bundle(source: KoiNetNode, target: KoiNetNode, rid_types: list[RIDType], edge_type: EdgeType) -> Bundle`

Generates a bundle representing an edge between two nodes.

Example:

```python
# Create a bundle for a proposed edge
bundle = generate_edge_bundle(
    source=my_node_rid,
    target=other_node_rid,
    rid_types=[MyCustomRID],
    edge_type=EdgeType.WEBHOOK
)
```

### koi_net.protocol.node

Contains classes related to nodes.

#### Classes

##### `NodeType`

```python
class NodeType(StrEnum)
```

Enum for node types.

**Values:**

- `FULL = "FULL"` - Full node (web server)
- `PARTIAL = "PARTIAL"` - Partial node (web client)

##### `NodeProvides`

```python
class NodeProvides(BaseModel)
```

What RID types a node provides.

**Attributes:**

- `event: list[RIDType] = []` - RID types provided via events
- `state: list[RIDType] = []` - RID types provided via state endpoints

##### `NodeProfile`

```python
class NodeProfile(BaseModel)
```

Profile for a node.

**Attributes:**

- `base_url: str | None = None` - Base URL for full nodes
- `node_type: NodeType` - Type of node
- `provides: NodeProvides = NodeProvides()` - What the node provides
