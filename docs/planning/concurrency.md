# Concurrency

### Possibilities

- Processes
- Threads
- Coroutines [gevent](http://www.gevent.org/),
[goroutines](https://tour.golang.org/concurrency/1)

### Objective

Each of these will be described with respect to inter communication,
memory footprint, and last but not least speed.
Pros and cons will be weighted and analyzed in order to find the one best suited
for the current task.

---

#### Processes

Each computer program is a **process**, a set of instructions that run a
specific task concurrently. Each process has 1 main thread running
from the get-go.

##### Memory

The OS provides each process with different memory section and provides bounds
checking for memory interactions achieving data tampering prevention from
external processes.

Each process can spawn subprocesses through system calls that by default are a
snapshot of the same program at the system call's exit but totally independent
of its parent. The snapshot includes memory, file descriptors,
and cpu registers.

After creation it is scheduled by the OS like any other program. Each time the
OS considers that the allocated time slice for the current process has been
reached it then switches to another process that is waiting.
The choice of whom to go next is based on several criteria:
available data in FD's or time waited in the queue, defined priorities etc.

Each such context switch will have to backup file descriptors and cpu registers
and possible disk dumps of data and load the new processes' snapshot. As one
could imagine this takes a lot of time and due to the way memory is managed
and can easily fill disks.

##### Communication

__Events - Signals__

Inter-process communication can be done minimalistically through signals.
For instance each parent will get notified with SIGCHLD when one of its children
stop, signalling end of a task, data availability etc. Signals by themselves
provide an insufficient method of communication as transferring data back
can't be done directly. Spawning an extra process and its overhead just to
record data using I/O is a huge waste.

__Data transfer - Pipes__

Pipes are a one way shared communication channel allowing 2 processes to
communicate to each other. Like any other communication protocol it has to be
well defined, in case of linux commands this protocol is simple text. While
transferring data is now straight forward, marshalling and unmarshalling
is not as it takes a lot of time if not done properly / frequently.

##### Conclusions

Processes should be used for independent parts of a program that can
function as separate units and don't require communication between them, or
at the very least it should be kept to a minimum. Their number should be also
kept as low as possible due to all the context switching carried out.

---

#### Threads

Threads are the parallel work horses of processes, and are bound to one in
particular.

##### Memory

Their memory regime is shared between all threads of the same process.
Exception being the stack of called functions, these are unique for each and
every one of them. Since memory is shared little to no context needs to be
switched. Although the sharing of data directly can pose serious issues
regarding concurrent execution without proper locking mechanisms.

Threads can be ran in 2 different modes -> joinable or detached (an obvious
difference is the time at which data will be gc-ed)

##### Communication

Since memory is shared communication can be done directly without any need for
serialization / data transfer and thus faster.

##### Conclusions

Threads are faster and are currently the standard of multitasking things,
but require greater care of synchronization especially when dealing with state
machines (cobalt).

---

#### Coroutines

Unlike threads coroutines are functions scheduled by the program and not by the
OS. They are extremely lite in regarding memory footprint as they only require
their stack. They are usually executed on the same thread gevent but not always,
goroutines can be spread across any number of threads (taking the pros of each
side). Usually such routines can control when the execution switches focus to
another routine either by calling some system call, like sleep or by calling the
scheduler directly in case of Go.

#### Memory

Since they are normal function executions they only require data on their
stack which normally is of small size.
In the case of Go this even more so as they have a concept of segmenting and
growing the stack only when needed.

Being part of a process they have the same features as threads and by that I
mean they have a shared memory space, facilitating
communication between several coroutines / threads.

#### Communication

Synchronizing message consumption and creation / data transmission etc. both
Python and Go implemented different concepts

__Python__

Queues, Events

Queues: A synchronized data structure to send and receive messages like a pipe.
Events: Are basically a sort of barrier structure found in other languages that
can synchronize execution blocks

__GO__

Chan, Timeout, Select

Chan: Similar to a queue but works both-ways, can be blocking or non-blocking
and can also be used as an event bus Timeout: Can execute coroutines at regular
intervals or once after a delay, as well as stopping already running ones.
Select: A type of switch case that blocks until one of its branches can be
executed (events received / closed etc)

#### Conclusions

Unlike threads, coroutines can be more tightly packed onto a processor and can
be controlled without the interraction of the OS making it a lot faster.
In case of I/O waits threads are not blocked they simply switch to another
coroutine untill conditions are met.

---

### Conclusions

Processes in our case for each component would place to much unwanted strain on
the machines without gaining nothing in return
only headaches regarding communication between the components.
As Cobalt should only run on storage nodes it must only be bound
by I/O operations and not frequent context switches, as a result the
entire app will be within 1 process.

Threads could be feasible but coroutines can be used just as well.
In case we choose to opt for Go this difference is even more amplified.