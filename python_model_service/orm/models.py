"""
SQLAlchemy models for the database
"""
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy import UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from python_model_service.orm.guid import GUID
from python_model_service.orm import Base
from python_model_service.orm.history_meta import Versioned


class Individual(Base, Versioned):
    """
    SQLAlchemy class/table representing an individual
    """
    __tablename__ = 'individuals'
    id = Column(GUID(), primary_key=True)
    description = Column(String(100))
    created = Column(DateTime())
    updated = Column(DateTime())
#    calls = relationship("Call", back_populates="individual")


class Variant(Base, Versioned):
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
    updated = Column(DateTime())
#    calls = relationship("Call", back_populates="variant")
    # chromosome, start, ref, alt _uniquely_ specifies a short variant
    __table_args__ = (
        UniqueConstraint("chromosome", "start", "ref", "alt"),
    )


class Call(Base, Versioned):
    """
    SQLAlchemy class/table representing Calls
    """
    __tablename__ = 'calls'
    id = Column(GUID(), primary_key=True)
    individual_id = Column(GUID(), ForeignKey('individuals.id'))
    individual = relationship("Individual", backref="calls")
    variant_id = Column(GUID(), ForeignKey('variants.id'))
    variant = relationship("Variant", backref="calls")
    genotype = Column(String(20))
    fmt = Column(String(100))
    created = Column(DateTime())
    updated = Column(DateTime())
    # a call is a _unique_ relationship between a variant and an individual
    __table_args__ = (
        UniqueConstraint("variant_id", "individual_id"),
    )