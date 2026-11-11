"""Define CLI arguments shared by planning, authoring and real execution."""


def authoring(commands):
    """Add agent, scenario, validation and discovery commands."""
    _ollama(commands)
    for name in ("init-agent", "validate-agent", "init-scenario", "init-example", "init-base", "validate"):
        parser = commands.add_parser(name)
        parser.add_argument("path")
        if name == "init-scenario":
            parser.add_argument("--benchmark", choices=["review_agent", "developer_agent"], required=True)
        if name == "validate":
            parser.add_argument("--check-references", action="store_true")
    commands.add_parser("list", help="List scenarios, types and tags").add_argument("--package", required=True)
    commands.add_parser("guide", help="Read the installed GUIDE_Benchmark-Custom.md tutorial")


def _ollama(commands):
    """Add explicit provider and model selection to the installed example export."""
    parser = commands.add_parser("init-ollama", help="Export installed Ollama roles and freeze local model metadata")
    parser.add_argument("path")
    parser.add_argument("--endpoint", default="http://localhost:11434")
    parser.add_argument("--model", default="gemma4:12b")


def suites(commands):
    """Add explicit suite initialization and execution commands."""
    init = commands.add_parser("init-suite", help="Create relocatable smoke templates")
    init.add_argument("path")
    init.add_argument("--preset", choices=["smoke"], required=True)
    init.add_argument("--fake", action="store_true", help="Use the offline reference fake")
    init.add_argument("--agent")
    init.add_argument("--pytest-agent", help="Create paired developer trials using a separate Pytest agent")
    init.add_argument("--package")
    for name in ("plan", "run"):
        commands.add_parser(name, help=f"{name.capitalize()} the selected suite").add_argument("--suite", required=True)


def comparison(commands):
    """Add archive comparison and optional disambiguation of multiple agents."""
    parser = commands.add_parser("compare", help="Compare saved runs of compatible tasks")
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--before-agent")
    parser.add_argument("--after-agent")
    parser.add_argument("--before-condition", choices=["cubie", "pytest"])
    parser.add_argument("--after-condition", choices=["cubie", "pytest"])
    pilot = commands.add_parser("summarize-pilot", help="Summarize verified pilot archives without rerunning agents")
    pilot.add_argument("archives", nargs="+")


def measurements(commands):
    """Add portable freeze, frozen execution and read-only gate inspection commands."""
    freeze = commands.add_parser("freeze", help="Freeze a suite and its local inputs without starting an agent")
    freeze.add_argument("--suite", required=True)
    freeze.add_argument("--destination", required=True)
    run = commands.add_parser("run-frozen", help="Execute a verified frozen measurement bundle")
    run.add_argument("bundle")
    run.add_argument("--output", required=True)
    commands.add_parser("evaluate-gates", help="Recompute gates from verified archived evidence").add_argument("archive")
