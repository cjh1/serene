from bottle import route, run, request, response, abort
import inspect
import json
import functools
import traceback
from collections import defaultdict
import sys
import argparse
import importlib


@route('/widgets/<id:int>', method='GET')
def get_widget(id):
    return {'id': id}

@route('/widgets', method='POST')
def post_widget():
    print request.json

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

mount_points_to_function = {}

func_to_wrapper = {}

def extract_query_args(func, pargs):
    (func_args, varargs, keywords, locals) = inspect.getargspec(func)

    for arg in func_args[len(pargs):]:
        if arg in request.query:
            pargs.append(arg)

    return pargs

def resolve_resource(method, func, *args, **kwargs):
    # If the function doesn't resolve to an instance then return None, so the
    # caller knows
    if not func in func_to_type_map:
        return (None, None)

    path_components = kwargs['path'].split('/')
    path_components = filter(None, path_components)

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
            if p in instance_path_map[class_context]:
                # Fill in the parameter with anything we can extract
                # from the query string
                pargs = extract_query_args(current_func, pargs)
                result = current_func(*pargs)
                pargs = [result]
                current_func = instance_path_map[class_context][p]
                continue


        tmp_type = func_to_type_map.get(current_func, None)

        if not tmp_type or (p not in class_to_create_methods[tmp_type] and \
           p not in instance_path_map[tmp_type]):
            pargs.append(p)
        else:
            spare_args.append(p)

    if current_func:
        result = current_func(*pargs)

    return (result, spare_args)

def find_update_method(cls, member):
    if cls in class_to_update_methods:
        methods = class_to_update_methods[cls]
        if member in methods:
            return methods[member]

    return None

class wrapper(object):
    def __init__(self, method, path=None, datatype=None, wrapper=None):
        self.path = path
        self.method = method
        self.datatype = datatype

        def its_a_wrap(func, *args, **kwargs):
            (resource, spare_args) = resolve_resource(request.method, func, *args, **kwargs)

            if request.method == 'GET':
                if not isinstance(resource, str):
                    response.content_type = "application/json"
                    resource = json.dumps(resource, default=lambda o: o.__dict__)
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
            (func_args, varargs, keywords, locals) = inspect.getargspec(func)
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

        wrap = functools.partial(self.wrapper, func)

        if not mount_point.startswith('/') and self.method == 'GET':
            (func_args, varargs, keywords, locals) = inspect.getargspec(func)
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
            if self.method == 'DELETE':
                route(mount_point + '<path:re:.*>' , self.method, wrap)
            else:
                route(mount_point + '<path:re:.*>', ['GET', 'PUT', 'POST'], wrap)
            if mount_point.startswith('/'):
                mount_points_to_function[mount_point] = self

        # TODO clean this up can we remove this mapping
        func_to_wrapper[func] = self

        return func


# CRUD

class create(wrapper):
    def __init__(self, path=None):
        def look_in_body(func, *args, **kwargs):
            content = json.loads(request.body.getvalue())

            pargs = []
            (func_args, varargs, keywords, locals) = inspect.getargspec(func)
            for arg in func_args:
                pargs.append(content[arg])

            result = func(*pargs)
            if not isinstance(result, str):
                response.content_type = "application/json"
                result = json.dumps(result, default=lambda o: o.__dict__)

            return result

        super(create, self).__init__("POST", path=path, wrapper=look_in_body)

class read(wrapper):
    def __init__(self, path=None, datatype=None, selfish=None):
        super(read, self).__init__("GET", path, datatype)

class update(wrapper):
    def __init__(self, path=None):
        super(update, self).__init__("PUT", path=path)

class delete(wrapper):
    def __init__(self, path=None):
        super(delete, self).__init__("DELETE", path=path)

def args_to_path(func):
    path = ""
    (func_args, varargs, keywords, locals) = inspect.getargspec(func)
    for arg in func_args:
        if arg == 'self':
            continue
        if len(path) > 0 and not path.endswith('/'):
            path += '/'

        path += "%s/<%s>" % (arg, arg)

    return path

put_endpoints = {}
post_endpoints = {}

def endpoint_to_doc(current_path, class_name):
    doc = ""
    for mount_point, method in instance_path_map[class_name].iteritems():
        path = "%s/%s" % (current_path, mount_point)
        path += "/%s" % args_to_path(method)

        docs = inspect.getdoc(method)

        if docs:
            doc += "%s\n" % docs

        doc += "GET %s\n" % path

        if method in func_to_wrapper:
            if func_to_wrapper[method].datatype:
                doc += endpoint_to_doc(path, func_to_wrapper[method].datatype)

    for mount_point, method in class_to_update_methods[class_name].iteritems():

        if current_path not in put_endpoints:
            put_endpoints[current_path] = set()

        (func_args, varargs, keywords, locals) = inspect.getargspec(method)
        for arg in func_args:
            if arg == 'self':
                continue
            put_endpoints[current_path].add(arg)

    for mount_point, method in class_to_create_methods[class_name].iteritems():
        post_point = '%s/%s' % (current_path, mount_point)

        if current_path not in post_endpoints:
            post_endpoints[post_point] = set()

        (func_args, varargs, keywords, locals) = inspect.getargspec(method)
        for arg in func_args:
            if arg == 'self':
                continue
            post_endpoints[post_point].add(arg)



        #doc += "PUT %s/%s" % (current_path, mount_point)
        #doc += "/%s" % args_to_path(method)

    return doc

def generate_doc():

    doc = "Serene generated RESTful API\n\n";

    for key, endpoint in mount_points_to_function.iteritems():
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
            (func_args, varargs, keywords, locals) = inspect.getargspec(endpoint.func)
            body = {}

            for p in func_args:
                body[p] = "<%s>" % p

            doc += "\n  Message Body:\n"
            for l in str(json.dumps(body, indent=2)).split('\n'):
                doc += "    %s\n" % l

    for path, parameters in put_endpoints.iteritems():
        body = {}

        for p in parameters:
            body[p] = "<%s>" % p

        doc += "PUT %s\n" % path

        doc += "\n  Message Body:\n"
        for l in str(json.dumps(body, indent=2)).split('\n'):
            doc += "    %s\n" % l

    for path, parameters in post_endpoints.iteritems():
        body = {}

        for p in parameters:
            body[p] = "<%s>" % p

        doc += "POST %s\n" % path

        doc += "\n  Message Body:\n"
        for l in str(json.dumps(body, indent=2)).split('\n'):
            doc += "    %s\n" % l

    return doc
