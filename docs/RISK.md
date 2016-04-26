# Risks


#### Single point of failure


Reliability and resilience are a must in any distributed system. No mix of component failures should prevent the service from
working.

---

- ETCD   -> **cluster of at least 3** servers but not too many due to how the raft algorithm works
- API    -> At least 2 servers load balanced
- Engine -> Each storage box will have its own engine in the quorum
- Agent  -> One agent per storage box - failures
    - network: all is good once the node comes back up
    - disk: volumes on the machine ma **LOST**  (**SOLUTION NEEDED**)


#### Quorum leader

Since each node has its own engine running to remove all ambiguity of who takes what decision a consensus mechanism
has to be utilized. Only one engine will be in charge at a time.

---

Leader selection method based on [Raft](http://thesecretlivesofdata.com/raft/)

- Discovery: All nodes will be present in ETCD /machines
    - initially: they are all **Followers**
- Election:
    - followers that don't hear from the leader's heartbeat can become **Candidates**
    - candidates ask for **votes** from all nodes -> positive / negative responses. Nodes cast votes once.
    - candidates become **Leaders** if they have majority of votes
        - In case Candidates can't win, another node will try to have a go with an increased election count.



#### Missed tasks

Once a task is set in by the API in ETCD it should be processed no mater the circumstances.

---

- Agent goes away: If an agent has some tasks to do and it fails to do them in X amount of time or his heartbeat stops
                   then the task is rescheduled.
- Agent fails and scheduling engine fails : New leader should notice tasks ordered by the old leader and reschedule.


#### No suitable host for Volume

In the event a volume doesn't meet the specified requirements on all available machines. What then?

---

- Volume remains in pending state.
    - How long?
    - Method or retrial:
        - Pooling
        - Resource changes (Machine added, Volumes resized, Labels changed)
- Notification toward maintainers.



#### Insufficient storage for current volumes

Due to the existence of only a soft cap for reserving space on the machine but no constraint for the actual volume sizes
available memory can reach 0.

---

- Notification toward maintainers.
- Machines added to cluster -> trigger minimal rebalancing of volumes

