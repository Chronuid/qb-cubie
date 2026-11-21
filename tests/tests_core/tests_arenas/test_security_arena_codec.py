from pathlib import Path
from qb_cubie.core.arenas.pyvenv import PyVenv
from qb_cubie.core.arenas.codecs import PickleCodec, MSGspecCodec
from qb_cubie.core.ebt import EBT
from qb_cubie.core.protocols import WorldState


# ==================================================================================================
# 1. ATTACK-VECTORS (Targets)
# ==================================================================================================

def attack_vector_pickle_rce(indicator_path: str, *args, **kwargs):
    import inspect
    import os
    import pickle
    from pathlib import Path

    class MaliciousPayload:
        def __reduce__(self):
            return (Path.write_text, (Path(indicator_path), "compromised", "utf-8"))

    out_paths = []
    frame = inspect.currentframe()
    while frame:
        if frame.f_code:
            for const in frame.f_code.co_consts:
                if isinstance(const, str) and const.endswith('.pkl'):
                    out_paths.append(const)
        frame = frame.f_back
    for path in set(out_paths):
        with open(path, "wb") as f:
            pickle.dump(("SUCCESS", MaliciousPayload()), f)
    os._exit(0)


def attack_vector_msgspec_rce(indicator_path: str, *args, **kwargs):
    """Tries to replicate output hijacking using msgspec."""
    import inspect
    import msgspec
    import os
    from pathlib import Path

    class MaliciousPayload: # 1. The same payload attempt as with Pickle
        def __reduce__(self):
            return (Path.write_text, (Path(indicator_path), "compromised", "utf-8"))

    out_paths = []
    frame = inspect.currentframe()
    while frame: # 2. Search for the msgpack output file
        if frame.f_code:
            for const in frame.f_code.co_consts:
                if isinstance(const, str) and const.endswith('.msgpack'):
                    out_paths.append(const)
        frame = frame.f_back
    for path in set(out_paths): # 3. The attempt to hijack the file
        if os.path.exists(path):
            with open(path, "wb") as f:
                try: # Attack Attempt A: Directly serialize the object
                    payload = msgspec.msgpack.encode(["SUCCESS", MaliciousPayload()])
                    f.write(payload)
                except TypeError: # Attack Attempt B: If that fails (and it will!),
                    # Let's write a malicious string instead, hoping that the host somehow evaluates it during unpacking.
                    fake_payload = msgspec.msgpack.encode([
                        "SUCCESS",
                        f"__import__('pathlib').Path({indicator_path!r}).write_text('compromised', encoding='utf-8')",
                    ])
                    f.write(fake_payload)
    os._exit(0)


# ==================================================================================================
# 2. THE REFEREE LOGIC (The Setup)
# ==================================================================================================

def assert_security_matrix(codec, attack_target, expect_compromise: bool, tmp_path: Path):
    """
    The generic test setup. It builds the arena using the codec, fires the target, and validates the result.
    """
    arena_path = "tests/.arenas/empty_venv"
    indicator_file = tmp_path / "host_compromised.txt"
    if indicator_file.exists(): indicator_file.unlink()
    arena = PyVenv(arena_path, codec=codec)
    try:
        EBT(
            arena=arena,
            target=attack_target,
            pre=WorldState(args=(str(indicator_file),)),
            post=WorldState(returns="Irrelevant"),
        ).run()
    except Exception: pass
    is_compromised = indicator_file.exists()
    if indicator_file.exists(): indicator_file.unlink()
    if expect_compromise: assert is_compromised, \
        f"STATE-GUARD: {attack_target.__name__} failed against {type(codec).__name__}."
    else: assert not is_compromised, \
        f"STATE-GUARD: CRITICAL! {type(codec).__name__} was compromised by {attack_target.__name__}!"


# ==================================================================================================
# 3. THE ACTUAL TESTS
# ==================================================================================================

def test_pickle_codec_is_vulnerable_to_pickle_attack(tmp_path: Path):
    """Demonstrates that the pickle codec is vulnerable."""
    assert_security_matrix(
        codec=PickleCodec(),
        attack_target=attack_vector_pickle_rce,
        expect_compromise=True,
        tmp_path=tmp_path,
    )

def test_msgspec_codec_is_not_vulnerable_to_pickle_attack(tmp_path: Path):
    """Verfication that the MSGspecCodec is not vulnerable."""
    assert_security_matrix(
        codec=MSGspecCodec(),
        attack_target=attack_vector_msgspec_rce,
        expect_compromise=False,
        tmp_path=tmp_path,
    )