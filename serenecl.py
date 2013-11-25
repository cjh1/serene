import serene
import argparse
import importlib
import sys

def main():
    parser = argparse.ArgumentParser(description='Serene command line.')
    parser.add_argument('module', metavar='module', type=str,
                   help='the module to process')
    parser.add_argument('--host', dest='host',  default='localhost',
                    help='host name')
    parser.add_argument('--port', dest='port', default=8082, help='port')
    parser.add_argument('--server', action='store_const', const='server', dest='action')
    parser.add_argument('--doc', action='store_const', const='doc', dest='action')

    args = parser.parse_args()

    if not args.action:
        print >> sys.stderr, "One of --server or --doc must be given"
        return

    importlib.import_module(args.module)

    if args.action == 'server':
        from bottle import run
        run(reloader=True, host=args.host , port=args.port)
    elif args.action == 'doc':
        print serene.generate_doc()

if __name__ == "__main__":
    main()
