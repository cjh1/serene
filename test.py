import serene
from bottle import run
@serene.create()
def create_dataset(id, dataset):
    return "OK"

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


run(host='localhost' , port=8082)
