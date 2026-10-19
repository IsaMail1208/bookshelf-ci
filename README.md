# DevOps Homework — Week 5: CI pipeline with GitHub Actions

Student: Ismailbek Nurdzhanov (`IsaMail1208`)

[![CI](https://github.com/IsaMail1208/bookshelf-ci/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/IsaMail1208/bookshelf-ci/actions/workflows/ci.yml)

**Green run:** <https://github.com/IsaMail1208/bookshelf-ci/actions/runs/39254944570>
(all jobs passed: lint, test on 3.11/3.12/3.13, build; artifacts
`test-results-py3.11`, `test-results-py3.12`, `test-results-py3.13`,
`image-digest`)

**Red run (failing test):** <https://github.com/IsaMail1208/bookshelf-ci/actions/runs/39255348916>
from the demo pull request
[IsaMail1208/bookshelf-ci#1](https://github.com/IsaMail1208/bookshelf-ci/pull/1),
which intentionally broke `/healthz`. It was closed, not merged.

GitHub only runs workflows from `.github/workflows/` at the root of a
repository, so a workflow inside this course folder can never run. The same
files are therefore also pushed to their own repository,
[IsaMail1208/bookshelf-ci](https://github.com/IsaMail1208/bookshelf-ci), where
the pipeline runs on every push and pull request. The badge above and the run
link come from that repository.

## What is here

| File | Description |
| --- | --- |
| `.github/workflows/ci.yml` | CI workflow: `lint` → `test` (Python 3.11/3.12/3.13 matrix) → `build` |
| `tests/test_app.py` | 6 test functions / 9 test cases for the Bookshelf API |
| `CI.md` | Explanation of each job, the triggers and the caching |
| `app.py`, `Dockerfile`, `.dockerignore` | The Week 3 app and its multi-stage image |
| `requirements.txt`, `requirements-dev.txt` | Runtime and dev (pytest, ruff) dependencies, pinned |
| `pyproject.toml` | pytest and ruff configuration |

## Run the checks locally

Requires Python 3.11+ (tested with 3.11, 3.12, 3.13) and Docker for the image.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
ruff check . && ruff format --check .
pytest
docker build -t bookshelf:local .
```

Local results (same commands as CI, run in `python:3.x-slim` containers):

```
$ ruff check .
All checks passed!
$ ruff format --check .
2 files already formatted
$ pytest -q          # on 3.11, 3.12 and 3.13
.........                                                                [100%]
9 passed
```

## Proof that a failing test fails the build

Changing `/healthz` to return `"degraded"` instead of `"ok"`:

```
FAILED tests/test_app.py::test_healthz_returns_ok - AssertionError: assert 'd...
1 failed, 8 passed in 0.15s
pytest exit code: 1
```

A non-zero exit code fails the `test` step, `fail-fast` cancels the other
matrix jobs, and `build` (which `needs: test`) is skipped. This is exactly what
happened in the red run on GitHub:

| Job | Result |
| --- | --- |
| Lint (ruff) | success |
| Test (Python 3.13) | **failure** |
| Test (Python 3.12) | cancelled (fail-fast) |
| Test (Python 3.11) | cancelled (fail-fast) |
| Build image | skipped |

See `CI.md` for the details of each job.
