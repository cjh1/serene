import serene
from bottle import run

datasets = {}

@serene.create()
def create_dataset(id, name, data):
    ds = dataset(id, name, data)
    datasets[id] = ds

    return ds

# Return GJSON
@serene.read(path="/vtk/read")
def read_vtk(filename, vars=None, timestep=None):
  return { "type": "FeatureCollection",
  "features": [
    { "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [102.0, 0.5]},
      "properties": {"prop0": "value0"}
      }]}

@serene.read()
def test(arg1, arg2, arg3):
    return "test"

@serene.delete()
def delete_dataset(id):
    return "DELETED"

@serene.update()
def update_dataset(id, updates):
    return "UPDATED"

@serene.read(datatype='dataset', path="/dataset")
def get_dataset(id):
    print "in get_dataset"
    return dataset(id)

class parameter:
    def __init__(self, name):
        self.name = name

    @serene.read(path="timestep")
    def timestep(self, id):
        return id

class dataset(object):
    def __init__(self, id, name, data):
        self.id = id
        self.data = data
        self.name = name

    @serene.read(path="get_timestep")
    def get_timestep(self, id):
        print 'get_time'
        return "dataset: "  + self.id + "\ntimestep: " + id + "\n"

    @serene.read(datatype='parameter', path='parameter')
    def parameter(self, name):
        return parameter(name)

run(reloader=True, host='localhost' , port=8082)
