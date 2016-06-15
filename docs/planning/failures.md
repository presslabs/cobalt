# Failures

## Objective

The purpose of this document is to document and state all possible failures
that could happen, and figure out a solution prior to the implementation
phase actually starting.

---


### ETCD

Since this component is outside the scope of the project we'll talk briefly on
possible problems when integrating it in the cluster.

Since ETCD is a datastore that is in the middle of all the other components
a failure at this level will affect all other processes. Due to how it is built
and how it functions in a quorum it by its nature could last even if half
of its participating nodes fail at the same time. One taking into account only
the previously stated would think that ramping up the number of nodes could
technically fix the problem, and it would not for the
hidden repercussions. Raft the algorithm it uses internally has to keep each
node in sync and by raising the quorum size one would effectively reduce
semnificatively the data throughput of the system. By nature and its constant
network synchronization the distance between servers should be minimal to reduce
network lag. Having such close proximity
to one another possibly situated on the same rack (which is frowned upon,
at least 2 racks to provide the necessary redundancy) could
could leave one naked in the event of a power outage.

### API

Since the API will be hosted on each node it may be the case when 2 updates
happen in the same time each changing
a different attribute on a volume and only the last one will take precedence
even though the responses will appear to have both succeed.
The last one will take precedence because of how ETCD handles the writes.
A possible solution to this would be to change as little information on the
volume as possible or to have the API use ETCD's compare and swap. Both should
work just fine as the throughput of commands for
volume management is quite low.

### ENGINE

#### Leader election

Since the engine component will run on all storage nodes by default a master
election method is needed to prevent multiple decision makers at any time.

Since we are using ETCD which in turn uses [Raft](https://raft.github.io/)
consensus algorithm to manage its own master
and data replication we've already got the foundation built for us.
We'll instead use a lease mechanism to select the engine leader through a
simple FIFO method. While in some systems fairness regarding lease times
is essential in our case this is not an issue. We don't care who takes the
decision as all of them have the same view on the world in the first place.
The FIFO method works like this:

1. On engine start it appends to an ETCD managed list, refreshing it constantly
2. If it is the first, with respect to ETCD modification index it is the MASTER,
if not continue
3. Sets a watch on the previous entry
4. If the node watched goes away, check if it is the new master else go to `3.`

This works even when multiple nodes die off at the watch time since a watch on
an nonexistent entry will through an exception and a watch could then be
re-established on the next candidate etc.

If the engine schedules a volume change to one machine, and then it looses
the leader status. The new leader should be aware of this fact and monitor
the task as if it were his own.


#### No suitable host for Volume

In the event a volume doesn't meet the specified requirements on all available
machines. What then?

- Volume remains in pending state.
    - How long?
    - Method or retrial:
        - Pooling
        - Resource changes (Machine added, Volumes resized, Labels changed)
- Notification toward maintainers.

#### Insufficient storage for current volumes

Due to the existence of only a soft cap for reserving space on the machine but
no constraint for the actual volume sizes
available memory can reach 0.

- Notification toward maintainers.
- Machines added to cluster -> trigger minimal rebalancing of volumes
- Apply subvolume quotas (hard limits)

### AGENT

The agent should be resilient to network failures and should not delete volumes
unless explicitly told to do so. In case of a network failure no volume
states can be fetched and as a result there is the risk of
it reconciling with no volumes thus deleting them.

Agents fails to respond in time to volume state changes, either due to network
downtime or to any other reason like no more space even though the engine
thought it could in the past. The task should be rescheduled.

#### Single point of failure

All these components will have a standby duplicate ready to take its place,
with the exception of the agent and the node itself.

If the node fails the volume states will not change on the machine until
it comes back up. As for the node entirely failing data could be lost if at the
underlying layers above BTRFS a system like
[DRBD](https://www.drbd.org/en/) or
[ISCSI](https://en.wikipedia.org/wiki/ISCSI).
Maybe in a future version of Cobalt replication will be a thing.