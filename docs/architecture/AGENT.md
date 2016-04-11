# Agent

### Purpose

- Task execution
- [NFS](http://nfs.sourceforge.net/) Volume entry points

### Description

The agent is the running process on all machines that should provide resources in the resource pool
managed by the [api](API.md). It knows to provide a heartbeat with its status (available memory, state of volumes under
its control etc) at regular intervals to the [etcd](ETCD.md) cluster.

The [api](API.md) when it sees so fit may queue tasks for the agent to execute.