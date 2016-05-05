# Environment

### Objective

To explain what Cobalt is responsible for setting up and what is taken for granted.

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

