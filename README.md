serene - RESTful Python APIs
======

#### Motivation

serene is designed to allow the user to expose a Python API through a RESTful endpoint with the minium of code changes. The idea is that if your API is well designed it should be a pretty mechanicial process to convert it to a RESTful API, serene takes care of this for you. It allow you to have two API for the price one, a Python API that can be called locally and RESTful API for client/server mode.

#### How it works

serene provides a set of decorators that are using to tag the functions on your API and define how are they are to be exposed. There are four decorators the corrispond to the basic CRUD operations.

```python
@serene.create
@serene.read
@serene.update
@serne.delete
```

So let take a simple example

```python
class Foo:
  def __init__(self, bar):
    self.bar = bar

  def bar(self):
    return bar

foos = {}

def create_foo(id, bar):
  foo = Foo(bar)
  foos[id] = foo

  return foo

def find_foo(id):
  if id in foos:
    return foos[id]
  else:
    return None

```

So given this simple API we can go ahead and decorate it with serene

```python
import serene

class Foo:
  def __init__(self, bar):
    self.bar = bar

  @serene.read(path='bar')
  def bar(self):
    return bar

foos = {}

@serene.create(path='/foo')
def create_foo(id, bar):
  foo = Foo(bar)
  foos[id] = foo

  return foo

@serene.read(path='/foo', datatype='Foo')
def find_foo(id):
  if id in foos:
    return foos[id]
  else:
    return None

```
We can now look at the RESTful API the serene will generate for us

```bash
$ python serenecl.py --doc foo

Serene generated RESTful API

GET /foo/<id>
GET /foo/<id>/bar
POST /foo

  Message Body:
    {
      "bar": <bar>, 
      "id": <id>
    }

```

So we can see that we can create a Foo using a POST request to /foo passing a JSON message as the body containing the id. We can then lookup a Foo using a GET request to /foo/<id> and finally we can access bar field of a Foo using a GET request to /foo/<id>/bar.

So we can now run the foo module in serene's server mode

```bash
$ python serenecl.py --server foo
Bottle v0.12-dev server starting up (using WSGIRefServer())...
Listening on http://localhost:8082/
Hit Ctrl-C to quit.

```

This starts a web server based on bottle.py that will now server our REST API. 

So we can create a Foo

```bash
$ curl -X POST --data '{"id":1, "bar": "bar bar black sheep"}' http://localhost:8082/foo
```


#### serenecl

serencecl is commandline tool that take a decortated module and can either produce documentation descripting the RESTful interface that will be exposed or expose it using bottle.py





