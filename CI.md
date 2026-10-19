# CI pipeline explained

Workflow file: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

## CI vs CD vs CD

- **Continuous integration**: every change is merged often and automatically
  built and tested, so integration problems are found within minutes.
- **Continuous delivery**: every change that passes CI produces an artifact
  that *could* be released at any time; the release itself is a manual button.
- **Continuous deployment**: every change that passes the pipeline is released
  to production automatically, with no manual step.

This workflow is CI: it ends with a tested, smoke-tested image, but does not
push or deploy it. That is the Week 6 topic.

## Triggers

| Event | When it runs | Why |
| --- | --- | --- |
| `push` to `main` | After every merge | Proves `main` is green and produces the image digest artifact |
| `pull_request` | Every PR opened, updated or reopened | Blocks a merge that breaks lint, tests or the build |
| `workflow_dispatch` | Manually from the Actions tab | Re-run on demand (for example after a flaky runner) |

`push` is limited to `main` so a commit on a PR branch does not run the
pipeline twice (once for `push`, once for `pull_request`). A `concurrency` group
cancels an older run of the same branch when a new commit arrives.

## Jobs

The jobs run in a chain `lint → test → build` (`needs:`), so the slower jobs do
not start when an earlier one already failed.

### 1. `lint`

Installs the dev requirements and runs `ruff check` (pyflakes, pycodestyle,
import order, bugbear, pyupgrade) and `ruff format --check`. With
`--output-format=github` ruff's messages show up as annotations on the PR diff.

### 2. `test` (matrix)

Runs `pytest` on **Python 3.11, 3.12 and 3.13** in parallel. There are 9 test
cases (6 test functions, one parametrized with 4 invalid payloads) covering the
health endpoint, the index, listing, adding and input validation.

- **Fail fast**: pytest exits with code 1 when any test fails, which fails the
  step and the job. `fail-fast: true` also cancels the other matrix jobs, and
  because `build` needs `test`, no image is built from broken code.
- **Artifact**: each matrix job uploads its JUnit XML report
  (`test-results-py3.xx`). It is uploaded with `if: always()` so the report is
  available exactly when it is needed most: when a test failed.

Verified locally: changing `/healthz` to return `"degraded"` gives
`1 failed, 8 passed` and `pytest exit code: 1`.

### 3. `build`

Builds the multi-stage Dockerfile from Week 3 with Buildx, starts the container
and curls `/healthz` (smoke test), then writes `image-digest.txt` (image tag,
image ID, digest, commit and run URL) and uploads it as the `image-digest`
artifact.

## Caching

| Cache | How | Effect |
| --- | --- | --- |
| pip | `actions/setup-python` with `cache: pip` and `cache-dependency-path: requirements-dev.txt` | Downloaded wheels are restored instead of fetched from PyPI. The cache key is a hash of the requirements file, so it is automatically invalidated when a dependency changes |
| Docker layers | `docker/build-push-action` with `cache-from/cache-to: type=gha` | Unchanged layers (the base image and the `pip install` layer) are reused between runs; only the `COPY app.py` layer is rebuilt for a code-only change |

Each matrix entry gets its own pip cache, because the key includes the Python
version and the OS. On a warm cache the install step drops from downloading all
packages to restoring them, which is most of the job time for a project this
small.

## Security choices

- `permissions: contents: read`: the default token can only read the repository.
- No secrets are needed: the image is built and loaded locally, not pushed.
- All actions are pinned to a major version tag (`actions/checkout@v4`,
  `actions/setup-python@v5`, `actions/upload-artifact@v4`,
  `docker/setup-buildx-action@v3`, `docker/build-push-action@v6`), and the
  runner image is pinned to `ubuntu-24.04` rather than `ubuntu-latest`.
