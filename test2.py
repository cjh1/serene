import serene
from bottle import run

#Access the dataset:
# /dataset/id
#
# Access the timestep:
# /dataset/id/timestep/number

@serene.read(path="/dataset")
def get_dataset(id):
    print "in get_dataset"
    return dataset(id)

class parameter(object):
    @serene.read(path="timestep")
    def timestep(self, id):
        return id

class dataset(object):
    def __init__(self, id):
        print "in __init__"
        self.id = id

    @serene.read( selfish=get_dataset, path="get_timestep")
    def get_timestep(self, id):
        print 'get_time'
        return "dataset: "  + self.id + "\ntimestep: " + id + "\n"

    @serene.read(path='parameter')
    def parameter(self, name):
        return parameter()

run(reloader=True, host='localhost', port=8082)
