import serene
from bottle import run

#Access the dataset:
# /dataset/id
#
# Access the timestep:
# /dataset/id/timestep/number

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
    def __init__(self, id):
        print "in __init__"
        self.id = id

    @serene.read(path="get_timestep")
    def get_timestep(self, id):
        print 'get_time'
        return "dataset: "  + self.id + "\ntimestep: " + id + "\n"

    @serene.read(datatype='parameter', path='parameter')
    def parameter(self, name):
        return parameter(name)

run(reloader=True, host='localhost', port=8082)
