import json, re
from pathlib import Path
from typing import Union, Any
from src.qb_cubie.ebt import EBT
from src.qb_cubie.protocols import WorldState
from dataclasses import dataclass
from src.qb_cubie.arenas.tempfs import TempFS

# ========== TARGETS ===================================================================================================

def dummy_return_dynamic():
    """Simulates an API that returns dynamic values."""
    import time, uuid
    return {"id": uuid.uuid4().hex, "time": time.time(), "status": "OK"}

def create_dynamic_file():
    """Simulates the creation of a log file with volatile content."""
    Path("dynamic.log").write_text("Timestamp: 123456")
    return True

def dummy_return_timestamped_log():
    """Simulates a function that returns formatted strings with timestamps."""
    return "[2026-09-06T14:13:01Z] - SYSTEM_BOOT_SUCCESS"

@dataclass
class DummyUser:
    id: int
    role: str

def dummy_return_class_instance():
    """Simulates a function that returns a complex class object."""
    return DummyUser(id=101, role="admin")

def dummy_return_nested_data():
    """Simulates a payload with potentially missing fields (unions) and lists."""
    return {
        "users": [{"id": 1, "active": True}, {"id": 2, "active": False}],
        "next_page": None,
        "metadata": "volatility_high"
    }

def create_dynamic_json_file():
    """Simulates the creation of a JSON file with dynamic runtime data."""
    Path("output.json").write_text(json.dumps({"task_id": "req_882", "duration": 1.45}))
    return True


# ========== EBT WITH TYPING-DEFINTIONS ================================================================================

def test_typing_in_returns():
    """Verifies that native types and callables seamlessly evaluate dynamic returns."""
    EBT(
        target=dummy_return_dynamic,
        post=WorldState(
            returns={
                "id": lambda actual_id: isinstance(actual_id, str) and len(actual_id) == 32,
                "time": float,
                "status": "OK"
            }
        )
    ).run()

def test_typing_in_filesystem(tmp_path):
    """Verifies that native callables can evaluate FS topologies instead of strict diffing."""
    EBT(
        arena=TempFS(),
        target=create_dynamic_file,
        pre=WorldState(fs={".": str(tmp_path)}),
        post=WorldState(
            returns=True,
            fs={"dynamic.log": lambda p: p.exists() and p.stat().st_size > 0}
        )
    ).run()

def test_typing_with_regex():
    """Checks whether re.Pattern objects are accepted as validators for dynamic strings (timestamps)."""
    EBT(
        target=dummy_return_timestamped_log,
        post=WorldState( # Expects the regex to match, instead of a static string diff
            returns=re.compile(r"^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\] - [A-Z_]+$")
        )
    ).run()

def test_typing_with_class_instances():
    """Checks whether class declarations are implicitly resolved as isinstance() checks."""
    EBT(
        target=dummy_return_class_instance,
        post=WorldState(returns=DummyUser)  # Declaration of the class, not the instance
    ).run()

def test_typing_nested_and_unions():
    """Tests recursive type resolution in nested structures and the handling of union types/Any."""
    EBT(
        target=dummy_return_nested_data,
        post=WorldState(
            returns={
                "users": list,  # Native type checking at the collection level
                "next_page": Union[str, None],  # Optionality: Accepts string or None
                "metadata": Any  # Ignores value and type, requires only the existence of the key
            }
        )
    ).run()

def test_typing_fs_content_evaluation(tmp_path):
    """Checks whether file contents can be validated based on semantic typing via predicates, rather than solely via topology."""
    import json
    def validate_json_content(p: Path) -> bool:
        if not p.exists(): return False
        data = json.loads(p.read_text())
        return isinstance(data.get("task_id"), str) and isinstance(data.get("duration"), float)
    EBT(
        arena=TempFS(),
        target=create_dynamic_json_file,
        pre=WorldState(fs={".": str(tmp_path)}),
        post=WorldState(
            returns=True,
            fs={"output.json": validate_json_content}
        )
    ).run()