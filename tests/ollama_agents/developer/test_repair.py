"""Use the production repair adapter with replayed model transport, no inference."""

import importlib
import json

from ..conftest import ReplayTransport, client
from .support import response

PATCH = '''diff --git a/pricing/policy.py b/pricing/policy.py
--- a/pricing/policy.py
+++ b/pricing/policy.py
@@ -1,2 +1,2 @@
 def fee(value):
-    return 0
+    return 7
'''


def test_repair_submits_a_patch_without_modifying_originals(api, tmp_path, developer_workspace):
    api('BudgetLedger')
    module = importlib.import_module('ollama_agents.developer.repair')
    evidence = api('EvidenceWriter')(archive_root=tmp_path / 'evidence', workspace=developer_workspace)
    transport = ReplayTransport(response({'action': 'list_files', 'prefix': 'pricing/', 'offset': 0}),
                                response({'action': 'read_file', 'path': 'pricing/policy.py', 'start_line': 0}),
                                response({'action': 'submit_patch', 'patch': PATCH}))
    adapter = module.RepairAdapter(client=client(api, transport),
                                   budget=api('BudgetLedger')(wall_time_seconds=30, reserve_seconds=1,
                                                              max_model_calls=5, max_tool_calls=5), evidence=evidence)
    request = {'schema_version': 1, 'type': 'request', 'run_id': 'repair-run', 'scenario_id': 'study/issue-1',
               'benchmark': 'developer_agent', 'process_profile': 'issue_resolution', 'phase': 'repair',
               'output_format': 'patch_v1', 'workspace': str(developer_workspace), 'task': 'Fix fee.',
               'criteria': ['repair', 'regression'], 'budgets': {'wall_time_seconds': 30, 'tool_calls': 5}}
    original = (developer_workspace / 'pricing/policy.py').read_bytes()
    event = adapter.develop(request)
    assert event['status'] == 'completed' and event['artifacts'] == ['submission.patch']
    assert (developer_workspace / 'submission.patch').read_text() == PATCH
    assert (developer_workspace / 'pricing/policy.py').read_bytes() == original
    assert not list(developer_workspace.glob('tests/test_*'))
    assert len(transport.requests) == 3
    prompt = json.loads(transport.requests[0][0].data)['messages'][0]['content']
    assert 'unified Git patch' in prompt
    assert adapter.develop(request)['status'] == 'invalid_output'
    evidence.finalize()


def test_repair_mode_has_distinct_prompt_and_capabilities(api):
    api('BudgetLedger')
    process = importlib.import_module('ollama_agents.developer.process')
    answer = process.handshake({'mode': 'repair', 'agent_id': 'repair-agent', 'model': {}})
    assert 'project_patch' in answer['capabilities'] and 'phased_submission' not in answer['capabilities']
    assert process.prompt_hash('repair') != process.prompt_hash('cubie')
