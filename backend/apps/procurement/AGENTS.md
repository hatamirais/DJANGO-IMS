# procurement AGENTS.md

App-specific guidance for SPJ / contract procurement workflows.

## Purpose

`procurement` is the authoritative SPJ / contract procurement module.

## Contract Source Of Truth

- `ProcurementContract` is the contractual source of truth.
- Contract approval does not mutate stock.
- Kepala/Admin approval synchronously creates or re-syncs the linked planned procurement receiving execution document.
- Contract create/edit reuses supplier and funding-source quick-create modals on the SPJ form.

## Amendments

- `ProcurementAmendment` stores formal revisions.
- Amendment document numbers are scoped to the parent SPJ as `{SPJ}-A{seq}`, for example `SPJ-2026-00001-A1`.
- Kepala/Admin approval of an amendment synchronously creates or re-syncs the linked planned procurement receiving execution document.
- Amendment approval does not mutate stock.

## Numbering

- Manual SPJ numbers reserve amendment suffix space.
- Manual SPJ numbers are limited to 95 characters even though the stored document field remains 100 characters.

## Role Rules

- `GUDANG` may operate, create, and submit procurement documents.
- `GUDANG` cannot approve SPJ or amendments, even when granted elevated procurement module scope.

## Receiving Link

- Approved SPJ contracts and amendments are responsible for keeping the linked planned procurement receiving document synchronized.
- Procurement-linked receiving leftovers must be corrected through procurement amendments, not receiving-side close-items actions.
- Quick-create lookup POST mutations are covered by `@item_mutation_ratelimit`, not the user-management throttle bucket.
- Procurement mutations are POST-limited by `PROCUREMENT_MUTATION_RATE_LIMIT`.
