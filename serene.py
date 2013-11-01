from bottle import route, run, request, abort
import inspect
import json
import functools

@route('/widgets/<id:int>', method='GET')
def get_widget(id):
    return {'id': id}

@route('/widgets', method='POST')
def post_widget():
    print request.json

class wrapper(object):
    def __init__(self, method, path=None, wrapper=None):
        self.path = path
        self.method = method

        def its_a_wrap(func, *args, **kwargs):
            print func
            print request.query
            print args
            print kwargs
            pargs = kwargs['path'].split('/')
            pargs = filter(None, pargs)


            (func_args, varargs, keywords, locals) = inspect.getargspec(func)
            for arg in func_args[len(pargs):]:
                value = request.query[arg]
                if ',' in value:
                    value = value.split(',')

                pargs.append(value)

            return func(*pargs)

        if not wrapper:
            self.wrapper = its_a_wrap
        else:
            self.wrapper = wrapper

    def __call__(self, func):

        if self.path:
            mount_point = self.path
        else:
            mount_point = '/%s' % func.__name__

        print "mount: " + mount_point

        wrap = functools.partial(self.wrapper, func)

        route(mount_point + '<path:re:.*>' , self.method, wrap)


        return func


# CRUD

class create(wrapper):
    def __init__(self, path=None):
        def its_a_wrap(func, *args, **kwargs):
            content = json.loads(request.body.getvalue())

            pargs = []
            (func_args, varargs, keywords, locals) = inspect.getargspec(func)
            for arg in func_args:
                pargs.append(content[arg])

            return func(*pargs)

        super(create, self).__init__("POST", path, its_a_wrap)


class read(wrapper):
    def __init__(self, path=None):
        super(read, self).__init__("GET", path)


def update(func):
  return func

def delete(func):
  return func