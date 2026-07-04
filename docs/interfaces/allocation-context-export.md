---
id: allocation-context-export
title: Allocation Context Export
kind: contract
depends_on:
  - architecture
  - domain-model
related:
  - web-routes
  - testing-playbook
  - project-roadmap
code_refs:
  - src/portfotrack/services/allocation_context_export.py
  - src/portfotrack/web/routes/report_routes.py
tests:
  - tests/services/test_allocation_context_export.py
  - tests/web/test_report_routes.py
updates_when:
  - the allocation export schema changes
  - export ordering or numeric representation changes
  - the download route or missing-data behavior changes
---

# Allocation Context Export

This contract defines the local, consumer-neutral JSON file used to exchange
an explicitly selected PortfoTrack allocation state. It contains descriptive
allocation facts only and must not include security prices, forecasts, trading
signals, or buy and sell guidance.

## Route and File

`GET /api/reports/allocation/export.json?snapshot_date=YYYY-MM-DD` returns an
`application/json` attachment named
`portfotrack-allocation-<snapshot-date>-v1.json`.

The caller must select a snapshot date explicitly. The route does not fall
back to the latest snapshot. A missing or malformed date returns `400`; an
unavailable snapshot or target returns `404`, following the existing allocation
report boundary.

## Version 1.0 Shape

```json
{
  "schema_version": "1.0",
  "snapshot": {
    "date": "2026-02-12",
    "currency": "KRW",
    "total_amount": 10000000
  },
  "assets": [
    {
      "asset_id": "us_equity",
      "current_amount": 4000000,
      "current_weight": 0.4,
      "target_weight": 0.6,
      "target_range": {"lower": 0.5, "upper": 0.7},
      "drift_percentage_points": -20.0,
      "status": "below_tolerance"
    }
  ]
}
```

Contract rules:

- `asset_id` is the existing target and snapshot asset-class identifier and is
  the stable cross-tool identity.
- `assets` is sorted ascending by `asset_id`; holding labels are excluded.
- Amounts are integer values in `snapshot.currency`.
- Weights and target bounds are ratios from `0.0` to `1.0` and retain the
  allocation report's computed precision.
- `drift_percentage_points` is `(current_weight - target_weight) * 100`, with
  floating-point noise normalized to 12 decimal places rather than
  presentation rounding.
- `status` is one of `below_tolerance`, `within_tolerance`, or
  `above_tolerance`. Bounds are inclusive.
- An empty snapshot remains valid: amounts and current weights are zero, while
  target facts and below-tolerance states remain present.
- New incompatible shapes require a new schema version. Consumers should use
  `schema_version`, not the filename, as the format authority.

## Ownership

The service builder owns payload construction and deterministic ordering. The
web route owns explicit selection, HTTP errors, and attachment headers. The
file is an export artifact and is not PortfoTrack persistence.

## Links

Depends on:

- [Architecture](../foundation/architecture.md)
- [Domain Model](../domain/overview.md)

Related:

- [Web Routes](../web/routes.md)
- [Testing Playbook](../policies/testing-playbook.md)
- [Project Roadmap](../planning/roadmap.md)
