from bottle import route, run, request, abort
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

def extract_query_args(func, pargs):
    (func_args, varargs, keywords, locals) = inspect.getargspec(func)

    for arg in func_args[len(pargs):]:
        if arg in request.query:
            pargs.append(arg)

    return pargs

class wrapper(object):
    def __init__(self, method, path=None, return_type=None, wrapper=None):
        self.path = path
        self.method = method
        self.return_type = return_type

        def its_a_wrap(func, *args, **kwargs):
            print func_to_type_map
            path_components = kwargs['path'].split('/')
            path_components = filter(None, path_components)

            pargs = []
            current_func = func

            class_context = None
            result = None
            for p in path_components:
                print "p: %s" % p
                if current_func in func_to_type_map:
                    class_context = func_to_type_map[current_func]

                # If we have a class context then look at the next part of the
                # path as if could be instance method that we need to apply
                print "class_context: %s" % class_context
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
                        print "New function %s" % current_func.__name__
                        continue

                pargs.append(p)
                print "pargs: " + str(pargs)

            print "current_func: %s" % current_func.__name__
            if current_func:
                result = current_func(*pargs)


            if not isinstance(result, str):
                result = json.dumps(result, default=lambda o: o.__dict__)

            return result

        if not wrapper:
            self.wrapper = its_a_wrap
        else:
            self.wrapper = wrapper

    def __call__(self, func):

        if self.path:
            mount_point = self.path
        else:
            mount_point = '/%s' % func.__name__

        if self.return_type:
            func_to_type_map[func] = self.return_type

        wrap = functools.partial(self.wrapper, func)

        if not mount_point.startswith('/'):
            (func_args, varargs, keywords, locals) = inspect.getargspec(func)
            first_arg =  func_args[0]

            if first_arg != 'self':
                raise Exception("paths that don't start with / must be class methods")

            class_name = inspect.getouterframes(inspect.currentframe())[1][3]
            instance_path_map[class_name] = {mount_point: func}
        else:
            route(mount_point + '<path:re:.*>' , self.method, wrap)


        print str(instance_path_map)

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

            return func(*pargs)

        super(create, self).__init__("POST", path, look_in_body)

class read(wrapper):
    def __init__(self, path=None, return_type=None, selfish=None):
        super(read, self).__init__("GET", path, return_type)

class update(wrapper):
    def __init__(self, path=None):
        def look_in_body(func, *args, **kwargs):

            print kwargs

            pargs = kwargs['path'].split('/')
            pargs = filter(None, pargs)

            print pargs

            content = json.loads(request.body.getvalue())

            pargs = []
            (func_args, varargs, keywords, locals) = inspect.getargspec(func)
            for arg in func_args[len(pargs):]:
                pargs.append(content[arg])

            return func(*pargs)

        super(update, self).__init__("PUT", path, look_in_body)

class delete(wrapper):
    def __init__(self, path=None):
        super(delete, self).__init__("DELETE", path)
