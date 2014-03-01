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
