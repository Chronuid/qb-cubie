"""Validate the reviewer subset of the existing public v1 request protocol."""

import math
from pathlib import PurePath

from ..errors import invalid
from ..schema import validate
from .schema import TEXT, obj

FIELDS = {'schema_version': {'type': 'integer', 'const': 1}, 'type': {'const': 'request'},
          'benchmark': {'const': 'review_agent'}, 'phase': {'const': 'review'},
          'output_format': {'const': 'review_v1'}, 'run_id': TEXT, 'scenario_id': TEXT,
          'workspace': TEXT, 'task': TEXT,
          'criteria': {'type': 'array', 'items': TEXT, 'minItems': 1},
          'budgets': {'type': 'object', 'required': ['wall_time_seconds'],
                      'properties': {'wall_time_seconds': {'type': 'number', 'minimum': 0},
                                     'tool_calls': {'type': 'integer', 'minimum': 0}},
                      'additionalProperties': False}}


def validate_request(request):
    """Reject malformed roles, criteria, paths and unsupported hard budgets."""
    validate(request, obj(FIELDS))
    criteria, limits = request['criteria'], request['budgets']
    if (type(request['schema_version']) is not int or not math.isfinite(limits['wall_time_seconds'])
            or limits['wall_time_seconds'] <= 0):
        raise invalid('Integer schema_version=1 and positive wall_time_seconds required')
    if len(set(criteria)) != len(criteria) or any(not item.strip() for item in criteria):
        raise invalid('Requested criteria must be nonempty and distinct')
    if 'tool_calls' in limits and type(limits['tool_calls']) is not int:
        raise invalid('tool_calls must be an integer')
    path = PurePath(request['workspace'])
    if not path.is_absolute() or '..' in path.parts:
        raise invalid('workspace must be an absolute path without traversal')
