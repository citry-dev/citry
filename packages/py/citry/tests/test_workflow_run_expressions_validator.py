"""The workflow run-expression validator catches event and input values written into scripts."""

from pathlib import Path

import pytest
from scripts.validators import workflow_run_expressions


def _check(tmp_path: Path, workflow: str, *, folder: str = "workflows", name: str = "ci.yml") -> list[str]:
    path = tmp_path / ".github" / folder / name
    path.parent.mkdir(parents=True)
    path.write_text(workflow, encoding="utf-8")
    return workflow_run_expressions.check(tmp_path)


@pytest.mark.parametrize(
    "expression",
    [
        "github.head_ref",
        "github.event.pull_request.title",
        "github.event.issue.body",
        "inputs.workspace_dependencies",
        "github.event.inputs.name",
        # Actions also accepts the index form and any letter case.
        "github['head_ref']",
        'github["event"].issue.title',
        "GITHUB.HEAD_REF",
        "Inputs.x",
        "inputs['x']",
    ],
)
def test_an_untrusted_value_in_a_run_script_is_reported(tmp_path: Path, expression: str) -> None:
    workflow = (
        "jobs:\n  a:\n    steps:\n      - run: |\n"
        f'          echo ok\n          git push origin "${{{{ {expression} }}}}"\n'
    )
    assert _check(tmp_path, workflow) == [
        f".github/workflows/ci.yml:4: the script starting on this line contains `${{{{ {expression} }}}}`; "
        "pass the value through `env:` and read it from the environment in the script"
    ]


def test_a_composite_action_is_checked_too(tmp_path: Path) -> None:
    action = "runs:\n  using: composite\n  steps:\n    - run: echo ${{ inputs.toolchain }}\n      shell: bash\n"
    problems = _check(tmp_path, action, folder="actions/rust/setup", name="action.yml")
    assert len(problems) == 1
    assert problems[0].startswith(".github/actions/rust/setup/action.yml:4:")


def test_a_github_script_step_is_checked_too(tmp_path: Path) -> None:
    workflow = (
        "jobs:\n  a:\n    steps:\n      - uses: actions/github-script@v8\n        with:\n"
        "          script: |\n            core.info('${{ github.event.pull_request.title }}')\n"
    )
    problems = _check(tmp_path, workflow, name="ci.yaml")
    assert len(problems) == 1
    assert problems[0].startswith(".github/workflows/ci.yaml:6:")


@pytest.mark.parametrize("content", ["", "- a\n- b\n", "jobs:\n  a: {steps: [{run: 'echo ${{ matrix.os }}'}]}\n"])
def test_empty_list_and_flow_style_documents_pass(tmp_path: Path, content: str) -> None:
    assert _check(tmp_path, content) == []


def test_a_flow_style_step_is_checked(tmp_path: Path) -> None:
    workflow = "jobs:\n  a: {steps: [{run: 'echo ${{ github.head_ref }}'}]}\n"
    assert len(_check(tmp_path, workflow)) == 1


def test_values_passed_through_env_or_computed_by_the_workflow_are_allowed(tmp_path: Path) -> None:
    workflow = (
        "defaults:\n  run:\n    shell: bash\n"
        "jobs:\n  a:\n"
        "    if: github.event.pull_request.user.login == 'dependabot[bot]'\n"
        "    steps:\n"
        "      - env:\n          HEAD_REF: ${{ github.head_ref }}\n"
        "        with:\n          ref: ${{ github.event.pull_request.head.ref }}\n"
        "        run: |\n"
        '          git push origin "HEAD:$HEAD_REF"\n'
        "          echo ${{ matrix.python }} ${{ steps.a.outputs.path }} ${{ needs.b.outputs.sha }}\n"
        "          echo ${{ github.event_name }} ${{ runner.temp }} ${{ steps.inputs.outputs.x }}\n"
    )
    assert _check(tmp_path, workflow) == []
