from python_model_service.orm.models import Individual, Variant, Call, get_session
from sqlalchemy.exc import SQLAlchemyError

ORMException = SQLAlchemyError


def dump(obj, nonulls=False):
    """
    Generate dictionary  of fields without SQLAlchemy internal fields
    & relationships
    """
    rels = ["calls", "variant", "individual"]
    if not nonulls:
        return dict([(k, v) for k, v in vars(obj).items()
                     if not k.startswith('_') and k not in rels])
    else:
        return dict([(k, v) for k, v in vars(obj).items()
                     if not k.startswith('_') and k not in rels and v])


