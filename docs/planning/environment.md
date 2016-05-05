# Environment

### Objective

To explain what Cobalt is responsible for setting up and what is taken for granted.
How it will be used and how it will be tested.

---

The Cobalt cluster will be comprised of an ETCD cluster and serveral storage nodes.

#### ETCD cluster

Cobalt sees this cluster as an external service, it is not responsible for expanding or shrinking
the quorum nor does it care of its size.
It expects that this information is given as a list of participating servers at
the start of the daemon / main process.

# TODO
Check how to handle when one node fails does the client switch automatically?
Maybe some sort of dns with health checks like route 53.

#### Daemon

Each storage node will run a single instance of Cobalt. This can be ensured from within
python [eg](http://stackoverflow.com/a/221159)

The daemon will expose a public web api on localhost but it is not responsible
for how clients will find it, HA proxies could help with this but will either have to
read for ETCD the machine pools or will have to be manually populated.

BTRFS and NFS-server have to be installed on the nodes and a proper endpoint for the
volumes has to be specified at first start time, later these configs will persist in
ETCD and will be the default values.


### Use cases

- Create / clone volumes
- Resize / move volumes
- Export permissions / accepted hosts - callback for changes
- Defragmentation / compression of volumes
- Storage node addition / removal - rebalancing

### Testing

Drone will be used to run the testcases after each push on git.

- Unit testing: API, Engine, Agent
- Integration testing: API public endpoints, Engine, Agent
- System tests

##### Integration testing

1. API:
    * all public endpoints will be tested and checked for proper changes in ETCD
2. Engine

##### System tests

To manage all the containers spawned we'll be using docker-compose.

- 1 ETCD docker container with just one server in the quorum (for speed)
- 3 Cobalt containers that act as a storage / api providers. These containers should have BTRFS and NFS on them.

**Cases:**

1. ETCD down (at start / during runtime)
    * any API call
    * Engine lease expiration (none should remain)
    * Agent still runs, no changes
2. Agent down
    * Volume present, changes in ETCD
    * Volume not present, scheduled for this agent but gone down -> reschedule
3. Engine leader down
    * Another takes its place and schedules (Only engine down, agent still has heartbeat)
4. NFS export created / modified
    * permission changes do consumers get affected -> mount destroyed / recreated
    * Volume moved to another machine notify and remount


### Volumes

As an end user volumes will be available to be mounted using the data provided by the api
ip permissions etc. Regular `mount` commands should work.

**Note:** [BTRFS restrictions](https://en.wikipedia.org/wiki/Btrfs)

