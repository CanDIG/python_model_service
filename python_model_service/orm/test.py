"""
Tests for ORM module
"""
import os
import uuid

import pytest

from python_model_service.orm import dump
from python_model_service.orm.models import Individual, Variant, Call, get_session


def are_equivalent(ormobj1, ormobj2):
    """
    Are dict representations of two objects equal?
    """
    return dump(ormobj1, nonulls=True) == dump(ormobj2, nonulls=True)


@pytest.fixture(scope="module")
def simple_db(db_filename="ormtest.db"):  # pylint: disable=too-many-locals
    """
    Create a DB with a small number of objects for testing
    """
    # delete db if already exists
    try:
        os.remove(db_filename)
    except OSError:
        pass

    session = get_session('sqlite:///'+db_filename, expire_on_commit=False)

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

    session.expunge_all()
    session.close()
    return individuals, variants, calls, db_filename


def test_search_calls(simple_db):
    """
    Perform simple call searches on the DB fixture
    """
    _, _, calls, dbname = simple_db
    db_session = get_session('sqlite:///'+dbname)

    # Test simple call queries
    # By ID:
    for call in calls:
        callquery = db_session.query(Call).filter(Call.id == call.id).all()
        assert len(callquery) == 1
        assert are_equivalent(callquery[0], call)

    # By individual + variant IDs
    for call in calls:
        callquery = db_session.query(Call).\
                    filter_by(individual_id=call.individual_id, variant_id=call.variant_id).all()
        assert len(callquery) == 1
        assert are_equivalent(callquery[0], call)

    db_session.close()


def test_search_variants(simple_db):
    """
    Perform simple variant searches on the DB fixture
    """
    _, variants, _, dbname = simple_db
    db_session = get_session('sqlite:///'+dbname)

    # Test simple variant queries
    # By ID:
    for var in variants:
        varquery = db_session.query(Variant).filter(Variant.id == var.id).all()
        assert len(varquery) == 1
        assert are_equivalent(varquery[0], var)

    # By chrom/start/ref/alt
    for var in variants:
        varquery = db_session.query(Variant).\
                    filter_by(chromosome=var.chromosome, start=var.start,
                              ref=var.ref, alt=var.alt).all()
        assert len(varquery) == 1
        assert are_equivalent(varquery[0], var)

    db_session.close()


def test_search_individuals(simple_db):
    """
    Perform simple individual searches on the DB fixture
    """
    inds, _, _, dbname = simple_db
    db_session = get_session('sqlite:///'+dbname)

    # Test simple individual queries
    # By ID:
    for ind in inds:
        indquery = db_session.query(Individual).filter(Individual.id == ind.id).all()
        assert len(indquery) == 1
        assert are_equivalent(indquery[0], ind)

    db_session.close()


def test_relationships(simple_db):
    """
    Test the individual <-> call <-> variant relationship
    """
    inds, variants, calls, dbname = simple_db
    db_session = get_session('sqlite:///'+dbname)

    # note: currenly only testing relationship outwards from call
    # TODO: add testing starting from individual and variant
    for call in calls:
        ormcalls = db_session.query(Call).filter_by(id=call.id).all()
        assert len(ormcalls) == 1
        ormcall = ormcalls[0]

        assert ormcall.variant.id == call.variant_id
        calledvar = [var for var in variants if var.id == call.variant_id][0]
        assert are_equivalent(ormcall.variant, calledvar)

        assert ormcall.individual.id == call.individual_id
        calledind = [ind for ind in inds if ind.id == call.individual_id][0]
        assert are_equivalent(ormcall.individual, calledind)

    db_session.close()


if __name__ == "__main__":
    test_search_calls(simple_db)
    test_search_variants(simple_db)
    test_search_individuals(simple_db)
    test_relationships(simple_db)
