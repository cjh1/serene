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
  def __init__(self, id):
    self.id = id
  
  def id(self):
    return id
  
foos = {}  

def create_foo(foo_id):
  foo = Foo(foo_id)
  foos[foo_id] = foo
  
  return foo
  
def find_foo(foo_id):
  if foo_id in foos:
    return foos[foo_id]
  else:
    return None

```

So given this simple API we can go ahead and decorate it with serene

```python
class Foo:
  def __init__(self, id):
    self.id = id
  
  @seren.read(path='id')
  def id(self):
    return id
  
foos = {}  

@serene.create(path='/foo')
def create_foo(foo_id):
  foo = Foo(foo_id)
  foos[foo_id] = foo
  
  return foo
  
@serene.read(path='/foo, datatype='Foo')  
def find_foo(foo_id):
  if foo_id in foos:
    return foos[foo_id]
  else:
    return None

```




#### serenecl

serencecl is commandline tool that take a decortated module and can either produce documentation descripting the RESTful interface that will be exposed or expose it using bottle.py





