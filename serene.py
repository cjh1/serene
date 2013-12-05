from bottle import route, run, request, response, abort, HTTPResponse
import inspect
import json
import functools
from collections import defaultdict
import sys
import uuid


def tree():
    return defaultdict(tree)

# class containing contain the method => {mount point: func}
instance_path_map = tree()
# Function to datatype they are marked to return
func_to_type_map = {}
# class name => (member => update function)
class_to_update_methods = tree()
# class name => (path => create function)
class_to_create_methods = tree()

# class name => (path => delete function)
class_to_delete_methods = tree()

mount_points_to_functions = {}

func_to_wrapper = {}

def extract_query_args(func, pargs):

    query_args = []

    func_args = inspect.getargspec(func)[0]

    for arg in func_args[len(pargs):]:
        if arg in request.query:
            value = request.query[arg]

            if ',' in value:
                value = value.split(',')
            query_args.append(value)

    return query_args

def resolve_resource(method, func, *args, **kwargs):

    path_components = kwargs['path'].split('/')
    path_components = filter(None, path_components)

    # If the function doesn't resolve to an instance then return None, so the
    # caller knows
    if not func in func_to_type_map:
        return (None, list(args) + path_components)

    pargs = []
    spare_args = []
    current_func = func

    class_context = None
    result = None
    for p in path_components:
        if current_func in func_to_type_map:
            class_context = func_to_type_map[current_func]

        # If we have a class context then look at the next part of the
        # path as if could be instance method that we need to apply
        if class_context in instance_path_map \
          and (method != 'POST' or class_context not in class_to_create_methods):
            # If we have a match then apply the current function so we
            # can call the next method on the returned instance

            if p in instance_path_map[class_context] and \
               ( method == 'DELETE' and p not in class_to_delete_methods[class_context] or \
                 method != 'DELETE' ):

                result = current_func(*pargs)

                if not result:
                    return (None, None)

                pargs = [result]
                current_func = instance_path_map[class_context][p]

                continue


        tmp_type = func_to_type_map.get(current_func, None)
        num_args = len(inspect.getargspec(current_func)[0])

        if (not tmp_type or (p not in class_to_create_methods[tmp_type] \
           and p not in instance_path_map[tmp_type])) and len(pargs) < num_args:
            pargs.append(p)
        else:
            spare_args.append(p)

    if current_func:
        # Fill in the parameter with anything we can extract
        # from the query string
        paramloc = func_to_wrapper[current_func].paramloc

        if paramloc and (paramloc == 'query' or 'query' in paramloc):
            pargs += extract_query_args(current_func, pargs)

        result = current_func(*pargs)

    return (result, spare_args)

def find_update_method(cls, member):
    if cls in class_to_update_methods:
        methods = class_to_update_methods[cls]
        if member in methods:
            return methods[member]

    return None

# function to convert object to JSON
def to_json(o):
    if isinstance(o, uuid.UUID):
        return str(o)
    else:
        d = o.__dict__

        for k in d.keys():
            if k.startswith('_'):
                del d[k]
        return d

class wrapper(object):
    def __init__(self, method, path=None, datatype=None, wrapper=None, paramloc=None):
        self.path = path
        self.method = method
        self.datatype = datatype
        self.paramloc = paramloc

        def its_a_wrap(func, *args, **kwargs):
            (resource, spare_args) = resolve_resource(request.method, func, *args, **kwargs)

            if request.method == 'GET':
                if not isinstance(resource, str):
                    response.content_type = "application/json"

                    if resource:
                        resource = json.dumps(resource, default=to_json)
                    else:
                        resource = HTTPResponse(status=404, body="Resource not found")

                return resource
            elif request.method == 'PUT':

                if resource:
                    for (member, value) in request.json.iteritems():
                        cls = resource.__class__.__name__
                        if cls in class_to_update_methods:
                            methods = class_to_update_methods[cls]
                            if member in methods:
                                update_func = methods[member]
                                pargs = [resource, value]
                                update_func(*pargs)
                # This is not a decorated instance method so just try and pull
                # the parameters out of the json body
                else:
                    func(**request.json)
            elif request.method == 'POST':
                if resource:
                    if len(spare_args) == 1:
                        path = spare_args[0]
                        cls = resource.__class__.__name__
                        if cls in class_to_create_methods:
                            methods = class_to_create_methods[cls]
                            if path in methods:
                                create_func = methods[path]
                                kwargs = request.json
                                create_func(resource, **kwargs)
                    else:
                        print >> sys.stderr, "POST request with invalid spare args: %s" % str(spare_args)
                else:
                    func(**request.json)
            elif request.method == 'DELETE':
                if resource:
                    if len(spare_args) >= 1:
                        path = spare_args[0]
                        cls = resource.__class__.__name__
                        if cls in class_to_delete_methods:
                            methods = class_to_delete_methods[cls]
                            if path in methods:
                                delete_func = methods[path]
                                delete_func(resource, *spare_args[1:])
                else:
                    func(*spare_args)

        if not wrapper:
            self.wrapper = its_a_wrap
        else:
            self.wrapper = wrapper

    def __call__(self, func):
        self.func = func
        if self.path:
            mount_point = self.path
        else:
            mount_point = '/%s' % func.__name__

        if self.method == 'GET' and self.datatype:
            func_to_type_map[func] = self.datatype
        elif self.method == 'PUT':
            class_name = inspect.getouterframes(inspect.currentframe())[1][3]
            func_args = inspect.getargspec(func)[0]
            methods = {}
            if class_name in class_to_update_methods:
                methods = class_to_update_methods[class_name]
            else:
                class_to_update_methods[class_name] = methods

            methods[func_args[1]] = func
        elif self.method == 'POST':
            class_name = inspect.getouterframes(inspect.currentframe())[1][3]
            methods = {}
            if class_name in class_to_create_methods:
                methods = class_to_create_methods[class_name]
            else:
                class_to_create_methods[class_name] = methods

            methods[self.path] = func
        elif self.method == 'DELETE':
            class_name = inspect.getouterframes(inspect.currentframe())[1][3]
            methods = {}
            if class_name in class_to_delete_methods:
                methods = class_to_delete_methods[class_name]
            else:
                class_to_delete_methods[class_name] = methods
            methods[self.path] = func

        self.wrap = functools.partial(self.wrapper, func)

        if not mount_point.startswith('/') and self.method == 'GET':
            func_args = inspect.getargspec(func)[0]
            first_arg =  func_args[0]

            if first_arg != 'self':
                raise Exception("paths that don't start with / must be class methods")

            class_name = inspect.getouterframes(inspect.currentframe())[1][3]

            paths_to_funcs = {}
            if class_name in instance_path_map:
                paths_to_funcs = instance_path_map[class_name]
            else:
                instance_path_map[class_name] = paths_to_funcs

            paths_to_funcs[mount_point] =  func

        else:
            if mount_point.startswith('/'):

                # We bind any GET endpoint to all HTTP methods. If there are other
                # endpoint that are not GET endpoints already bound we need to rebind
                # then so the appear in the right order in the routing stack. This is
                # is what is going on below.
                functions = mount_points_to_functions.get(mount_point, set())

                if self.method == 'GET':

                    mounted = False

                    for f in functions:
                        if f.method == 'GET':
                            mounted = True
                            break

                    if not mounted:
                        route(mount_point + '<path:re:.*>', ['GET', 'PUT', 'POST', 'DELETE'], self.wrap)
                        for f  in functions:
                            if f.method != 'GET':
                                if self.path:
                                    path = self.path
                                else:
                                    path = '/%s' % f.func.__name__
                                route(path + '<path:re:.*>', f.method, f.wrap)
                    else:
                        print >> sys.stderr, "GET method already mounted at %s" % mount_point
                else:
                    mounted = False
                    for f in functions:
                        if f.method == self.method:
                            mounted = True
                            break
                    if not mounted:
                        route(mount_point + '<path:re:.*>', self.method, self.wrap)
                    else:
                        print >> sys.stderr, "%s method already mounted at %s" % (self.method, mount_point)

                if len(functions) == 0:
                    mount_points_to_functions[mount_point] = functions

                functions.add(self)

        # TODO clean this up can we remove this mapping
        func_to_wrapper[func] = self

        return func


# CRUD

class create(wrapper):
    def __init__(self, path=None):
        def look_in_body(func, *args, **kwargs):
            content = json.loads(request.body.getvalue())

            pargs = []
            func_args = inspect.getargspec(func)[0]
            for arg in func_args:
                pargs.append(content[arg])

            result = func(*pargs)
            if not isinstance(result, str):
                response.content_type = "application/json"

                result = json.dumps(result, default=to_json)

            return result

        super(create, self).__init__("POST", path=path, wrapper=look_in_body)

class read(wrapper):
    def __init__(self, path=None, datatype=None, paramloc='path'):
        super(read, self).__init__("GET", path, datatype, None, paramloc)

class update(wrapper):
    def __init__(self, path=None):
        super(update, self).__init__("PUT", path=path)

class delete(wrapper):
    def __init__(self, path=None):
        super(delete, self).__init__("DELETE", path=path)

def args_to_path(func):
    path = ""
    func_args = inspect.getargspec(func)[0]

    for arg in func_args:
        if arg == 'self':
            continue
        if len(path) > 0 and not path.endswith('/'):
            path += '/'

        path += "<%s>" % arg

    return path

def args_to_query(func):
    query = ""
    func_args = inspect.getargspec(func)[0]

    for arg in func_args:
        if arg == 'self':
            continue

        if len(query) > 0:
            query += '&'

        query += "%s=<%s>" % (arg, arg)

    return query



put_endpoints = {}
post_endpoints = {}
delete_endpoints = {}

def endpoint_to_doc(current_path, class_name):
    doc = ""
    for mount_point, method in instance_path_map[class_name].iteritems():
        path = "%s/%s" % (current_path, mount_point)

        arg_path = args_to_path(method)
        if arg_path:
            path += "/%s" % arg_path

        docs = inspect.getdoc(method)

        if docs:
            doc += "%s\n" % docs

        paramloc = func_to_wrapper[method].paramloc

        if paramloc and (paramloc == 'path' or 'path' in paramloc):
            doc += "GET %s\n" % path

        if paramloc and (paramloc == 'query' or 'query' in paramloc):
            query = args_to_query(method)
            doc += "GET %s/%s?%s\n" % (current_path, mount_point, query)

        if method in func_to_wrapper:
            if func_to_wrapper[method].datatype:
                doc += endpoint_to_doc(path, func_to_wrapper[method].datatype)

    for mount_point, method in class_to_update_methods[class_name].iteritems():

        if current_path not in put_endpoints:
            put_endpoints[current_path] = set()

        func_args = inspect.getargspec(method)[0]
        for arg in func_args:
            if arg == 'self':
                continue
            put_endpoints[current_path].add(arg)

    for mount_point, method in class_to_create_methods[class_name].iteritems():
        post_point = '%s/%s' % (current_path, mount_point)

        if current_path not in post_endpoints:
            post_endpoints[post_point] = set()

        func_args = inspect.getargspec(method)[0]
        for arg in func_args:
            if arg == 'self':
                continue
            post_endpoints[post_point].add(arg)

    for mount_point, method in class_to_delete_methods[class_name].iteritems():
        delete_point = '%s/%s' % (current_path, mount_point)
        args = args_to_path(method)

        if args:
            delete_point += '/%s' % args

        doc += 'DELETE %s\n' % delete_point
        #doc += "PUT %s/%s" % (current_path, mount_point)
        #doc += "/%s" % args_to_path(method)

    return doc

def dump_body(body_dict, level=4):
    body = ""
    for l in str(json.dumps(body_dict, indent=2)).split('\n'):
        l = l.replace('"<', '<')
        l = l.replace('>"', '>')

        body += "%s%s\n" % (" "*level, l)

    return body

def generate_doc():

    doc = "Serene generated RESTful API\n\n";

    for key, endpoints in mount_points_to_functions.iteritems():

        for endpoint in endpoints:
            # if this read/get endpoint
            if endpoint.method == 'GET':
                path = "%s/%s" % (key, args_to_path(endpoint.func))
                doc += "GET %s\n" % path

                # if we have a datatype defined then look for other mount point that can
                # be combined with this one.
                if endpoint.datatype:
                    class_name = endpoint.datatype
                    doc += endpoint_to_doc(path, class_name)
            elif endpoint.method == 'POST':
                doc += "POST %s\n" % key
                func_args = inspect.getargspec(endpoint.func)[0]

                body = {}

                for p in func_args:
                    body[p] = "<%s>" % p

                doc += "\n  Message Body:\n"
                doc += dump_body(body)
            elif endpoint.method == 'DELETE':
                doc += "DELETE %s" % key
                arg_path = args_to_path(endpoint.func)
                if arg_path:
                    doc += "/%s" % arg_path
                doc +='\n'

    for path, parameters in put_endpoints.iteritems():
        body = {}

        for p in parameters:
            body[p] = "<%s>" % p

        doc += "PUT %s\n" % path

        doc += "\n  Message Body:\n"
        doc += dump_body(body)

    for path, parameters in post_endpoints.iteritems():
        body = {}

        for p in parameters:
            body[p] = "<%s>" % p

        doc += "POST %s\n" % path

        doc += "\n  Message Body:\n"
        doc += dump_body(body)

    return doc
