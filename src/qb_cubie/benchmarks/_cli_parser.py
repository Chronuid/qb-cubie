"""Define CLI arguments shared by planning, authoring and real execution."""


def authoring(commands):
    """Add agent, scenario, validation and discovery commands."""
    for name in ("init-agent", "validate-agent", "init-scenario", "init-example", "validate"):
        parser = commands.add_parser(name)
        parser.add_argument("path")
        if name == "init-scenario":
            parser.add_argument("--benchmark", choices=["review_agent", "developer_agent"], required=True)
        if name == "validate":
            parser.add_argument("--check-references", action="store_true")
    commands.add_parser("list", help="List scenarios, types and tags").add_argument("--package", required=True)
    commands.add_parser("guide", help="Read the installed GUIDE_Benchmark-Custom.md tutorial")


def suites(commands):
    """Add explicit suite initialization and execution commands."""
    init = commands.add_parser("init-suite", help="Create relocatable smoke templates")
    init.add_argument("path")
    init.add_argument("--preset", choices=["smoke"], required=True)
    init.add_argument("--fake", action="store_true", help="Use the offline reference fake")
    init.add_argument("--agent")
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
