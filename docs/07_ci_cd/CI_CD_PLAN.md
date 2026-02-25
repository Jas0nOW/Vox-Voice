# CI/CD Plan (v1)

## Goals
- Regression replay on golden runs
- Perf budget gating (P95 thresholds)
- Trace export validation (Perfetto import safety)

## CI pipeline (GitHub Actions / self-hosted runner)
1) Lint + typecheck
2) Unit tests (router, normalization, policy)
3) Replay goldens:
   - run `replay_goldens` on `goldens/index.json`
   - compare transcripts + router decisions
   - compute P50/P95/P99 for stage timings
4) Budgets gate:
   - fail if thresholds exceeded
5) Artifact upload:
   - traces + diffs + reports

## Release strategy
- semantic versioning
- store default config snapshots per release
- keep schema_version stable; bump only on breaking event changes
