# pylint: disable=invalid-name
# pylint: disable=C0301
"""
Front end of Individual/Variant/Call API example
"""
import datetime
import uuid

from sqlalchemy import and_
from python_model_service import orm
import python_model_service.orm.models
from python_model_service.api.logging import apilog, logger
from python_model_service.api.logging import structured_log as struct_log
from python_model_service.api.models import Error


def report_search_failed(typename, exception, **kwargs):
    report = typename + ' search failed'
    message = 'Internal error searching for '+typename+'s'
    logger.error(struct_log(action=report, exception=str(exception), kwargs))
    return Error(message=message, code=500)


@apilog
def get_variants(chromosome, start, end):
    """
    Return all variants between [chrom, start) and (chrom, end]
    """
    db_session = python_model_service.orm.models.get_session()
    try:
        q = db_session.query(python_model_service.orm.models.Variant).filter_by(chromosome=chromosome).filter(and_(start >= start, start <= end)) # noqa501
    except orm.ORMException as e:
        err = report_search_failed('variant', e, chromosome=chromosome, start=start, end=end)
        return err, 500

    return [orm.dump(p) for p in q], 200


@apilog
def get_one_variant(variant_id):
    """
    Return single variant object
    """
    db_session = python_model_service.orm.models.get_session()
    vid = variant_id
    try:
        q = db_session.query(python_model_service.orm.models.Variant).filter(
            python_model_service.orm.models.Variant.id == vid).one_or_none()  # noqa501
    except orm.ORMException as e:
        err = report_search_failed('variant', e, var_id=str(vid))
        return err, 500

    if not q:
        err = Error(message="No variant found: "+str(vid), code=404)
        return err, 404

    return orm.dump(q), 200


@apilog
def get_individuals():
    """
    Return all individuals
    """
    db_session = python_model_service.orm.models.get_session()
    logger = logging.getLogger('python_model_service')
    try:
        q = db_session.query(python_model_service.orm.models.Individual)
    except orm.ORMException as e:
        err = Error(message="DB error listing individuals", code=500)
        logger.error(struct_log(action='individual listing failed',
                                exception=str(e)))
        return err, 500

    return [orm.dump(p) for p in q.all()], 200


@apilog
def get_one_individual(individual_id):
    """
    Return single individual object
    """
    iid = individual_id
    db_session = python_model_service.orm.models.get_session()
    try:
        q = db_session.query(python_model_service.orm.models.Individual).filter(
            python_model_service.orm.models.Individual.id == iid).one_or_none()  # noqa501
    except orm.ORMException as e:
        err = report_search_failed('individual', e, ind_id=str(iid))
        return err, 500

    if not q:
        err = Error(message="No individual found: "+str(iid), code=404)
        return err, 404

    return orm.dump(q), 200


@apilog
def get_calls():
    """
    Return all calls
    """
    db_session = python_model_service.orm.models.get_session()
    try:
        q = db_session.query(python_model_service.orm.models.Call)
    except orm.ORMException as e:
        err = report_search_failed('call', e)
        return err, 500

    return [orm.dump(p) for p in q.all()], 200


@apilog
def get_one_call(call_id):
    """
    Return single call object
    """
    cid = call_id
    db_session = python_model_service.orm.models.get_session()
    try:
        q = db_session.query(python_model_service.orm.models.Call).filter(
            python_model_service.orm.models.Call.id == cid).one_or_none()  # noqa501
    except Error as e:
        err = report_search_failed('call', e, call_id=str(cid))
        return err, 500

    if not q:
        err = Error(message="No call found: "+str(cid), code=404)
        return err, 404

    return orm.dump(q), 200


def variant_exists(db_session, id=None, chromosome=None, start=None,
                   alt=None, ref=None, **kwargs):
    """
    Check to see if variant exists, by ID if given or if by features if not
    """
    if id is not None:
        if db_session.query(python_model_service.orm.models.Variant).filter(
           python_model_service.orm.models.Variant.id == id).one_or_none():  # noqa501
            return True
    if db_session.query(python_model_service.orm.models.Variant).filter_by(chromosome=chromosome)\
       .filter(and_(python_model_service.orm.models.Variant.start == start, python_model_service.orm.models.Variant.alt == alt,
                    python_model_service.orm.models.Variant.ref == ref))\
       .one_or_none():
        return True

    return False


@apilog
def post_variant(variant):
    """
    Add a new variant
    """
    db_session = python_model_service.orm.models.get_session()

    # Does this variant already exist, by ID or by content?
    try:
        found_variant = variant_exists(db_session, **variant)
    except orm.ORMException as e:
        err = report_search_failed('variant', e, chromosome=chromosome, start=start, end=end)
        return err

    if found_variant:
        logger.error(struct_log(action='variant_post',
                                status='Attempt to update object w post',
                                **variant))
        err = Error(message="Attempt to update object with a POST", code=405)
        return err, 405

    vid = uuid.uuid1()
    variant['id'] = vid
    variant['created'] = datetime.datetime.utcnow()

    try:
        orm_variant = python_model_service.orm.models.Variant(**variant)
    except orm.ORMException as e:
        logger.error(struct_log(action='variant_conversion',
                                status='could not convert to ORM object',
                                exception=str(e), **variant))
        err = Error(message="Could not convert to ORM object", code=400)
        return err, 400

    try:
        db_session.add(orm_variant)
        db_session.commit()
    except orm.ORMException as e:
        logger.error(struct_log(action='saving variant',
                                status='could not write variant to DB',
                                exception=str(e), **variant))
        err = Error(message="Could write not convert to ORM object", code=400)
        return err, 400

    logger.info(struct_log(action='variant_created', **variant))
    return variant, 201, {'Location': '/variants/'+str(vid)}


@apilog
def post_individual(individual):
    """
    Add a new individual
    """
    db_session = python_model_service.orm.models.get_session()
    logger = logging.getLogger('python_model_service')
    iid = individual['id'] if 'id' in individual else None
    try:
        if iid is not None:
            if db_session.query(python_model_service.orm.models.Individual)\
               .filter(python_model_service.orm.models.Individual.id == iid).one_or_none():
                logger.error(struct_log(action='individual_post',
                                        status='Attempt to update w post',
                                        code=405, **individual))
                err = Error(code=405,
                            message="Attempt to update object with a POST")
    except orm.ORMException as e:
        err = Error(message="DB error searching for individual", code=500)
        logger.error(struct_log(action='DB error searching for variant',
                                exception=str(e)))
        return err

    iid = uuid.uuid1()
    individual['id'] = iid
    individual['created'] = datetime.datetime.utcnow()

    try:
        orm_ind = python_model_service.orm.models.Individual(**individual)
    except orm.ORMException as e:
        logger.error(struct_log(action='individual_conversion',
                                status='could not convert to ORM object',
                                exception=str(e), **individual))
        err = Error(message="Could not convert to ORM object", code=400)
        return err

    try:
        db_session.add(orm_ind)
        db_session.commit()
    except orm.ORMException as e:
        logger.error(struct_log(action='saving individual',
                                status='could not write individual to DB',
                                exception=str(e), **individual))
        err = Error(message="Could not write ORM object", code=400)
        return err

    logger.info(struct_log(action='individual_created',
                           ind_id=str(iid), **individual))
    return individual, 201, {'Location': '/individuals/'+str(iid)}


def call_exists(db_session, id=None, variant_id=None, individual_id=None,
                **kwargs):
    """
    Check to see if call exists, by ID if given or if by features if not
    """
    if id is not None:
        if db_session.query(python_model_service.orm.models.Call)\
           .filter(python_model_service.orm.models.Call.id == id).one_or_none():
            return True
    if db_session.query(python_model_service.orm.models.Call).filter_by(variant_id=variant_id)\
       .filter(python_model_service.orm.models.Call.individual_id == individual_id).one_or_none():
        return True

    return False


@apilog
def post_call(call):
    """
    Add a new call
    """
    db_session = python_model_service.orm.models.get_session()
    logger = logging.getLogger('python_model_service')

    try:
        found_call = call_exists(db_session, **call)
    except orm.ORMException as e:
        err = Error(message="DB error searching for call", code=500)
        logger.error(struct_log(action='DB error searching for call',
                                exception=str(e)))
        return err

    if found_call:
        logger.warning(struct_log(action='call_post',
                                  error='Attempt to update call w post',
                                  code=405,
                                  **call))
        err = Error(message="Attempt to update object with a POST", code=405)
        return err, 405

    cid = uuid.uuid1()
    call['id'] = cid
    call['created'] = datetime.datetime.utcnow()

    try:
        orm_call = python_model_service.orm.models.Call(**call)
    except orm.ORMException as e:
        logger.error(struct_log(action='call_conversion',
                                status='could not convert to ORM object',
                                exception=str(e), **call))
        err = Error(message="Could not convert to ORM object", code=400)
        return err

    try:
        db_session.add(orm_call)
        db_session.commit()
    except orm.ORMException as e:
        logger.error(struct_log(action='saving call',
                                status='could not write call to DB',
                                exception=str(e), **call))
        err = Error(message="Could not write ORM object", code=400)
        return err

    logger.info(struct_log(action='call_post', status='created', call_id=str(cid), **call))  # noqa501
    return call, 201, {'Location': '/calls/'+str(cid)}


@apilog
def get_variants_by_individual(individual_id):
    """
    Return variants that have been called in an individual
    """
    db_session = python_model_service.orm.models.get_session()
    logger = logging.getLogger('python_model_service')
    ind_id = individual_id

    try:
        ind = db_session.query(python_model_service.orm.models.Individual)\
            .filter(python_model_service.orm.models.Individual.id == ind_id)\
            .one_or_none()
    except orm.ORMException as e:
        err = Error(message="DB error searching for individual", code=500)
        logger.error(struct_log(action='DB error searching for individual',
                                exception=str(e)))
        return err

    if not ind:
        err = Error(message="No individual found: "+str(ind_id), code=404)
        return err, 404

    try:
        variants = [call.variant for call in ind.calls if call.variant]
    except orm.ORMException as e:
        err = Error(message="DB error searching for variants", code=500)
        logger.error(struct_log(action='DB error searching for variants',
                                exception=str(e)))
        return err

    return [orm.dump(v) for v in variants], 200


@apilog
def get_individuals_by_variant(variant_id):
    """
    Return variants that have been called in an individual
    """
    db_session = python_model_service.orm.models.get_session()
    logger = logging.getLogger('python_model_service')
    var_id = variant_id

    try:
        var = db_session.query(python_model_service.orm.models.Variant)\
            .filter(python_model_service.orm.models.Variant.id == var_id)\
            .one_or_none()
    except orm.ORMException as e:
        err = Error(message="DB error searching for variant", code=500)
        logger.error(struct_log(action='DB error searching for variant',
                                exception=str(e)))
        return err

    if not var:
        err = Error(message="No individual found: "+str(var_id), code=404)
        return err, 404

    try:
        individuals = [call.individual for call in var.calls
                       if call.individual is not None]
    except orm.ORMException as e:
        err = Error(message="DB error searching for individuals", code=500)
        logger.error(struct_log(action='DB error searching for individuals',
                                exception=str(e)))
        return err

    return [orm.dump(i) for i in individuals], 200
