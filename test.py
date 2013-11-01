import serene
from bottle import run

# Return GJSON
@serene.read(path="/vtk/read")
def read_vtk(filename, vars, timestep):
  return { "type": "FeatureCollection",
  "features": [
    { "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [102.0, 0.5]},
      "properties": {"prop0": "value0"}
      }]}

@serene.read()
def test(arg1, arg2, arg3):
    return "test"

@serene.create()
def create_dataset(id, dataset):
    return "OK"


run(host='localhost' , port=8082)
