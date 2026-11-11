"""Automatic build/cache contracts for starting studies after local changes."""

import shutil
from types import SimpleNamespace

import pytest
from test_pilot_technical_ebt import contract
from testguided_study import images
from testguided_study.artifacts import digest, read


@pytest.fixture
def image_environment(tmp_path, monkeypatch):
    repository = tmp_path / "repository"
    source = repository / "src/qb_cubie/core.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n")
    (repository / "pyproject.toml").write_text('[project]\nname="qb-cubie"\nversion="1.0.0"\n')
    root = repository / "experiments/testguided-study"
    root.mkdir(parents=True)
    for name in ("Dockerfile.pytest", "Dockerfile.cubie", "task-requirements.txt"):
        (root / name).write_text(f"synthetic {name}\n")
    monkeypatch.setattr(images, "ROOT", root)
    monkeypatch.setattr(images, "REPOSITORY", repository)
    original_which = shutil.which
    monkeypatch.setattr(images.shutil, "which", lambda name: "/synthetic/uv" if name == "uv" else original_which(name))
    state = SimpleNamespace(version="1.0.0")
    calls, registry = [], {}

    def execute(arguments, log):
        calls.append(arguments)
        if arguments[:3] == ["uv", "build", "--wheel"]:
            output = root / "local/build/wheels"
            output.mkdir(parents=True, exist_ok=True)
            (output / f"qb_cubie-{state.version}-py3-none-any.whl").write_text(
                state.version + source.read_text())
        elif arguments[:2] == ["docker", "build"]:
            tag = arguments[arguments.index("-t") + 1]
            label = arguments[arguments.index("--label") + 1].split("=", 1)[1]
            metadata = {"Id": f"sha256:synthetic-{len(calls)}", "Config": {"Labels": {images.LABEL: label}}}
            registry[tag] = metadata
            registry[metadata["Id"]] = metadata
        elif arguments[:2] == ["docker", "tag"]:
            registry[arguments[3]] = registry[arguments[2]]
        else:
            raise AssertionError(f"Unexpected external command: {arguments}")

    monkeypatch.setattr(images, "execute", execute)
    monkeypatch.setattr(images, "identity", registry.get)
    config = {"images": {"pytest": "cubie-study-pytest:local", "cubie": "cubie-study-cubie:local",
                         "evaluator": "cubie-study-pytest:local"}}

    def counts():
        return (sum(command[:3] == ["uv", "build", "--wheel"] for command in calls),
                sum(command[:2] == ["docker", "build"] and "Dockerfile.pytest" in " ".join(command) for command in calls),
                sum(command[:2] == ["docker", "build"] and "Dockerfile.cubie" in " ".join(command) for command in calls))

    return SimpleNamespace(root=root, repository=repository, source=source, state=state, calls=calls, counts=counts,
                           config=config, ensure=lambda directory: images.ensure(config, directory))


@pytest.mark.parametrize("condition", ["unchanged", "missing", "tampered", "new_version"])
def test_m11_wheel_cache_recovers_without_manual_cleanup_or_stale_selection(image_environment, condition):
    env = image_environment

    def observe():
        first = images.wheel(None, env.root / "first-build.log")
        if condition == "missing":
            first.unlink()
        elif condition == "tampered":
            first.write_text("CORRUPT_CACHED_WHEEL")
        elif condition == "new_version":
            env.state.version = "2.0.0"
            (env.repository / "pyproject.toml").write_text('[project]\nname="qb-cubie"\nversion="2.0.0"\n')
        try:
            current = images.wheel(None, env.root / "second-build.log")
        except ValueError:
            current = None
        receipt = read(env.root / "local/build/wheel.json")
        return (current is not None, current.name if current else None,
                current is not None and receipt["sha256"] == digest(current), env.counts()[0])

    version = "2.0.0" if condition == "new_version" else "1.0.0"
    contract(observe, (True, f"qb_cubie-{version}-py3-none-any.whl", True, 1 if condition == "unchanged" else 2))


@pytest.mark.parametrize("change,counts", [
    ("unchanged", (1, 1, 1)), ("base_recipe", (1, 2, 2)), ("dependencies", (1, 2, 2)),
    ("cubie_source", (2, 1, 2)), ("cubie_recipe", (1, 1, 2)),
])
def test_m12_next_start_rebuilds_only_changed_image_inputs_and_saves_current_provenance(image_environment, change, counts):
    env = image_environment

    def observe():
        env.ensure(env.root / "attempt-one/setup")
        first = read(env.root / "attempt-one/setup/images.json")
        changed = {
            "base_recipe": env.root / "Dockerfile.pytest",
            "dependencies": env.root / "task-requirements.txt",
            "cubie_source": env.source,
            "cubie_recipe": env.root / "Dockerfile.cubie",
        }.get(change)
        if changed:
            changed.write_text(changed.read_text() + "\n# current input revision\n")
        env.ensure(env.root / "attempt-two/setup")
        current = read(env.root / "attempt-two/setup/images.json")
        return (env.counts(), current["pytest"] == current["evaluator"],
                current["pytest"] == first["pytest"], current["cubie"] == first["cubie"],
                read(env.root / "attempt-one/setup/images.json") == first)

    contract(observe, (counts, True, change not in {"base_recipe", "dependencies"}, change == "unchanged", True))
