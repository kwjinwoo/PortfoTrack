# Domain Agent Instructions

The domain layer owns business concepts and invariants.

## Invariants

- No file system access, JSON store access, Flask imports, route handling, or
  template rendering.
- Track asset classes, not individual securities.
- Target ratios are between `0.0` and `1.0`.
- Tolerance bounds are absolute allocation ratios between `0.0` and `1.0`.
- Tolerance lower bound cannot exceed the upper bound.
- Total target ratio validation is explicit and should happen after a target is
  fully defined.
- Snapshots record dated amount-based holdings; normal application amounts are
  integer KRW values.
- Trend logic stays descriptive and rule-based; no forecasting or investment
  advice.
- Optional bets stay separated from core target allocation semantics.
- User-controlled validation errors use the custom app error hierarchy.
- Programmer or invariant violations use native Python exceptions.

## Related Knowledge

- `docs/domain-model.md`
- `docs/error-policy.md`
- `docs/testing-playbook.md`
