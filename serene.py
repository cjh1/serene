from bottle import route, run, request, abort
import inspect
import json

@route('/widgets/<id:int>', method='GET')
def get_widget(id):
    return {'id': id}

@route('/widgets', method='POST')
def post_widget():
    print request.json

class wrapper(object):
    def __init__(self, method, path=None):
        self.path = path
        self.method = method

    def __call__(self, func):
        print '__call__'

        print type(func)

        (func_args, varargs, keywords, locals) = inspect.getargspec(func)

        def its_a_wrap(*args, **kwargs):

            print request.query
            print args
            pargs = kwargs['path'].split('/')
            pargs = filter(None, pargs)

            for arg in func_args[len(pargs):]:
                value = request.query[arg]
                if ',' in value:
                    value = value.split(',')

                pargs.append(value)

            return func(*pargs)

        print self.path

        if self.path:
            mount_point = self.path
        else:
            mount_point = '/%s' % func.__name__

        print "mount: " + mount_point

        route(mount_point + '<path:re:.*>' , self.method, its_a_wrap)


        return func


# CRUD

class create(wrapper):
    def __init__(self, path=None):
        super(create, self).__init__("POST", path)

    def __call__(self, func):

        (func_args, varargs, keywords, locals) = inspect.getargspec(func)

        def its_a_wrap(*args, **kwargs):

            content = json.loads(request.body.getvalue())

            pargs = []

            for arg in func_args:
                pargs.append(content[arg])

            return func(*pargs)

        if self.path:
            mount_point = self.path
        else:
            mount_point = '/%s' % func.__name__

        route(mount_point + '<path:re:.*>' , self.method, its_a_wrap)


        return func


class read(wrapper):
    def __init__(self, path=None):
        super(read, self).__init__("GET", path)


def update(func):
  return func

def delete(func):
  return func