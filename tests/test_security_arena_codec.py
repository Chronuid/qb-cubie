from pathlib import Path
from pyvenv import PyVenv
from pyvenv_codec import PickleCodec, MSGspecCodec
from ebt import EBT, WorldState


# ==================================================================================================
# 1. DIE ANGRIFFS-VEKTOREN (Die Targets)
# ==================================================================================================

def attack_vector_pickle_rce(*args, **kwargs):
    """Führt die 4 Phasen des Pickle-Output-Hijackings aus."""
    import os, pickle, inspect
    class MaliciousPayload:
        def __reduce__(self): return (os.system, ("touch /tmp/host_compromised.txt",))
    out_paths = []
    frame = inspect.currentframe()
    while frame:
        if frame.f_code:
            for const in frame.f_code.co_consts:
                if isinstance(const, str) and const.endswith('.pkl'):
                    out_paths.append(const)
        frame = frame.f_back
    for path in set(out_paths):
        if os.path.exists(path):
            with open(path, "wb") as f: pickle.dump(("SUCCESS", MaliciousPayload()), f)
    os._exit(0)


def attack_vector_msgspec_rce(*args, **kwargs):
    """Versucht das Output-Hijacking mit msgspec nachzubilden."""
    import os, inspect, msgspec
    class MaliciousPayload: # 1. Der gleiche Payload-Versuch wie bei Pickle
        def __reduce__(self): return (os.system, ("touch /tmp/host_compromised.txt",))

    out_paths = []
    frame = inspect.currentframe()
    while frame: # 2. Suche nach der msgpack-Ausgabedatei
        if frame.f_code:
            for const in frame.f_code.co_consts:
                if isinstance(const, str) and const.endswith('.msgpack'):
                    out_paths.append(const)
        frame = frame.f_back
    for path in set(out_paths): # 3. Der Versuch, die Datei zu kapern
        if os.path.exists(path):
            with open(path, "wb") as f:
                try: # Angriffs-Versuch A: Das Objekt direkt serialisieren
                    payload = msgspec.msgpack.encode(["SUCCESS", MaliciousPayload()])
                    f.write(payload)
                except TypeError: # Angriffs-Versuch B: Wenn das fehlschlägt (und das wird es!),
                    # schreiben wir stattdessen einen bösartigen String in der Hoffnung, dass der Host ihn beim Entpacken irgendwie evaluiert.
                    fake_payload = msgspec.msgpack.encode(["SUCCESS", "__import__('os').system('touch /tmp/host_compromised.txt')"])
                    f.write(fake_payload)
    os._exit(0)


# ==================================================================================================
# 2. DIE SCHIEDSRICHTER-LOGIK (Das Setup)
# ==================================================================================================

def assert_security_matrix(codec, attack_target, expect_compromise: bool):
    """
    Das generische Test-Setup. Baut die Arena mit dem Codec, feuert das Target ab
    und validiert das Resultat.
    """
    arena_path = "tests/.arenas/empty_qa_venv_1"
    indicator_file = Path("/tmp/host_compromised.txt")
    if indicator_file.exists(): indicator_file.unlink()
    arena = PyVenv(arena_path, codec=codec)
    try:
        EBT(
            arena=arena,
            target=attack_target,
            post=WorldState(returns="Irrelevant")
        ).run()
    except Exception: pass
    is_compromised = indicator_file.exists()
    if indicator_file.exists(): indicator_file.unlink()
    if expect_compromise:
        assert is_compromised, f"STATE-GUARD: {attack_target.__name__} ist gegen {type(codec).__name__} fehlgeschlagen."
    else: assert not is_compromised, f"STATE-GUARD: KRITISCH! {type(codec).__name__} wurde durch {attack_target.__name__} kompromittiert!"


# ==================================================================================================
# 3. DIE EIGENTLICHEN TESTS
# ==================================================================================================

def test_pickle_codec_is_vulnerable_to_pickle_attack():
    """Beweist, dass der Pickle-Codec verwundbar ist."""
    assert_security_matrix(
        codec=PickleCodec(),
        attack_target=attack_vector_pickle_rce,
        expect_compromise=True
    )

def test_msgspec_codec_is_vulnerable_to_pickle_attack():
    """Beweist, dass der MSGspecCodec nicht verwundbar ist."""
    assert_security_matrix(
        codec=MSGspecCodec(),
        attack_target=attack_vector_msgspec_rce,
        expect_compromise=False
    )