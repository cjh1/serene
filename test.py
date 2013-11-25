import serene

datasets = {}

@serene.create()
def create_dataset(id, name, data):
    ds = dataset(id, name, data)
    datasets[id] = ds

    print datasets

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
def update_dataset(id, name):
    dataset = datasets[id]
    dataset.set_name(name)

    return dataset

@serene.read(datatype='dataset', path="/dataset")
def get_dataset(id):
    print "in get_dataset: " + id

    return datasets[int(id)]

class parameter:
    def __init__(self, name):
        self.name = name
        self.type = "temp"

    @serene.read(path="timestep")
    def timestep(self, id):
        return id

    @serene.update()
    def set_type(self, type):
        self.type = type

    @serene.update()
    def set_name(self, name):
        self.name = name

class dataset(object):
    def __init__(self, id, name, data):
        self.id = id
        self.data = data
        self.name = name
        self.parameters = {'name': parameter('name') }

    @serene.read(path="get_timestep")
    def get_timestep(self, id):
        """ Returns timestep for the given id."""
        return "dataset: "  + str(self.id) + "\ntimestep: " + str(id) + "\n"

    @serene.read(datatype='parameter', path='parameter')
    def parameter(self, name):
        return self.parameters[name]

    @serene.read(datatype='list(parameter)', path='parameters')
    def parameters(self):
        print 'parameters'
        return self.parameters


    @serene.create(path='parameter')
    def add_parameter(self, name):
        print 'add_parameter %s ' % name
        param = parameter(name)
        self.parameters[name] = param

    def set_name(self, name):
        self.name = name


#run(reloader=True, host='localhost' , port=8082)
