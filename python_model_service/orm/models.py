"""
SQLAlchemy models for the database
"""
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy import UniqueConstraint, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from tornado.options import options

from python_model_service.orm.guid import GUID

Base = declarative_base()


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
    # chromosome, start, ref, alt _uniquely_ specifies a short variant
    __table_args__ = (
        UniqueConstraint("chromosome", "start", "ref", "alt"),
    )


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
    # a call is a _unique_ relationship between a variant and an individual
    __table_args__ = (
        UniqueConstraint("variant_id", "individual_id"),
    )


def get_session(uri=None, **kwargs):
    """
    Start the database session
    """
    if not uri:
        uri = 'sqlite:///' + options.dbfile
    engine = create_engine(uri, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False,
                                             bind=engine, **kwargs))
    Base.query = db_session.query_property()
    Base.metadata.create_all(bind=engine)
    return db_session