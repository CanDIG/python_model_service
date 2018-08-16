"""
ORM module for service
"""
import os
import warnings
from sqlalchemy import event, create_engine, exc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from tornado.options import options

ORMException = SQLAlchemyError

Base = declarative_base()

_engine = None
_db_session = None


# From http://docs.sqlalchemy.org/en/latest/faq/connections.html
def add_engine_pidguard(engine):
    """Add multiprocessing guards.

    Forces a connection to be reconnected if it is detected
    as having been shared to a sub-process.

    """
    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        connection_record.info['pid'] = os.getpid()

    @event.listens_for(engine, "checkout")
    def checkout(dbapi_connection, connection_record, connection_proxy):
        pid = os.getpid()
        if connection_record.info['pid'] != pid:
            # substitute log.debug() or similar here as desired
            warnings.warn(
                "Parent process %(orig)s forked (%(newproc)s) with an open "
                "database connection, "
                "which is being discarded and recreated." %
                {"newproc": pid, "orig": connection_record.info['pid']})
            connection_record.connection = connection_proxy.connection = None
            raise exc.DisconnectionError(
                "Connection record belongs to pid %s, "
                "attempting to check out in pid %s" %
                (connection_record.info['pid'], pid)
            )


def init_db(uri=None):
    """
    Creates the DB engine + ORM
    """
    global _engine
    import python_model_service.orm.models # noqa401
    if not uri:
        uri = 'sqlite:///' + options.dbfile
    _engine = create_engine(uri, convert_unicode=True)
    add_engine_pidguard(_engine)
    Base.metadata.create_all(bind=_engine)


def get_session(**kwargs):
    """
    Start the database session
    """
    global _db_session
    if not _db_session:
        _db_session = scoped_session(sessionmaker(autocommit=False,
                                                  autoflush=False,
                                                  bind=_engine, **kwargs))
        Base.query = _db_session.query_property()
    return _db_session


def dump(obj, nonulls=False):
    """
    Generate dictionary  of fields without SQLAlchemy internal fields
    & relationships
    """
    rels = ["calls", "variant", "individual"]
    if not nonulls:
        return dict([(k, v) for k, v in vars(obj).items()
                     if not k.startswith('_') and k not in rels])

    return dict([(k, v) for k, v in vars(obj).items()
                 if not k.startswith('_') and k not in rels and v])
