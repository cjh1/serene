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

instance_path_map = {}

class wrapper(object):
    def __init__(self, method, path=None, wrapper=None):
        self.path = path
        self.method = method

        def its_a_wrap(func, *args, **kwargs):
            print func
            print inspect.getargspec(func)
            print request.query
            print args
            print kwargs
            path_components = kwargs['path'].split('/')
            path_components = filter(None, path_components)

            pargs = []
            current_func = func

            # Tuples (function, pargs)
            call_sequence = []

            for p in path_components:
                print "p: " + p
                if p in instance_path_map:
                    call_sequence.append((current_func, pargs))
                    current_func = instance_path_map[p]
                    pargs = []
                else:
                    pargs.append(p)

            # add the final call
            if current_func:
                call_sequence.append((current_func, pargs))

            result = None
            try:
                for (f, args) in call_sequence:
                    if result:
                        args.insert(0, result)
                    result = f(*args)
            except:
                print traceback.format_exc()

#             (func_args, varargs, keywords, locals) = inspect.getargspec(func)
#             for arg in func_args[len(pargs):]:
#                 print arg
#                 value = request.query[arg]
#                 if ',' in value:
#                     value = value.split(',')
#
#                 pargs.append(value)

            print "returning ... " + str(result)

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

        print func.__name__
        print "mount: " + mount_point

        wrap = functools.partial(self.wrapper, func)

        if not mount_point.startswith('/'):
            instance_path_map[mount_point] = func
        else:
            route(mount_point + '<path:re:.*>' , self.method, wrap)

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
    def __init__(self, path=None, selfish=None):
        super(read, self).__init__("GET", path)

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
