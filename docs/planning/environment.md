# Environment

### Objective

To explain what Cobalt is responsible for setting up and what is taken for granted.
How it will be used and how it will be tested.

---

The storage cluster will be comprised of an ETCD cluster and several storage nodes running cobalt.

#### ETCD cluster

Cobalt sees this cluster as an external service, it is not responsible for expanding or shrinking
the quorum nor does it care of its size.
It expects that this information is given as a list of participating servers at
the start of the daemon / main process.

All connections to ETCD will be done though a DNS and it will know which servers are down and route accordingly.
Possibilities: AWS Route 53, HA Proxy at a known address.

#### Daemon

The daemon will allow control over which components should be started. Consider the case
when there are no storage nodes but requests for future volumes have to be created. One could
only enable the API to write these to ETCD and when time comes when storage nodes are
configured they could process them as soon as possible.

Each machine could in theory run multiple instances of Cobalt with different ETCD addresses and/or
separate BTRFS root volumes.

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


### In house usage

Currently we are using zfs data storage servers with automatic replication as backups.
Their main focus is to provide a place to store Wordpress hosted sites media files.
Currently the failover mechanism is done by UCARP at the IP level using a public entry IP.

Now as is when needing a new storage entry one would have to write on the master node through
SSH and create the appropriate folder structure that will further be exposed through NFS and
mounted inside an LXC container on a consumer machine running the actual site.
As one could figure out these static IPs could break a lot of things not to mention
that the pool of machines is somewhat static. In case of consumer machines moving to another
geographical area outside the storage's 'zone' will need full replication to the other storage tanks.

The project should fix these issues as storage nodes no longer require a static IP,
and no longer need to be maintained or provisioned manually with the added benefit of
a new and growing in popularity file system, namely BTRFS.

File details regarding what can get stored on a Wordpress install are mostly under 6MB in size for images
and significantly larger for videos, well withing BTRFS capability of 16 EiB. None of the storage nodes even
come close to the file limit cap at 2^64 files.



