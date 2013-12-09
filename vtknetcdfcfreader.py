import serene
import uuid
import vtk
from standardtime import attrib_to_converters

readers = {}

class vtkNetCDFCFReader:
    def __init__(self, filename):
        self.id = uuid.uuid1()

        self.filename = filename
        self._reader = vtk.vtkNetCDFCFReader() #get test data
        self._reader.SphericalCoordinatesOff()
        self._reader.SetOutputTypeToImage()
        self._reader.ReplaceFillValueWithNanOn()
        self._reader.SetFileName(filename)
        self._reader.UpdateInformation()

    @serene.read(path='filename')
    def filename(self):
        return self.filename

    @serene.read(path='timestep', paramloc='query')
    def read(self, variables, timestep):

        #obtain temporal information
        rawTimes = self._reader.GetOutputInformation(0).Get(vtk.vtkStreamingDemandDrivenPipeline.TIME_STEPS())
        tunits = self._reader.GetTimeUnits()
        converters = attrib_to_converters(tunits)

        # pick particular timestep
        if timestep is not None and rawTimes is not None:
            utcconverter = attrib_to_converters("days since 1970-0-0")
            abs_request_time = utcconverter[0](float(timestep)/(1000*60*60*24))

            local_request_time = converters[5](abs_request_time)

            # For now clamp to time range
            if float(local_request_time) < rawTimes[0]:
                local_request_time = rawTimes[0]
            elif float(local_request_time) > rawTimes[-1]:
                local_request_time = rawTimes[-1]

            sddp = self._reader.GetExecutive()
            sddp.SetUpdateTimeStep(0, local_request_time)

        # enable only chosen array(s)
        narrays = self._reader.GetNumberOfVariableArrays()
        for x in range(0,narrays):
            arrayname = self._reader.GetVariableArrayName(x)
            if arrayname in variables:
                #cherrypy.log("Enable " + arrayname)
                self._reader.SetVariableArrayStatus(arrayname, 1)
            else:
                #cherrypy.log("Disable " + arrayname)
                self._reader.SetVariableArrayStatus(arrayname, 0)

        # wrap around to get the implicit cell
        extent = self._reader.GetOutputInformation(0).Get(vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT())
        pad = vtk.vtkImageWrapPad()
        self._reader.Update()
        data = self._reader.GetOutput()
        da = data.GetPointData().GetArray(0).GetName();
        data.GetPointData().SetActiveScalars(da)
        pad.SetInputData(data)
        pad.SetOutputWholeExtent(extent[0], extent[1]+1,
                                 extent[2], extent[3],
                                 extent[4], extent[5]);

        # Convert to polydata
        sf = vtk.vtkDataSetSurfaceFilter()
        sf.SetInputConnection(pad.GetOutputPort())

        # Error reading file?
        if not sf.GetOutput():
          raise IOError("Unable to load data file: " + self.filename)

        # Convert to GeoJSON
        gw = vtk.vtkGeoJSONWriter()
        gw.SetInputConnection(sf.GetOutputPort())
        gw.SetScalarFormat(2)
        gw.WriteToOutputStringOn()
        gw.Write()
        gj = str(gw.RegisterAndGetOutputString()).replace('\n','')
        return gj

@serene.create(path="/vtkreaders")
def open(filename):
    reader = vtkNetCDFCFReader(filename)
    readers[reader.id] = reader
    return reader

# These function are only required to support the REST API :-(
@serene.read(path='/vtkreaders', datatype='vtkNetCDFCFReader')
def _get_reader(id):
    reader = readers.get(uuid.UUID(id), None)

    return reader

@serene.delete(path='/vtkreaders')
def _delete_reader(id):
    id = uuid.UUID(id)
    if id in readers:
        del readers[id]
