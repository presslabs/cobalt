# Language choice

### Possibilities
- Python
- Go

### Objective
Based on the needs of the project that need to be satisfied along with other perks that these languages bring, we will debate on which one is more fit for the job.

### Brief description
#### Python
Python is an interpreted object-oriented high-level programming language that first appeared in 1991. It is best known for the emphasis it puts on readability, as well as for its high-level built in data structures and dynamic typing & binding, which make prototyping and rapid coding an easy task.
#### Go
Go is a compiled, statically typed programming language that first appeared in 2009. It was created in the tradition of Algol and C, following the structured and imperative paradigms.

### Judging criteria

- Concurrency & Parallelism
- Language perks
- Popularity among other related projects
- Community
- Testability
- Libraries
- Prototyping ease

#### Concurrency & Parallelism
After previous discussions regarding [concurrency](https://github.com/PressLabs/cobalt/blob/5_threads-vs-coroutines/docs/planning/concurrency.md), we have settled that we will use coroutines.
##### Python
One of the best options for concurrency and parallelism in Python is to use the [gevent](https://github.com/gevent/gevent) library. Gevent makes use of the libevent and libev C libraries for asynchronous event notification and implements coroutines using greenlets, which are more lightweight than POSIX threads.
Its API design follows the conventions of the standard Python modules. As for the threading.Event built-in module, gevent.event.Event has a similar interface, using the `wait()`, `get()` and `join()` methods.
As a downside, gevent requires monkey patching the run-time code in order to be able to play nice with it.
##### Go
In Go the option for obtaining both concurrency and parallelism is by using goroutines. A possibly good reason for choosing Go would be that goroutines are managed by the runtime and do not permit manual management, thus avoiding human error. Piping between goroutines is done via channels.
Goroutines run on a few threads allocated to the runtime. They are multiplexed and only one goroutine will be ran on a thread at any given time. When a goroutine is blocked, it is switched with another goroutine to be executed on that thread instead.

#### Language perks
##### Python
- **Simplicity**
Python is easy to learn and fast to start with. You can spend less time on getting used to the tools used for the project and more time on getting the project done.
- **Short effective code**
Operations that would take up many lines of code in other languages can simply be written in Python even on one line.
Example:
```
list = []
for i in range(1, 10):
    if i % 2 == 0:
        list.append(i ** 2)
```
versus
```
list = [i**2 for i in range(1, 10) if i % 2 == 0]
```
- **Data type restrictions**
Unlike other dynamically typed languages, Python treats operations between different data types carefully and does not rely on intuition, ratherly throwing an error.
Example:
```
// Javascript addition between an array and an object
// will give an unexpected result
> [] + {}
"[object Object]"
```
versus
```
# Python addition between a list and a dictionary
# The error speaks for itself
>>> [] + {}
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: can only concatenate list (not "dict") to list
```

##### Go
- **Different error handling**
In Go the is no `try-catch-finally` idiom and there are no exceptions. A quote from the [offical golang website](https://golang.org/doc/faq) says that this common way of handling exceptions "results in convoluted code" and that "It also tends to encourage programmers to label too many ordinary errors, such as failing to open a file, as exceptional". As an alternative, Go uses multi-value returns for this.
Example:
```
f, err := os.Open("filename.ext")
if err != nil {
    log.Fatal(err)
}
// do something with the open *File f
```
- **No type inheritance**
Unlike other programming languages where the relation between two types has to be declared ahead of time, Go uses automatic deriving of these relations by the following rule: in Go a type automatically satisfies any interface that specifies a subset of its methods. This brings a level of simplicity even when compared to Python, where multiple inheritance requires typing all parent classes in the class header.
- **Pointers**
Go is a modern language that still gives the possibility to control memory at a low level. As a result, complex projects can be developed in something fairly easier to learn & use than C. These projects can also be considerably optimised in regard to speed, compared to the degree of optimisation that can be done using a dynamic language like Python.

#### Popularity among other related projects
This point of discussion has Go as a standing champion, as `etcd` is a project written in Go. Kubernetes, another project that will be used alongside cobalt in the future, is also written in Go.
An official answer on a [blog page](https://blog.gopheracademy.com/birthday-bash-2014/kubernetes-go-crazy-delicious/) about Go and Kubernetes states the following:

"We considered writing Kubernetes in the other main languages that we use at Google: C/C++, Java and Python. While each of these languages has its upsides, none of them hits the sweet spot like Go.

Go is neither too high level nor too low level."

Go is both a language for developing high-level software and a good system programming language. Since Kubernetes and etcd are a bit of both types of software, the reason why their authors chose Go becomes obvious.

#### Community
Both languages have attracted a great community of contributors. Go has managed to develop a great community in its 7 years of existence, but given the long time Python has been around (25 years) you are more prone to finding answers when working with Python rather than when working with Go.

#### Testability
TODO

#### Libraries
TODO

#### Prototyping ease
TODO

### Conclusions
TODO