# allocation AGENTS.md

App-specific guidance for pre-distribution allocation planning.

## Purpose

`allocation` owns pre-distribution planning and orchestration.

## Workflow

- The lifecycle is `DRAFT -> SUBMITTED -> APPROVED`.
- Approval auto-generates one `Distribution` per facility.
- Approval immediately reserves the approved batch quantities for each generated child distribution.
- Approved allocations may be stepped back to `SUBMITTED` by approvers.
- Stepping an allocation back releases generated child distribution reservations.
- Stepping back also deletes the auto-generated child distributions so approval can be re-run cleanly.

## Generated Distributions

- `Distribution(distribution_type=ALLOCATION)` is system-generated from allocation approval.
- Generated child distributions start in `VERIFIED` status with selected stock already reserved.
- Generated child distribution quantities are locked and cannot be edited.
- Allocation-generated child distributions remain parent-managed by the Allocation module.
- Revert generated child distributions from the parent Allocation workflow, not generic distribution reset/step-back endpoints.

## Stock Behavior

- Stock deduction is deferred to per-distribution delivery confirmation.
- Allocation approval reserves stock only; it does not consume physical stock.
- Item batch selection can span all available stock sources.
- Allocation no longer stores a header-level funding source.

## Fulfillment

- Allocation auto-transitions to `PARTIALLY_FULFILLED` when any child distribution is delivered.
- Allocation auto-transitions to `FULFILLED` when all child distributions are delivered.

## Permissions

- Allocation is active and gated by `ModuleAccess` scopes like all other modules.
