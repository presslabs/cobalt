# States

### Objectives

To show all possible transitions and what are each an every one of them responsible for.

---

### Diagram

![States](../assets/cobalt-states.png)

### Volume transitions

Every new volume will have the `registered` state which tells the system it should be
scheduled on a machine. Once a suitable machine is found it transitions to the `scheduling` state.
Agent confirms creation transitioning it to `ready`.

From the ready state only one can update the volume characteristics. After a change in the expected state is detected
the API transitions to `pending` to inform the engine an operation is required. It decides which `*-ing` operation best
suits the changes and transitions the volume to that state (at this time it also resets error messages / try counts, makes
decisions on where to clone / move / if the resize is possible etc).

Once the agent sees a transition it tries to apply the changes if it succeeds then it sets it to `ready`, if it fails
it marks it as `pending` + increments try counts / error messages etc.
One could configure the api to stop trying after n iterations or to alert a human.

To remove the nfs exposure one could set a decommissioned flag on true -> the volume ending in a
`decommissioned` state. From here one could order a scrub and resource release.