"""
Driver program for service
"""
import sys
import argparse
import logging
import pkg_resources
import connexion
from python_model_service import orm

db_session = None

def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser('Run python model service')
    parser.add_argument('--database', default="./data/developments.sqlite")
    parser.add_argument('--port', default=3000)
    args = parser.parse_args(args)

    api_def = pkg_resources.resource_filename('python_model_service', 'api/swagger.yaml')

    db_session = orm.init_db('sqlite:///'+args.database)
    logging.basicConfig(level=logging.INFO)

    app = connexion.FlaskApp(__name__)
    app.add_api(api_def)
    application = app.app

    @application.teardown_appcontext
    def shutdown_session(exception=None):
        """
        cleanup
        """
        db_session.remove()

    app.run(port=args.port)
    try:
        db_session.remove()
    except:
        pass


if __name__ == "__main__":
    main()
