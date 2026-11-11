"""Run benchmark adapters inside immutable images with only the visible workspace."""

import os
import re
import subprocess

from qb_cubie.benchmarks.contracts import _validation as v

from ._common import docker

WITHOUT_CUBIE = (
    "import importlib.util, os, sys; "
    "assert importlib.util.find_spec('qb_cubie') is None, 'Pytest baseline image contains Cubie'; "
    "os.execvp(sys.argv[1], sys.argv[1:])"
)


def image(agent):
    """Require an immutable adapter image reference."""
    value = agent.get('container_image')
    v.require(type(value) is str and re.fullmatch(r'[^\s@]+@sha256:[a-f0-9]{64}|sha256:[a-f0-9]{64}', value),
              'agent.container_image', 'adapter needs an immutable image digest containing its command')
    v.require(not value.startswith('-'), 'agent.container_image', 'invalid image')
    return value


class AgentContainer:
    """Own the whole adapter container, including children surviving the CLI."""

    def __init__(self, agent, name, workspace=None, evidence=None, *, without_cubie=False, network=True):
        """Initialize the bounded container execution configuration."""
        self.docker = docker('agent.container', 'Docker isolation runtime unavailable')
        self.name = 'cubie-agent-' + name
        self.stopped = False
        v.identifier(self.name, 'agent.container')
        self.command = _agent_command(self.docker, self.name)
        _mounts(self.command, workspace, evidence)
        if not network:
            self.command.extend(['--network', 'none'])
        if workspace is not None:
            self.command.extend(['--workdir', str(workspace)])
        if without_cubie:
            self.command.extend(['--entrypoint', 'python', image(agent), '-I', '-c', WITHOUT_CUBIE, *agent['command']])
        else:
            self.command.extend([image(agent), *agent['command']])

    def __enter__(self):
        """Expose the configured isolated adapter command."""
        return self.command

    def __exit__(self, *_):
        """Terminate all remaining adapter container processes."""
        self.stop()

    def stop(self):
        """Confirm termination of the adapter container."""
        if self.stopped:
            return
        try:
            result = subprocess.run([self.docker, 'rm', '--force', self.name], check=False, capture_output=True, timeout=30)
            v.require(result.returncode == 0 or b'No such container' in result.stderr, 'agent.container', 'could not confirm termination')
            self.stopped = True
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ValueError('agent.container: could not confirm termination') from error


def _agent_command(docker, name):
    """Declare the bounded adapter container command."""
    command = [docker, 'run', '--pull', 'never', '--rm', '-i', '--name', name, '--init',
                    '--add-host', 'host.docker.internal:host-gateway',
                    '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                    '--memory', str(8 * 1024**3), '--memory-swap', str(8 * 1024**3),
                    '--cpus', '2', '--pids-limit', '256']
    if os.name != 'nt':
        command.extend(['--user', f'{os.getuid()}:{os.getgid()}'])
    command.extend(['--env', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1', '--env', 'PYTHONDONTWRITEBYTECODE=1'])
    return command


def _mounts(command, workspace, evidence):
    """Grant only the visible workspace and empty evidence directory."""
    if workspace is not None:
        v.require(',' not in str(workspace), 'workspace', 'comma in Docker mount path unsupported')
        command.extend(['--mount', f'type=bind,source={workspace},target={workspace}'])
    if evidence is not None:
        evidence.mkdir(parents=True)
        v.require(',' not in str(evidence), 'evidence', 'comma in Docker mount path unsupported')
        command.extend(['--mount', f'type=bind,source={evidence},target=/agent-evidence'])
