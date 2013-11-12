from bottle import route, run, request, response, abort
import inspect
import json
import functools
import traceback
from collections import defaultdict
import json

@route('/widgets/<id:int>', method='GET')
def get_widget(id):
    return {'id': id}

@route('/widgets', method='POST')
def post_widget():
    print request.json

def tree():
    return defaultdict(tree)

instance_path_map = tree()
func_to_type_map = {}
class_to_update_methods = tree()

def extract_query_args(func, pargs):
    (func_args, varargs, keywords, locals) = inspect.getargspec(func)

    for arg in func_args[len(pargs):]:
        if arg in request.query:
            pargs.append(arg)

    return pargs

def resolve_resource(func, *args, **kwargs):

    # If the function doesn't resolve to an instance then return None, so the
    # caller knows
    if not func in func_to_type_map:
        return None

    print "resolve_resource: " + str(kwargs)

    path_components = kwargs['path'].split('/')
    path_components = filter(None, path_components)

    pargs = []
    current_func = func

    class_context = None
    result = None
    for p in path_components:
        print p
        if current_func in func_to_type_map:
            class_context = func_to_type_map[current_func]

        # If we have a class context then look at the next part of the
        # path as if could be instance method that we need to apply
        if class_context in instance_path_map:
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

        pargs.append(p)

    print "current_func: " + current_func.__name__
    print pargs

    if current_func:
        result = current_func(*pargs)

    return result

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
            print kwargs
            resource = resolve_resource(func, *args, **kwargs)

            print 'its_a_wrap'
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

        if not wrapper:
            self.wrapper = its_a_wrap
        else:
            self.wrapper = wrapper

    def __call__(self, func):

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

            print class_to_update_methods

        wrap = functools.partial(self.wrapper, func)

        if not mount_point.startswith('/'):
            (func_args, varargs, keywords, locals) = inspect.getargspec(func)
            first_arg =  func_args[0]

            if first_arg != 'self':
                raise Exception("paths that don't start with / must be class methods")

            class_name = inspect.getouterframes(inspect.currentframe())[1][3]
            instance_path_map[class_name] = {mount_point: func}
        else:
            if self.method == 'POST' or self.method == 'DELETE':
                route(mount_point + '<path:re:.*>' , self.method, wrap)
            else:
                #print "mounting: " + mount_point
                route(mount_point + '<path:re:.*>', ['GET', 'PUT'], wrap)

        print func

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
