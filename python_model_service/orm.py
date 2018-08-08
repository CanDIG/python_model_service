#!/usr/bin/env python3
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments
# pylint: disable=redefined-builtin
# pylint: disable=no-else-return
"""
Database layer for Individuals/Variants/Calls API
"""
import os
import uuid
from tornado.options import options
from sqlalchemy import Column, DateTime, String, Integer, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError
import pytest

Base = declarative_base()
ORMException = SQLAlchemyError


# from SQLAlchemy Docs
# http://docs.sqlalchemy.org/en/rel_0_9/core/custom_types.html
class GUID(TypeDecorator):  # pylint: disable=abstract-method
    """Platform-independent GUID type.

    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int  # noqa # pylint: disable=no-member
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)


def dump(obj):
    """
    Generate dictionary  of fields without SQLAlchemy internal fields
    & relationships
    """
    rels = ["calls", "variant", "individual"]
    return dict([(k, v) for k, v in vars(obj).items()
                 if not k.startswith('_') and k not in rels])


class Individual(Base):
    """
    SQLAlchemy class/table representing an individual
    """
    __tablename__ = 'individuals'
    id = Column(GUID(), primary_key=True)
    description = Column(String(100))
    created = Column(DateTime())
    calls = relationship("Call", back_populates="individual")


class Variant(Base):
    """
    SQLAlchemy class/table representing a Variant
    """
    __tablename__ = 'variants'
    id = Column(GUID(), primary_key=True)
    chromosome = Column(String(10))
    start = Column(Integer)
    ref = Column(String(100))
    alt = Column(String(100))
    name = Column(String(100))
    created = Column(DateTime())
    calls = relationship("Call", back_populates="variant")


class Call(Base):
    """
    SQLAlchemy class/table representing Calls
    """
    __tablename__ = 'calls'
    id = Column(GUID(), primary_key=True)
    individual_id = Column(GUID(), ForeignKey('individuals.id'))
    individual = relationship("Individual", back_populates="calls")
    variant_id = Column(GUID(), ForeignKey('variants.id'))
    variant = relationship("Variant", back_populates="calls")
    genotype = Column(String(20))
    fmt = Column(String(100))
    created = Column(DateTime())


def get_session(uri=None):
    """
    Start the database session
    """
    if not uri:
        uri = 'sqlite:///' + options.dbfile
    engine = create_engine(uri, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False,
                                             bind=engine))
    Base.query = db_session.query_property()
    Base.metadata.create_all(bind=engine)
    return db_session


@pytest.fixture
def simple_db(db_filename="ormtest.db"):  # pylint: disable=too-many-locals
    """
    Simple ORM check
    """
    # delete db if already exists
    try:
        os.remove(db_filename)
    except OSError:
        pass

    session = get_session('sqlite:///'+db_filename)

    ind_ids = [uuid.uuid1() for _ in range(2)]
    var_ids = [uuid.uuid1() for _ in range(3)]
    call_ids = [uuid.uuid1() for _ in range(4)]

    ind1 = Individual(id=ind_ids[0], description='Subject X')
    ind2 = Individual(id=ind_ids[1], description='Subject Y')
    individuals = [ind1, ind2]

    session.add_all(individuals)
    session.commit()

    variant1 = Variant(id=var_ids[0], name='rs699', chromosome='chr1',
                       start=230710048, ref='C', alt='T')
    variant2 = Variant(id=var_ids[1], name='rs900', chromosome='chr1',
                       start=218441563, ref='A', alt='T')
    variant3 = Variant(id=var_ids[2], name='rs5714', chromosome='chr1',
                       start=53247055, ref='A', alt='G')
    variants = [variant1, variant2, variant3]

    session.add_all(variants)
    session.commit()

    call1 = Call(id=call_ids[0], individual_id=ind_ids[0],
                 variant_id=var_ids[0], genotype='0/1')
    call2 = Call(id=call_ids[1], individual_id=ind_ids[0],
                 variant_id=var_ids[1], genotype='0/0')
    call3 = Call(id=call_ids[2], individual_id=ind_ids[1],
                 variant_id=var_ids[1], genotype='1/1')
    call4 = Call(id=call_ids[3], individual_id=ind_ids[1],
                 variant_id=var_ids[2], genotype='0/1')
    calls = [call1, call2, call3, call4]

    session.add_all(calls)
    session.commit()

    print([dump(call) for call in ind2.calls])
    print([dump(call) for call in variant2.calls])

    ind1variants = [call.variant for call in ind1.calls
                    if call.variant is not None]
    print([dump(v) for v in ind1variants])

    variant2inds = [call.individual for call in variant2.calls
                    if call.individual is not None]
    print([dump(i) for i in variant2inds])

    return individuals, variants, calls


def test_orm_search_simple(db_filename="otest.db"):
    inds, variants, calls = test_orm_create_simple(db_filename)
    db_session = get_session("sqlite:///"+db_filename)


if __name__ == "__main__":
    test_orm_search_simple()
