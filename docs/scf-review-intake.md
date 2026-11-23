# SCF review-candidate intake

The intake workflow watches changes to the project's authoritative source registries:

- `metadata/works.json`
- `metadata/distributions.json`
- `metadata/external-reception.json`
- `metadata/application-mappings.json`
- `discovery/catalog-source.json`

For pull requests, pushes to `main`, or a manual workflow dispatch, it compares the selected commits and creates two downloadable artifacts:

- `scf-review-candidates.json` — before/after records and source fingerprints.
- `scf-review-candidates.md` — a human-readable review queue.

## Deliberate boundary

The intake workflow does **not** author or publish SCF events. A changed registry record is only a candidate signal. It does not establish that a change is material to DIO/ODI, prove the underlying event, determine the event date, infer impact, or assign lineage.

The canonical feed remains `semantic-change-feed/events.json`. Adding an event still requires editorial review of its relevance, primary evidence, `date_basis`, before/after state, scope, impact, preserved invariants, and lineage. Git commit dates and diffs are not treated as semantic evidence.

The workflow has read-only repository permissions and uploads a 30-day artifact. It does not modify repository files, open issues, create pull requests, increment the SCF version, create an archive, or deploy the site.

## Triggering

The workflow runs when one of the tracked source registries changes in a pull request or on `main`. It can also be started manually from GitHub Actions; an optional base commit can be supplied, otherwise the previous commit is used.

The source list is intentionally narrow. Derived files, keyword profiles, public HTML, and the SCF feed itself are not scanned, avoiding recursive or noisy candidate generation.
