from bottle import route, run, request, abort
import inspect

@route('/widgets/<id:int>', method='GET')
def get_widget(id):
    return {'id': id}

@route('/widgets', method='POST')
def post_widget():
    print request.json

# CRUD
class read(object):
    def __init__(self, path=None):
        print 'here'
        self.path = path

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


        if self.path:
            mount_point = self.path
        else:
            mount_point = '/%s' % func.__name__

        print "mount: " + mount_point

        route(mount_point + '/<path:re:.*>' , 'GET', its_a_wrap)


        return func


def update(func):
  return func

def delete(func):
  return func