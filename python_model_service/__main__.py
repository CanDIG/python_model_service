#!/usr/bin/env python3
"""
Driver program for service
"""
import sys
import argparse
import logging
import pkg_resources
import connexion
from tornado.options import options, define

db_session = None

def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser('Run python model service')
    parser.add_argument('--database', default="./data/model_service.sqlite")
    parser.add_argument('--port', default=3000)
    parser.add_argument('--logfile', default="./log/model_service.log")
    parser.add_argument('--loglevel', choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'], default='INFO')
    args = parser.parse_args(args)

    # set up the application
    app = connexion.FlaskApp(__name__, server='tornado')
    define("dbfile", default=args.database)

    # configure logging
    numeric_loglevel = getattr(logging, args.loglevel.upper())
    log_handler = logging.FileHandler(args.logfile)
    log_handler.setLevel(numeric_loglevel)

    # add the swagger APIs
    api_def = pkg_resources.resource_filename('python_model_service', 'api/swagger.yaml')
    app.add_api(api_def, strict_validation=True, validate_responses=True)
    application = app.app

    app.run(port=args.port)


if __name__ == "__main__":
    main()
