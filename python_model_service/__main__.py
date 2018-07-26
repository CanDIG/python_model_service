import sys
import argparse
import orm
import logging
import connexion

def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser('Run python model service')
    parser.add_argument('--database', default="./data/developments.sqlite")
    parser.add_argument('--port', default=3000)
    args = parser.parse_args(args)

    db_session = orm.init_db('sqlite3:///'+args.database)
    app = connexion.FlaskApp(__name__)
    app.add_api('api/swagger.yaml')

    application = app.app

    @application.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    app.run(port=args.port)
    try:
        db_session.remove()
    except:
        pass


if __name__ == "__main__":
    main()
