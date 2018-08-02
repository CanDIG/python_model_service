# pylint: disable=invalid-name
"""
Front end of Individual/Variant/Call API example
"""
import datetime
import uuid
import logging

from connexion import NoContent
from sqlalchemy import and_
import python_model_service.orm as orm
from python_model_service.api.logging import apilog
from python_model_service.api.logging import structured_log as struct_log
from python_model_service.api.models import Error


@apilog
def get_variants(chromosome, start, end):
    """
    Return all variants between [chrom, start) and (chrom, end]
    """
    db_session = orm.get_session()
    q = db_session.query(orm.Variant).filter_by(chromosome=chromosome).filter(and_(start >= start, start <= end)) # noqa501
    return [orm.dump(p) for p in q], 200


@apilog
def get_one_variant(variant_id):
    """
    Return single variant object
    """
    vid = variant_id
    db_session = orm.get_session()
    q = db_session.query(orm.Variant).filter(orm.Variant.id == vid).one_or_none()  # noqa501
    if q:
        return orm.dump(q), 200
    else:
        err = Error(message="No variant found: "+str(vid), code=404)
        return err, 404


@apilog
def get_individuals():
    """
    Return all individuals
    """
    db_session = orm.get_session()
    q = db_session.query(orm.Individual)
    return [orm.dump(p) for p in q.all()], 200


@apilog
def get_one_individual(individual_id):
    """
    Return single individual object
    """
    iid = individual_id
    db_session = orm.get_session()
    q = db_session.query(orm.Individual).filter(orm.Individual.id == iid).one_or_none()  # noqa501
    if q:
        return orm.dump(q), 200
    else:
        err = Error(message="No individual found: "+str(iid), code=404)
        return err, 404


@apilog
def get_calls():
    """
    Return all calls
    """
    db_session = orm.get_session()
    q = db_session.query(orm.Call)
    return [orm.dump(p) for p in q.all()], 200


@apilog
def get_one_call(call_id):
    """
    Return single call object
    """
    cid = call_id
    db_session = orm.get_session()
    q = db_session.query(orm.Call).filter(orm.Call.id == cid).one_or_none()  # noqa501
    if q:
        return orm.dump(q), 200
    else:
        err = Error(message="No call found: "+str(cid), code=404)
        return err, 404


@apilog
def post_variant(variant):
    """
    Add a new variant
    """
    db_session = orm.get_session()
    logger = logging.getLogger('python_model_service')
    vid = variant['id'] if 'id' in variant else None

    # Does this variant already exist, by ID or by content?
    found_variant = False
    if vid is not None and db_session.query(orm.Variant).filter(orm.Variant.id == vid).one_or_none():  # noqa501
        found_variant = True
    elif db_session.query(orm.Variant)\
            .filter_by(chromosome=variant['chromosome'])\
            .filter(and_(orm.Variant.start == variant['start'],
                         orm.Variant.alt == variant['alt'],
                         orm.Variant.ref == variant['ref']))\
            .one_or_none():
        found_variant = True

    if found_variant:
        logger.warning(struct_log(action='variant_post',
                                  error='Attempt to update object w post',
                                  code=405,
                                  **variant))
        return NoContent, 405

    vid = uuid.uuid1()
    logger.info(struct_log(action='variant_created', id=str(vid), **variant))

    variant['id'] = vid
    variant['created'] = datetime.datetime.utcnow()
    db_session.add(orm.Variant(**variant))
    db_session.commit()
    return variant, 201, {'Location': '/variants/'+str(vid)}


@apilog
def post_individual(individual):
    """
    Add a new individual
    """
    db_session = orm.get_session()
    logger = logging.getLogger('python_model_service')
    iid = individual['id'] if 'id' in individual else None
    if iid is not None:
        if db_session.query(orm.Individual)\
           .filter(orm.Individual.id == iid).one_or_none():
            logger.warning(struct_log(action='individual_post',
                                      error='Attempt to update object w post',
                                      code=405,
                                      **individual))
            return NoContent, 405

    iid = uuid.uuid1()
    logger.info(struct_log(action='individual_created',
                           id=str(iid), **individual))
    individual['id'] = iid
    individual['created'] = datetime.datetime.utcnow()

    db_session.add(orm.Individual(**individual))
    db_session.commit()
    return individual, 201, {'Location': '/individuals/'+str(iid)}


@apilog
def post_call(call):
    """
    Add a new call
    """
    db_session = orm.get_session()
    logger = logging.getLogger('python_model_service')
    cid = call['id'] if 'id' in call else None
    vid = call['variant_id'] if 'variant_id' in call else None
    iid = call['individual_id'] if 'individual_id' in call else None

    found_call = False
    if cid is not None and db_session.query(orm.Call).filter(orm.Call.id == cid).one_or_none():  # noqa501
        found_call = True
    elif db_session.query(orm.Call).filter_by(variant_id = vid).filter(orm.Call.individual_id == iid).one_or_none():  # noqa501
        found_call = True

    if found_call:
        logger.warning(struct_log(action='call_post',
                                  error='Attempt to update call w post',
                                  code=405,
                                  **call))
        return NoContent, 405

    cid = uuid.uuid1()
    logger.info(struct_log(action='call_post', status='created', id=str(cid), **call))  # noqa501

    call['id'] = cid
    call['created'] = datetime.datetime.utcnow()
    db_session.add(orm.Call(**call))
    db_session.commit()
    return call, 201, {'Location': '/variants/'+str(iid)}


@apilog
def get_variants_by_individual(individual_id):
    """
    Return variants that have been called in an individual
    """
    db_session = orm.get_session()
    ind_id = individual_id
    ind = db_session.query(orm.Individual)\
        .filter(orm.Individual.id == ind_id)\
        .one_or_none()
    if not ind:
        err = Error(message="No individual found: "+str(ind_id), code=404)
        return err, 404

    variants = [call.variant for call in ind.calls if call.variant is not None]
    return [orm.dump(v) for v in variants], 200


@apilog
def get_individuals_by_variant(variant_id):
    """
    Return variants that have been called in an individual
    """
    db_session = orm.get_session()
    var_id = variant_id
    var = db_session.query(orm.Variant)\
        .filter(orm.Variant.id == var_id)\
        .one_or_none()
    if not var:
        err = Error(message="No individual found: "+str(var_id), code=404)
        return err, 404

    individuals = [call.individual for call in var.calls
                   if call.individual is not None]
    return [orm.dump(i) for i in individuals], 200
