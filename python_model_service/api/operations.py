# pylint: disable=invalid-name
# pylint: disable=C0301
"""
Implement endpoints of model service
"""
import datetime
import uuid
from sqlalchemy import and_
from python_model_service import orm
from python_model_service.orm import models
from python_model_service.api.logging import apilog, logger
from python_model_service.api.logging import structured_log as struct_log
from python_model_service.api.models import Error, BASEPATH
from python_model_service.orm.models import Individual, Variant, Call


def _report_search_failed(typename, exception, **kwargs):
    """
    Generate standard log message + request error for error:
    Internal error performing search

    :param typename: name of type involved
    :param exception: exception thrown by ORM
    :param **kwargs: arbitrary keyword parameters
    :return: Connexion Error() type to return
    """
    report = typename + ' search failed'
    message = 'Internal error searching for '+typename+'s'
    logger().error(struct_log(action=report, exception=str(exception), **kwargs))
    return Error(message=message, code=500)


def _report_update_failed(typename, exception, **kwargs):
    """
    Generate standard log message + request error for error:
    Internal error performing update (PUT)

    :param typename: name of type involved
    :param exception: exception thrown by ORM
    :param **kwargs: arbitrary keyword parameters
    :return: Connexion Error() type to return
    """
    report = typename + ' updated failed'
    message = 'Internal error updating '+typename+'s'
    logger().error(struct_log(action=report, exception=str(exception), **kwargs))
    return Error(message=message, code=500)


def _report_object_exists(typename, **kwargs):
    """
    Generate standard log message + request error for warning:
    Trying to POST an object that already exists

    :param typename: name of type involved
    :param **kwargs: arbitrary keyword parameters
    :return: Connexion Error() type to return
    """
    report = typename + ': Attempt to modify with a POST'
    message = 'Attempt to modify '+typename+' with a POST'
    logger().warning(struct_log(action=report, **kwargs))
    return Error(message=message, code=405)


def _report_conversion_error(typename, exception, **kwargs):
    """
    Generate standard log message + request error for warning:
    Trying to POST an object that already exists

    :param typename: name of type involved
    :param exception: exception thrown by ORM
    :param **kwargs: arbitrary keyword parameters
    :return: Connexion Error() type to return
    """
    report = 'Could not convert '+typename+' to ORM model'
    message = typename + ': failed validation - could not convert to internal representation'
    logger().error(struct_log(action=report, exception=str(exception), **kwargs))
    return Error(message=message, code=400)


def _report_write_error(typename, exception, **kwargs):
    """
    Generate standard log message + request error for error:
    Error writing to DB

    :param typename: name of type involved
    :param exception: exception thrown by ORM
    :param **kwargs: arbitrary keyword parameters
    :return: Connexion Error() type to return
    """
    report = 'Internal error writing '+typename+' to DB'
    message = typename + ': internal error saving ORM object to DB'
    logger().error(struct_log(action=report, exception=str(exception), **kwargs))
    err = Error(message=message, code=500)
    return err


@apilog
def get_variants(chromosome, start, end):
    """
    Return all variants between [chrom, start) and (chrom, end]
    """
    db_session = orm.get_session()
    try:
        q = db_session.query(orm.models.Variant)\
            .filter(models.Variant.chromosome == chromosome)\
            .filter(and_(models.Variant.start >= start, models.Variant.start <= end))
    except orm.ORMException as e:
        err = _report_search_failed('variant', e, chromosome=chromosome, start=start, end=end)
        return err, 500

    return [orm.dump(p) for p in q], 200


@apilog
def get_one_variant(variant_id):
    """
    Return single variant object
    """
    db_session = orm.get_session()
    try:
        q = db_session.query(models.Variant).get(variant_id)
    except orm.ORMException as e:
        err = _report_search_failed('variant', e, var_id=str(variant_id))
        return err, 500

    if not q:
        err = Error(message="No variant found: "+str(variant_id), code=404)
        return err, 404

    return orm.dump(q), 200


@apilog
def get_individuals():
    """
    Return all individuals
    """
    try:
        q = Individual().query.all()
    except orm.ORMException as e:
        err = _report_search_failed('individuals', e, ind_id="all")
        return err, 500

    return [orm.dump(p) for p in q], 200


@apilog
def get_one_individual(individual_id):
    """
    Return single individual object
    """
    try:
        q = Individual().query.get(individual_id)
    except orm.ORMException as e:
        err = _report_search_failed('individual', e, ind_id=str(individual_id))
        return err, 500

    if not q:
        err = Error(message="No individual found: "+str(individual_id), code=404)
        return err, 404

    return orm.dump(q), 200


@apilog
def get_calls():
    """
    Return all calls
    """
    try:
        q = Call().query.all()
    except orm.ORMException as e:
        err = _report_search_failed('call', e, call_id='all')
        return err, 500

    return [orm.dump(p) for p in q], 200


@apilog
def get_one_call(call_id):
    """
    Return single call object
    """
    try:
        q = Call().query.get(call_id)
    except Error as e:
        err = _report_search_failed('call', e, call_id=str(call_id))
        return err, 500

    if not q:
        err = Error(message="No call found: "+str(call_id), code=404)
        return err, 404

    return orm.dump(q), 200


def variant_exists(id=None, chromosome=None,  # pylint:disable=redefined-builtin
                   start=None, alt=None, ref=None, **_kwargs):
    """
    Check to see if variant exists, by ID if given or if by features if not
    """
    if id is not None:
        if Variant().query.get(id).count() > 0:
            return True
    if Variant().query.filter(models.Variant.chromosome == chromosome)\
        .filter(and_(models.Variant.start == start,
                     models.Variant.alt == alt,
                     models.Variant.ref == ref)).count() > 0:
        return True

    return False


def call_exists(id=None, variant_id=None,  # pylint:disable=redefined-builtin
                individual_id=None, **_kwargs):
    """
    Check to see if Call exists, by ID if given or if by features if not
    """
    if id is not None:
        if Call().query.get(id).count() > 0:
            return True

    c = Call().query.filter(and_(models.Call.variant_id == variant_id,
                                 models.Call.individual_id == individual_id))\
        .count()
    return c > 0


def individual_exists(db_session, id=None, description=None, **_kwargs):  # pylint:disable=redefined-builtin
    """
    Check to see if individual exists, by ID if given or if by features if not
    """
    if id is not None:
        return db_session.query(models.Individual)\
                          .filter(models.Individual.id == id).count() > 0

    if description is not None:
        return db_session.query(models.Individual)\
                          .filter(models.Individual.description == description).count() > 0

    return False


@apilog
def post_variant(variant):
    """
    Add a new variant
    """
    db_session = orm.get_session()

    # Does this variant already exist, by ID or by content?
    try:
        found_variant = variant_exists(**variant)
    except orm.ORMException as e:
        err = _report_search_failed('variant', e, **variant)
        return err

    if found_variant:
        err = _report_object_exists('variant', **variant)
        return err, 405

    vid = uuid.uuid1()
    variant['id'] = vid
    variant['created'] = datetime.datetime.utcnow()
    variant['updated'] = variant['created']

    # convert to ORM representation
    try:
        orm_variant = models.Variant(**variant)
    except orm.ORMException as e:
        err = _report_conversion_error('variant', e, **variant)
        return err, 400

    try:
        db_session.add(orm_variant)
        db_session.commit()
    except orm.ORMException as e:
        err = _report_write_error('variant', e, **variant)
        return err, 400

    logger().info(struct_log(action='variant_created', **variant))
    return variant, 201, {'Location': BASEPATH+'/variants/'+str(vid)}


@apilog
def put_variant(variant_id, variant):
    """
    Update a single variant by variant id (in URL)
    and new Variant dict object (passed in body)
    """
    db_session = orm.get_session()
    try:
        q = db_session.query(Variant).get(variant_id)
    except orm.ORMException as e:
        err = _report_search_failed('variant', e, var_id=str(variant_id))
        return err, 500

    if not q:
        err = Error(message="No variant found: "+str(variant_id), code=404)
        return err, 404

    if 'id' in variant:
        del variant['id']
    if 'created' in variant:
        del variant['created']

    variant['updated'] = datetime.datetime.utcnow()

    try:
        row = db_session.query(Variant).filter(Variant.id == variant_id).first()
        for key in variant:
            setattr(row, key, variant[key])
        db_session.commit()
    except orm.ORMException as e:
        err = _report_update_failed('variant', e, var_id=str(variant_id))
        return err, 500

    return None, 204, {'Location': BASEPATH+'/individuals/'+str(variant_id)}


@apilog
def delete_variant(variant_id):
    """
    Delete a single call by call id (in URL)
    """
    db_session = orm.get_session()
    try:
        q = db_session.query(Variant).get(variant_id)
    except orm.ORMException as e:
        err = _report_search_failed('call', e, variant_id=str(variant_id))
        return err, 500

    if not q:
        err = Error(message="No variant found: "+str(variant_id), code=404)
        return err, 404

    try:
        row = db_session.query(Variant).filter(Variant.id == variant_id).first()
        db_session.delete(row)
        db_session.commit()
    except orm.ORMException as e:
        err = _report_update_failed('variant', e, var_id=str(variant_id))
        return err, 500

    return None, 204, {'Location': BASEPATH+'/variant/'+str(variant_id)}


@apilog
def post_individual(individual):
    """
    Add a new individual
    """
    db_session = orm.get_session()
    try:
        found_individual = individual_exists(db_session, **individual)
    except orm.ORMException as e:
        err = _report_search_failed('variant', e, **individual)
        return err

    if found_individual:
        err = _report_object_exists('individual', **individual)
        return err, 405

    iid = uuid.uuid1()
    individual['id'] = iid
    individual['created'] = datetime.datetime.utcnow()
    individual['updated'] = individual['created']

    try:
        orm_ind = orm.models.Individual(**individual)
    except orm.ORMException as e:
        err = _report_conversion_error('individual', e, **individual)
        return err, 400

    try:
        db_session.add(orm_ind)
        db_session.commit()
    except orm.ORMException as e:
        err = _report_write_error('individual', e, **individual)
        return err, 500

    logger().info(struct_log(action='individual_created',
                             ind_id=str(iid), **individual))
    return individual, 201, {'Location': BASEPATH+'/individuals/'+str(iid)}


@apilog
def put_individual(individual_id, individual):
    """
    Update a single individual by individual id (in URL)
    and new api.models.Invididual object (passed in body)
    """
    db_session = orm.get_session()
    try:
        q = db_session.query(Individual).get(individual_id)
    except orm.ORMException as e:
        err = _report_search_failed('individual', e, ind_id=str(individual_id))
        return err, 500

    if not q:
        err = Error(message="No individual found: "+str(individual_id), code=404)
        return err, 404

    if 'id' in individual:
        del individual['id']
    if 'created' in individual:
        del individual['created']

    individual['updated'] = datetime.datetime.utcnow()

    try:
        row = db_session.query(Individual).filter(Individual.id == individual_id).first()
        for key in individual:
            setattr(row, key, individual[key])
        db_session.commit()
    except orm.ORMException as e:
        err = _report_update_failed('individual', e, ind_id=str(individual_id))
        return err, 500

    return None, 204, {'Location': BASEPATH+'/individuals/'+str(individual_id)}


@apilog
def delete_individual(individual_id):
    """
    Delete a single individual by individual id (in URL)
    """
    db_session = orm.get_session()
    try:
        q = db_session.query(Individual).get(individual_id)
    except orm.ORMException as e:
        err = _report_search_failed('individual', e, ind_id=str(individual_id))
        return err, 500

    if not q:
        err = Error(message="No individual found: "+str(individual_id), code=404)
        return err, 404

    try:
        row = db_session.query(Individual).filter(Individual.id == individual_id).first()
        db_session.delete(row)
        db_session.commit()
    except orm.ORMException as e:
        err = _report_update_failed('individual', e, ind_id=str(individual_id))
        return err, 500

    return None, 204, {'Location': BASEPATH+'/individuals/'+str(individual_id)}


@apilog
def post_call(call):
    """
    Add a new call
    """
    db_session = orm.get_session()

    try:
        found_call = call_exists(**call)
    except orm.ORMException as e:
        err = _report_search_failed('call', e, **call)
        return err

    if found_call:
        err = _report_object_exists('call', **call)
        return err, 405

    cid = uuid.uuid1()
    call['id'] = cid
    call['created'] = datetime.datetime.utcnow()
    call['updated'] = call['created']

    try:
        orm_call = orm.models.Call(**call)
    except orm.ORMException as e:
        err = _report_conversion_error('call', e, **call)
        return err

    try:
        db_session.add(orm_call)
        db_session.commit()
    except orm.ORMException as e:
        err = _report_write_error('call', e, **call)
        return err

    logger().info(struct_log(action='call_post', status='created', call_id=str(cid), **call))  # noqa501
    return call, 201, {'Location': BASEPATH+'/calls/'+str(cid)}


@apilog
def put_call(call_id, call):
    """
    Update a single individual by call id (in URL)
    and new Call api dict (passed in body)
    """
    db_session = orm.get_session()
    try:
        q = db_session.query(Call).get(call_id)
    except orm.ORMException as e:
        err = _report_search_failed('call', e, call_id=str(call_id))
        return err, 500

    if not q:
        err = Error(message="No individual found: "+str(call_id), code=404)
        return err, 404

    if 'id' in call:
        del call['id']
    if 'created' in call:
        del call['created']

    call['updated'] = datetime.datetime.utcnow()

    try:
        row = db_session.query(Individual).filter(Call.id == call_id).first()
        for key in call:
            setattr(row, key, call[key])
        db_session.commit()
    except orm.ORMException as e:
        err = _report_update_failed('call', e, call_id=str(call_id))
        return err, 500

    return None, 204, {'Location': '/calls/'+str(call_id)}


def delete_call(call_id):
    """
    Delete a single call by call id (in URL)
    """
    db_session = orm.get_session()
    try:
        q = db_session.query(Call).get(call_id)
    except orm.ORMException as e:
        err = _report_search_failed('call', e, call_id=str(call_id))
        return err, 500

    if not q:
        err = Error(message="No call found: "+str(call_id), code=404)
        return err, 404

    try:
        row = db_session.query(Call).filter(Call.id == call_id).first()
        db_session.delete(row)
        db_session.commit()
    except orm.ORMException as e:
        err = _report_update_failed('call', e, call_id=str(call_id))
        return err, 500

    return None, 204, {'Location': BASEPATH+'/calls/'+str(call_id)}


@apilog
def get_variants_by_individual(individual_id):
    """
    Return variants that have been called in an individual
    """
    db_session = orm.get_session()
    ind_id = individual_id

    try:
        ind = db_session.query(orm.models.Individual)\
            .filter(orm.models.Individual.id == ind_id)\
            .one_or_none()
    except orm.ORMException as e:
        err = _report_search_failed('individual', e, individual_id=individual_id)
        return err, 500

    if not ind:
        err = Error(message="No individual found: "+str(ind_id), code=404)
        return err, 404

    try:
        variants = [call.variant for call in ind.calls if call.variant]
    except orm.ORMException as e:
        err = _report_search_failed('variants', e, by_individual_id=individual_id)
        return err, 500

    return [orm.dump(v) for v in variants], 200


@apilog
def get_individuals_by_variant(variant_id):
    """
    Return variants that have been called in an individual
    """
    db_session = orm.get_session()

    try:
        var = db_session.query(orm.models.Variant)\
            .filter(orm.models.Variant.id == variant_id)\
            .one_or_none()
    except orm.ORMException as e:
        err = _report_search_failed('variant', e, variant_id=variant_id)
        return err, 500

    if not var:
        err = Error(message="No variant found: "+str(variant_id), code=404)
        return err, 404

    try:
        individuals = [call.individual for call in var.calls
                       if call.individual is not None]
    except orm.ORMException as e:
        err = _report_search_failed('individuals', e, by_variant_id=variant_id)
        return err, 500

    return [orm.dump(i) for i in individuals], 200
