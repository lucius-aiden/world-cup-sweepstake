from pathlib import Path

import yaml


def test_pages_workflow_builds_prod_and_dev_without_overwriting():
    workflow = yaml.load(
        Path(".github/workflows/pages.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )

    push_branches = workflow["on"]["push"]["branches"]
    build_steps = workflow["jobs"]["build"]["steps"]
    run_commands = "\n".join(step.get("run", "") for step in build_steps)

    assert "main" in push_branches
    assert "dev" in push_branches
    assert '"${{ github.workspace }}/_site"' in run_commands
    assert '"${{ github.workspace }}/_site/dev"' in run_commands
    assert 'site_base_path="/dev"' in run_commands
