"""
API Data Model definitions
From Swagger file, with python classes via Bravado
"""

import pkg_resources
import yaml
from bravado_core.spec import Spec

_API_DEF = pkg_resources.resource_filename('python_model_service',
                                           'api/swagger.yaml')
_SPEC_DICT = yaml.safe_load(open(_API_DEF, 'r'))
_SWAGGER_SPEC = Spec.from_dict(_SPEC_DICT)

Error = _SWAGGER_SPEC.definitions['Error']
Individual = _SWAGGER_SPEC.definitions['Individual']
Variant = _SWAGGER_SPEC.definitions['Variant']
Call = _SWAGGER_SPEC.definitions['Call']
