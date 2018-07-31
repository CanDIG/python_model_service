#!/usr/bin/env python3
# pylint: disable=invalid-name
"""
Front end of Individual/Variant/Call API example
"""
import datetime
import logging
import uuid

from connexion import NoContent

from sqlalchemy import and_
import python_model_service.orm as orm



def get_variants(chromosome, start, end):
    """
    Return all variants between [chrom, start) and (chrom, end]
    """
    db_session = orm.get_session()
    q = db_session.query(orm.Variant)
    q = q.filter_by(chromosome=chromosome).filter(and_(start >= start, start <= end))
    return [orm.dump(p) for p in q]


def get_individuals():
    """
    Return all individuals
    """
    db_session = orm.get_session()
    q = db_session.query(orm.Individual)
    return [orm.dump(p) for p in q.all()], 200


def get_calls():
    """
    Return all calls
    """
    db_session = orm.get_session()
    q = db_session.query(orm.Call)
    return [orm.dump(p) for p in q.all()], 200


def post_variant(variant):
    """
    Add a new variant
    """
    db_session = orm.get_session()
    vid = variant['id'] if 'id' in variant else None
    if vid is not None:
        if db_session.query(orm.Variant).filter(orm.Variant.id == vid).one_or_none():
            logging.info('Attempting to update existing variant %d..', vid)
            return NoContent, 405
    else:
        variant['id'] = uuid.uuid1()

    logging.info('Creating variant...')
    variant['created'] = datetime.datetime.utcnow()
    db_session.add(orm.Variant(**variant))
    db_session.commit()
    return NoContent, 201


def post_individual(individual):
    """
    Add a new individual
    """
    db_session = orm.get_session()
    iid = individual['id'] if 'id' in individual else None
    if iid is not None:
        if db_session.query(orm.Individual).filter(orm.Individual.id == iid).one_or_none():
            logging.info('Attempting to update individual %d..', iid)
            return NoContent, 405
    else:
        individual['id'] = uuid.uuid1()

    logging.info('Creating individual...')
    individual['created'] = datetime.datetime.utcnow()
    db_session.add(orm.Individual(**individual))
    db_session.commit()
    return NoContent, 201


def post_call(call):
    """
    Add a new call
    """
    db_session = orm.get_session()
    cid = call['id'] if 'id' in call else None
    if cid is not None:
        if db_session.query(orm.Call).filter(orm.Call.id == cid).one_or_none():
            logging.info('Attempting to update call %d..', cid)
            return NoContent, 405
    else:
        call['id'] = uuid.uuid1()

    call['created'] = datetime.datetime.utcnow()
    db_session.add(orm.Call(**call))
    db_session.commit()
    logging.info('Creating call...' + str(call))
    return NoContent, 201


def get_variants_by_individual(individual_id):
    """
    Return variants that have been called in an individual
    """
    db_session = orm.get_session()
    ind_id = individual_id
    ind = db_session.query(orm.Individual).filter(orm.Individual.id == ind_id).one_or_none()
    if not ind:
        return [], 404

    variants = [call.variant for call in ind.calls if call.variant is not None]
    return [orm.dump(v) for v in variants], 200


def get_individuals_by_variant(variant_id):
    """
    Return variants that have been called in an individual
    """
    db_session = orm.get_session()
    var_id = variant_id
    var = db_session.query(orm.Variant).filter(orm.Variant.id == var_id).one_or_none()
    if not var:
        return [], 404

    individuals = [call.individual for call in var.calls if call.individual is not None]
    return [orm.dump(i) for i in individuals], 200
