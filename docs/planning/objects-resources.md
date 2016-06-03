# Objects & Resources

### Objective
Brief presentation of the resources managed by cobalt, along with the implicated resources needed for performing each operation. Also a presentation of what the client can do using cobalt will be given.

---

### Managed objects & resources
- Storage nodes
- BTRFS volumes

#### Storage nodes
The purpose of cobalt is to manage nodes used for storing data such as static media files in an efficient way. (more about this [here](https://github.com/PressLabs/cobalt/blob/13_environment/docs/planning/environment.md#in-house-usage))

#### BTRFS volumes
Storage nodes will be composed of BTRFS volumes of various sizes, satisfying the needs of each user. Cobalt will take care of allocating space in such a manner so that there will be a minimum of redundancy and unusable storage space.
Our main reason for choosing BTRFS as the filesystem for file storage is the advantage brought by [CoW](https://en.wikipedia.org/wiki/Copy-on-write) (Copy on Write) filesystems. Being able to create duplicates of blocks of data without using the actual storage space it would require for each copy represents a major benefit in the hosting industry.

---

### Implicated resources
- etcd cluster

#### etcd cluster
The [etcd](https://coreos.com/etcd/) distributed key value store is our choice for storing information that needs to be accessible to the whole cluster.

For now the cobalt information that will be written into etcd will consist of volume and node states. Future versions may also use it for enabling/disabling feature flags, taking advantage of how the application can be reconfigured through watches once a feature flag has changed its value.

---

### Client operations
Cobalt will give clients the liberty of performing basic CRUD operations (Create, Read, Update, Delete) on BTRFS volumes. Each will be accessible through an API endpoint that will be made available to the client.

#### Create
This operation will be used to create new BTRFS volumes of various sizes. Upon making a request, cobalt will take care of finding the right storage node for the new volume.

#### Read
This operation will be used for querying information about volumes or storage nodes. This information will consist of properties like free space, number of volumes on node and volume / machine [state](https://github.com/PressLabs/cobalt/blob/10_states/docs/planning/states.md).

#### Update
This operation will be used for resizing or moving volumes.
##### Resize volume
For certain reasons, one might want to reduce or expand the size of his volume. In the case of insufficient disk space on the current storage node, this operation will probably be prefixed behind the scenes with a move operation.
##### Move volume (Clone volume)
A move operation might be needed in case of insufficient disk space for volume expansion. It may also be needed in the case of making a backup / copy for failover scenarios.

#### Delete
This operation will take care of cleaning the storage node disk. It can be triggered on demand or by some cluster internal logic meant for cleaning old, unused volumes.