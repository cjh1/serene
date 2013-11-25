from bottle import run
import argparse
import test

parser = argparse.ArgumentParser(description='Test server.')
parser.add_argument('--host', dest='host',  default='localhost',
                    help='host name')
parser.add_argument('--port', dest='port', default=8082, help='port')
args = parser.parse_args()

run(reloader=True, host=args.host , port=args.port)