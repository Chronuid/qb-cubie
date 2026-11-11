"""Enforce short decision checkpoints without treating model claims as facts."""

import copy


class Analysis:
    def __init__(self):
        self.pending = 'reproduction'
        self.read = False
        self.reviewed = False
        self.records = {}

    def schema(self, schema):
        entries = []
        for original in schema['oneOf']:
            entry = copy.deepcopy(original)
            name = entry['properties']['action']['const']
            if name == 'analyze':
                if not self.read:
                    continue
                entry['properties']['phase'] = {'enum': [self.pending] if self.pending else ['review']}
            elif name == 'submit':
                if self.pending or not self.reviewed:
                    continue
            elif name in {'write_file', 'replace_text', 'delete_file'} and self.pending:
                continue
            entries.append(entry)
        return {'oneOf': entries}

    def analyze(self, action):
        phase = action['phase']
        self.records[phase] = {k: v for k, v in action.items() if k not in {'action', 'stage'}}
        self.reviewed = phase == 'review'
        self.pending = None
        return {'status': 'completed', 'analysis_recorded': phase,
                'scope': 'Model assessment, not verified runner evidence.'}

    def observe(self, action, result):
        if result.get('status') != 'completed':
            return
        name = action['action']
        if name == 'read_file':
            self.read = True
        if name in {'write_file', 'replace_text', 'delete_file', 'run_tests', 'check_baseline'}:
            self.reviewed = False
        if (result.get('observation') in {'assertion_failure', 'test_failure', 'invalid_test_run'}
                and not result.get('collection_only')):
            self.pending = 'diagnosis' if 'reproduction' in self.records else 'reproduction'
