"""Versioned v7 contracts; historical v6 schemas remain unchanged."""

import copy

from .design import TEXT, action
from .team_design import COMMON as V6_COMMON
from .team_design import POLICY as V6_POLICY
from .team_design import PROMPTS as V6_PROMPTS
from .team_design import SCHEMAS as V6_SCHEMAS
from .team_design import STRINGS

POLICY = V6_POLICY | {
    # Retained for frozen-policy compatibility; local allowances are disabled.
    'orientation_calls': 0, 'orientation_seconds': 0,
    'qa_calls': 0, 'qa_seconds': 0,
    'qa_recovery_calls': 0, 'qa_recovery_seconds': 0,
    'information_calls': 0, 'information_seconds': 0,
    'response_seconds': 0, 'search_page_size': 80, 'start_card_chars': 6000,
    'repeat_limit': 2,
}
COMMON = V6_COMMON + """
V7 navigation: read_file(path, line_start, line_end) uses inclusive one-based lines.
find_paths(pattern, cursor?) uses a path glob; search_content(scope, query, cursor?)
is a literal substring search, never regex. Omit cursor for the first page; only
reuse the runner's opaque next_cursor with the same tool and parameters. A missing
scope returns public candidates; inspect one explicitly before correcting the path.
QA and Dev may navigate public sources directly. Every role, information request
and recovery shares the same task deadline. No local phase or response deadline
shortens the remaining task time.
"""
PROMPTS = {role: prompt.removeprefix(V6_COMMON) for role, prompt in V6_PROMPTS.items()}
PROMPTS['analysis'] = PROMPTS['analysis'].replace('Publish requirements with', 'Conclude orientation with requirements and')
PROMPTS['analysis'] += """
In orient, finish_orientation atomically publishes a context and starts QA.
Provide requirements with id, text, public refs, and proposed/confirmed status;
source_refs and test_entry_refs must reference current, actually read files.
Keep hypotheses and unknowns explicit. Never invent job IDs or facts. The runner
keeps orientation available until you conclude it or the shared task time expires.
"""
PROMPTS['qa'] = PROMPTS['qa'].replace('ask analysis for further navigation or API knowledge.',
                                    'navigate public files yourself; ask analysis for substantive ambiguities.')
PROMPTS['qa'] += """
Start with one justified executable regression case. A provisional context has no
confirmed requirements: confirm_requirements from the original issue and public
evidence before creating cases. Confirmation is your judgment, not a runner fact.
Do not weaken the issue. Publish only cases with complete oracles and current
collection. Requirements in proposed status cannot authorize a suite.
"""

REQUIREMENT = {'type': 'object', 'properties': {'id': TEXT, 'text': TEXT, 'refs': STRINGS},
               'required': ['id', 'text', 'refs'], 'additionalProperties': False}
ORIENT_REQUIREMENT = copy.deepcopy(REQUIREMENT)
ORIENT_REQUIREMENT['properties']['status'] = {'enum': ['proposed', 'confirmed']}
ORIENT_REQUIREMENT['required'].append('status')
READ = action('read_file', path=TEXT, line_start={'type': 'integer', 'minimum': 1},
              line_end={'type': 'integer', 'minimum': 1})
FIND = action('find_paths', pattern={**TEXT, 'description': 'Relative path glob, not regex.'})
SEARCH = action('search_content', scope=TEXT,
                query={**TEXT, 'description': 'Literal substring; escape characters are preserved.'})
for entry in (FIND, SEARCH):
    entry['properties']['cursor'] = {**TEXT, 'description': 'Opaque next_cursor from the same unchanged search.'}

SCHEMAS = copy.deepcopy(V6_SCHEMAS)
for schema in SCHEMAS.values():
    schema['oneOf'] = [e for e in schema['oneOf'] if e['properties']['action']['const'] not in
                       {'read_file', 'find_paths', 'search_content', 'publish_context'}]
    schema['oneOf'].extend(copy.deepcopy([READ, FIND, SEARCH]))
SCHEMAS['analysis']['oneOf'].append(action(
    'finish_orientation', requirements={'type': 'array', 'items': ORIENT_REQUIREMENT, 'maxItems': 20},
    source_refs=STRINGS, test_entry_refs=STRINGS, hypotheses=STRINGS, unknowns=STRINGS))
SCHEMAS['qa']['oneOf'].append(action('confirm_requirements', requirements={
    'type': 'array', 'items': REQUIREMENT, 'minItems': 1, 'maxItems': 20}))
for schema in SCHEMAS.values():
    for entry in schema['oneOf']:
        entry['properties']['note'] = {'type': 'object'}

TOOLS = sorted({e['properties']['action']['const'] for s in SCHEMAS.values() for e in s['oneOf']})


def contract():
    return {'strategy': 'team', 'version': 7, 'roles': PROMPTS, 'schemas': SCHEMAS,
            'templates': 'v7-case-forms-1'}
