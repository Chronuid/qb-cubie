"""Only explicit provisioning installs packages; arena setup validates its base."""

import importlib.util
import subprocess
import sysconfig
import venv
from pathlib import Path

import pytest

from qb_cubie import EBT, CloudpickleCodec, PickleCodec, PyVenv, WorldState
from qb_cubie.arenas._requirements import _environment_python, _requirements_satisfied
from qb_cubie.arenas.pyvenv import ArenaBuilder


@pytest.fixture
def base_env(tmp_path):
    base = tmp_path / "base"
    venv.EnvBuilder(with_pip=False, symlinks=True).create(base)
    return base


def add_distribution(base, name="demo", version="1.2", requires=(), extras=()):
    site_packages = Path(sysconfig.get_path(
        "purelib", vars={"base": str(base), "platbase": str(base)},
    ))
    metadata_dir = site_packages / f"{name}-{version}.dist-info"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    metadata = ["Metadata-Version: 2.1", f"Name: {name}", f"Version: {version}"]
    metadata.extend(f"Requires-Dist: {value}" for value in requires)
    metadata.extend(f"Provides-Extra: {extra}" for extra in extras)
    (metadata_dir / "METADATA").write_text("\n".join(metadata) + "\n", encoding="utf-8")
    return metadata_dir


@pytest.mark.parametrize(("requirement", "satisfied"), [
    ("demo", True),
    ("Demo>=1,<2", True),
    ("demo==1.2", True),
    ("demo>=2", False),
    ("demo!=1.2", False),
    ("missing", False),
    ('missing; python_version < "0"', True),
    ('demo>=2; python_version >= "3"', False),
    ("demo[unknown]", False),
    ("demo @ https://example.invalid/demo.whl", False),
])
def test_requirements_use_target_metadata(base_env, requirement, satisfied):
    add_distribution(base_env)
    assert _requirements_satisfied(_environment_python(base_env), [requirement]) is satisfied


def test_host_packages_do_not_satisfy_empty_arena(base_env, monkeypatch):
    # Even a host site-packages entry in PYTHONPATH must not satisfy the arena.
    monkeypatch.setenv("PYTHONPATH", sysconfig.get_path("purelib"))
    assert not _requirements_satisfied(_environment_python(base_env), ["msgspec"])


def test_distribution_name_can_differ_from_import_name(base_env):
    add_distribution(base_env, name="demo_library")
    assert _requirements_satisfied(_environment_python(base_env), ["demo-library>=1"])


@pytest.mark.parametrize("dependency_version", [None, "1.0", "2.0"])
def test_transitive_dependencies_are_checked(base_env, dependency_version):
    add_distribution(base_env, requires=["dependency>=2"])
    if dependency_version:
        add_distribution(base_env, name="dependency", version=dependency_version)
    assert _requirements_satisfied(
        _environment_python(base_env), ["demo"],
    ) is (dependency_version == "2.0")


def test_extras_and_dependency_cycles(base_env):
    add_distribution(base_env, requires=['dependency>=2; extra == "speed"'], extras=["speed"])
    python = _environment_python(base_env)
    assert _requirements_satisfied(python, ["demo"])
    assert not _requirements_satisfied(python, ["demo[speed]"])
    add_distribution(base_env, name="dependency", version="2.0", requires=["demo"])
    assert _requirements_satisfied(python, ["demo[speed]"])


def test_requirement_check_does_not_cache_environment_state(base_env):
    python = _environment_python(base_env)
    assert not _requirements_satisfied(python, ["demo>=1"])
    metadata = add_distribution(base_env)
    assert _requirements_satisfied(python, ["demo>=1"])
    (metadata / "METADATA").unlink()
    metadata.rmdir()
    assert not _requirements_satisfied(python, ["demo>=1"])


@pytest.fixture
def installer_calls(monkeypatch):
    """Keep real metadata probes; record installers without executing them."""
    original_run = subprocess.run
    calls = []

    def run(args, **kwargs):
        if args[0] == "uv":
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, stdout=b"", stderr=b"")
        return original_run(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    return calls


def test_builder_checks_new_packages_and_changed_versions(base_env, installer_calls):
    add_distribution(base_env)
    builder = ArenaBuilder(str(base_env)).with_packages(["demo>=1"])
    builder.build(codec=PickleCodec())
    assert installer_calls == []
    builder.with_packages(["missing"])
    builder.build(codec=PickleCodec())
    assert installer_calls[-1][3:5] == ["demo>=1", "missing"]
    ArenaBuilder(str(base_env)).with_packages(["demo>=2"]).build(codec=PickleCodec())
    assert installer_calls[-1][3] == "demo>=2"


@pytest.mark.parametrize(("requirement", "version"), [
    ("msgspec", None), ("msgspec>=2", "1.0"), ("msgspec>=1", "1.0"),
])
def test_setup_validates_codec_without_installing(
    base_env, installer_calls, requirement, version,
):
    if version:
        add_distribution(base_env, name="msgspec", version=version)
    arena = PyVenv(env_path=str(base_env))
    arena.codec.requirements = [requirement]
    before = {p.relative_to(base_env): p.read_bytes()
              for p in base_env.rglob("*") if p.is_file()}
    if requirement == "msgspec>=1":
        try:
            arena.setup(WorldState())
            assert arena.virtual_path.is_dir()
        finally:
            arena.teardown()
    else:
        with pytest.raises(RuntimeError, match=r"ArenaBuilder.*build\(codec=codec\)"):
            arena.setup(WorldState())
        assert arena.workspace_path is None
    assert installer_calls == []
    assert before == {p.relative_to(base_env): p.read_bytes()
                      for p in base_env.rglob("*") if p.is_file()}


@pytest.mark.parametrize("codec", [None, CloudpickleCodec(), PickleCodec()])
def test_builder_provisions_selected_codec(base_env, installer_calls, codec):
    arena = ArenaBuilder(str(base_env)).build(codec=codec)
    if codec is not None:
        assert arena.codec is codec
    requirements = arena.codec.requirements
    if requirements:
        assert installer_calls == [[
            "uv", "pip", "install", *requirements, "--python",
            str(_environment_python(base_env)),
        ]]
    else:
        assert installer_calls == []


def test_setup_checks_overridden_base_before_creating_workspace(base_env, installer_calls):
    # The configured path must not hide an incomplete pre.arena override.
    arena = PyVenv(env_path="unused-configured-base")
    with pytest.raises(RuntimeError, match="Arena codec requirements are not satisfied"):
        arena.setup(WorldState(arena=str(base_env)))
    assert installer_calls == []
    assert arena.workspace_path is None


def test_installer_arguments_are_delegated_unchanged(base_env, installer_calls):
    packages = ["-r", "requirements.txt"]
    ArenaBuilder(str(base_env)).with_packages(packages).build(codec=PickleCodec())
    assert installer_calls[0][3:5] == packages


def test_invalid_arena_reports_probe_error_without_installing(tmp_path, installer_calls):
    arena = tmp_path / "invalid"
    arena.mkdir()
    with pytest.raises(RuntimeError, match="Could not inspect arena requirements"):
        ArenaBuilder(str(arena)).with_packages(["demo"]).build()
    assert installer_calls == []


def test_setup_error_is_not_masked_by_teardown(tmp_path):
    arena = PyVenv(env_path=str(tmp_path / "missing"))
    with pytest.raises(RuntimeError, match="Base arena not found") as error:
        EBT(target=sum, arena=arena,
            pre=WorldState(args=([1],)), post=WorldState(returns=1)).run()
    assert any("Arena teardown also failed" in note for note in error.value.__notes__)


@pytest.mark.parametrize("codec", [None, PickleCodec()], ids=["msgspec", "pickle"])
def test_setup_rejects_incomplete_venv_without_pyvenv_cfg(base_env, codec):
    (base_env / "pyvenv.cfg").unlink()
    arena = PyVenv(env_path=str(base_env), codec=codec)
    with pytest.raises(RuntimeError, match="missing pyvenv\\.cfg"):
        arena.setup(WorldState())
    assert arena.workspace_path is None


def test_probe_rejects_incomplete_venv_without_installing(base_env, installer_calls):
    (base_env / "pyvenv.cfg").unlink()
    with pytest.raises(RuntimeError, match=r"Could not inspect arena requirements.*missing pyvenv\.cfg"):
        ArenaBuilder(str(base_env)).with_packages(["demo"]).build()
    assert installer_calls == []


def test_provision_script_clears_only_incomplete_venvs(tmp_path, base_env):
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "provision_test_arenas.py"
    spec = importlib.util.spec_from_file_location("provision_test_arenas", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    incomplete = tmp_path / "incomplete"
    (incomplete / "bin").mkdir(parents=True)
    (incomplete / "bin" / "activate").write_text("# stub\n", encoding="utf-8")

    module._remove_incomplete_venv(incomplete)
    assert not incomplete.exists()

    module._remove_incomplete_venv(base_env)
    assert base_env.exists()


def test_src_files_prunes_incomplete_venv_stubs(src_files):
    assert not any(path.name == "activate_this.py" for path in src_files)
