# States

### Objectives

To show all possible transitions and what are each an every one of them responsible for.

---

### Diagram

![States](../assets/cobalt-states.png)

### Volume transitions

Every new volume will have the `pending` state which tells the system it should be
scheduled on a machine. Once a suitable machine is found it transitions to the `scheduled` state.
Here the agent listens and sees that a new entry should be created on the disk it does so and sets
the volume to `ready`. In case a scheduled volume can't be handled, either the agent went down or
the agent has no more room left (due to dilation in-between scheduling and doing) it is set back to `pending`.

Tasks that are in pending for an X amount of time will trigger an alert, but will remain there in the
event room will be available.

There are 2 ways to delete a volume, either soft or hard. The soft deletion will transition to `decommisioned`,
recovery from this state is possible. On the other hand a hard delete will procede and scrub the disks (PERMANENTLY).

### Task queue

The task queue will be present for each and every volume and will persist as long as the volume itself will.
It is basically a FIFO list of instructions that needs to be applied on the volume entries: resize, move, clone,
change permissions etc.
These tasks should be applied as soon as possible if the volume is in either ready or pending state
and will delay transitions until they are consumed and relocated for storage.

Once a volume is deleted all its task history will be as well.
