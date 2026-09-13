# CI/CD

The pipeline is a PR gate that builds and tests every change before it can merge to `main`, plus a publish workflow that pushes the Host container image to GHCR.

## PR Gate

- **Workflow:** `.github/workflows/pr-gate.yml`
- **Triggers:** `pull_request` → `main` (including PR branch updates), `push` → `main`, and manual `workflow_dispatch`.

### Steps

1. **Checkout** — `actions/checkout@v4`.
2. **Install .NET SDK** — `actions/setup-dotnet@v4` (version from the `DOTNET_VERSION` env, currently `10.0.x`).
3. **Restore** — `dotnet restore Project.slnx`.
4. **Build** — `dotnet build --no-restore --configuration Release`.
5. **Aspire test with coverage** — local action `.github/actions/aspire-test-with-coverage`:
   - Starts `tests/Project.TestFramework.Aspire`, keeps its PID inside the action script, and waits for PostgreSQL (`127.0.0.1:15432`), Redis (`127.0.0.1:16379`), and WireMock (`http://127.0.0.1:19091/__admin/health`).
   - Restores .NET tools (`dotnet tool restore`) after the dependency pre-warm, matching the proven CI timing before tests start.
   - Prepares `artifacts/testresults/` and `artifacts/coverage/`.
   - Runs test projects in order: Host integration → Application/Infrastructure component → Domain/Application/Infrastructure/Host unit tests.
   - Generates coverage reports with `dotnet tool run reportgenerator`.
   - Stops the Aspire host from the action script's teardown trap once tests and coverage have finished or failed.
6. **Publish coverage summary** (`if: always()`) — appends `artifacts/coverage/SummaryGithub.md` to the GitHub step summary.
7. **Upload coverage artifacts** (`if: always()`) — uploads `artifacts/coverage/` as `coverage-report`.

## Publish image

- **Workflow:** `.github/workflows/publish-image.yml`
- **Triggers:** `push` → `main` (tags `:latest`), `push` → tags `v*` (semver tags), and manual `workflow_dispatch` (publishes the supplied pre-release version — never `:latest`, so a pre-release can be cut from any branch).

### Dispatch input validation

`workflow_dispatch` inputs accept only `description`, `type`, `required`, `default`, and `options` — the Actions workflow parser rejects the file outright on any other key, so a `pattern:` regex on the input is **not** valid YAML for this event. The semver constraint on `inputs.version` is therefore enforced by the job's first step, **Validate dispatch version**, which runs before checkout/QEMU/GHCR login so an invalid input fails in seconds. The value is passed through `env:` rather than `${{ }}` interpolation inside `run:`, keeping it out of the shell command string.

Accepted: `MAJOR.MINOR.PATCH` with optional `-prerelease` and `+build`, no leading `v` (e.g. `1.0.0`, `1.0.0-rc.1`, `1.2.3-alpha.1+build.7`). Rejected: `v1.0.0`, `1.0`, `latest`, empty.

## AI asset sync

Reusable workflow `.github/workflows/pipeline-ai-asset-sync.yml` (`workflow_call` + `workflow_dispatch` only — no push/pull_request). Composite action `.github/actions/ai-asset-sync`. Consumer example: `.docs/examples/ai-asset-sync-caller.yml`. See [AI Asset Sync](ai-asset-sync.md).

## .NET local tools

`.config/dotnet-tools.json` declares the local tool manifest, restored in CI (and locally) with `dotnet tool restore`:

| Tool | Version | Command |
|---|---|---|
| `dotnet-reportgenerator-globaltool` | `5.4.4` | `reportgenerator` |
| `dotnet-ef` | `10.0.8` | `dotnet-ef` |

`dotnet-ef` is pinned to the EF Core runtime version (`Directory.Packages.props`) so the migrations CLI never drifts from the `Microsoft.EntityFrameworkCore.*` packages. Bump both together.
