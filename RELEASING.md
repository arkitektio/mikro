# Releasing mikro-next

`mikro-next` ships as a PyPI package (`mikro-next`). Versioning is automated by
[python-semantic-release][psr] from [Conventional Commits][cc] — you never bump
the version by hand. A push to a release branch runs
`.github/workflows/release.yaml`, which:

1. runs the test suite,
2. computes the next version from the commit history, bumps `pyproject.toml`,
   updates `CHANGELOG.md`, tags `vX.Y.Z`, and cuts a GitHub Release,
3. builds the wheel and, **only if a release was cut**, uploads it to PyPI via
   trusted publishing (OIDC).

## Commit messages drive the version

| Commit prefix | Bump | Example |
| --- | --- | --- |
| `fix:` | patch | `fix: handle empty stack` |
| `feat:` | minor | `feat: add roi accessor` |
| `feat!:` / `BREAKING CHANGE:` footer | **major** | `feat!: new api` |

Commits that aren't releasable (`chore:`, `docs:`, `refactor:` …) don't trigger
a release on their own.

## Branches

| Branch | Releases | PyPI |
| --- | --- | --- |
| `main` | stable `X.Y.Z` | the default install (`pip install mikro-next`) |
| `next` | prereleases `X.Y.Z-rc.N` | published as a **prerelease** — only reached via `pip install mikro-next --pre` or an exact pin |
| `N.x` (e.g. `2.x`) | maintenance `X.Y.Z` | published stable for an older major |

PyPI marks `…-rc.N` versions as prereleases, so a plain `pip install mikro-next`
never picks them up — `next` is a safe soak channel.

## Tag-based integration backend

`integration.yaml` runs on `main` and `next` and sets `MIKRO_SERVICE_TAG`
(`latest` on `main`, `next` elsewhere). `tests/integration/docker-compose.yml`
resolves the mikro backend image via `jhnnsrs/mikro:${MIKRO_SERVICE_TAG:-next}`,
so the prerelease line is tested against the prerelease backend and the stable
line against `:latest`.

## Day-to-day

- **Patch/feature for the current line:** merge a `fix:`/`feat:` PR into `main`.
  PSR cuts the next stable release and publishes it to PyPI.
- **Anything risky / breaking:** land it on `next` first. Each push cuts a fresh
  `…-rc.N` and publishes it as a PyPI prerelease so you can soak it. Promote by
  merging `next` → `main`.

## Working on a new major (v3)

```
next   feat!: …      -> 3.0.0-rc.1, 3.0.0-rc.2 …   (PyPI prereleases)
              │ merge main into next regularly to keep the rc base correct
main   ──2.5.2──(merge next)──> 3.0.0 -> 3.0.1 …    (stable PyPI)
          │ cut `2.x` from main HEAD *before* the 3.0.0 merge
2.x    ──2.5.2──> 2.5.3 -> 2.5.4 …                  (stable PyPI for v2)
```

1. **Develop the new major on `next`.** Land `feat!:` / `BREAKING CHANGE:`
   commits there. PSR cuts `…-rc.N` as PyPI prereleases. Periodically merge
   `main` → `next` so the rc base stays at the latest stable.
2. **Cut the maintenance branch first.** Right before promoting, branch `2.x`
   from `main` HEAD (still at the last v2 commit):
   ```sh
   git checkout main && git pull
   git checkout -b 2.x && git push -u origin 2.x
   ```
3. **Promote.** Merge `next` → `main`. The breaking change makes PSR cut the
   stable major.

## Backporting a fix (after a new major has shipped)

Branch off `N.x`, PR the fix into `N.x` with a `fix:` commit. PSR cuts the next
patch and publishes it to PyPI. Forward-port the same fix to `main`/`next` if it
also applies there.

## Consuming the next channel

```sh
pip install mikro-next --pre          # latest rc (or stable, whichever is newer)
pip install 'mikro-next==3.0.0-rc.1'  # pin a specific rc
```

Stable consumers (`pip install mikro-next`) are unaffected by the `next` channel.

## Dry-running locally

`python-semantic-release` is in the dev group, so you can preview the version a
branch would cut without pushing anything:

```sh
uv run semantic-release version --print   # prints the next version, makes no changes
```

[psr]: https://python-semantic-release.readthedocs.io/
[cc]: https://www.conventionalcommits.org/
