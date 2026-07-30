# receiving AGENTS.md

App-specific guidance for receiving workflows.

## Purpose

`receiving` owns regular and planned receiving flows, custom CSV import endpoint and matching CSV template download in admin, quick-create lookup endpoints, custom `ReceivingTypeOption` support, and authenticated download links for `ReceivingDocument` attachments stored under `PRIVATE_MEDIA_ROOT`.

## Stock Mutation

- Receiving admin CSV import writes `Receiving`, `ReceivingItem`, updates or creates `Stock`, and writes `Transaction(IN)`.
- Receiving stock rows use the receiving `document_number` as `Stock.source_document_number`.
- Receiving transactions use the same receiving `document_number` as `Transaction.source_document_number`.
- Receiving `document_number` values must not collide with opening-balance import document numbers; generated receiving numbers skip opening-balance-owned `RCV-YYYY-NNNNN` values.
- Same item/location/batch/funding can appear in different receiving documents as separate stock layers; do not average their `unit_price` values.
- Within one receiving source-document layer, expiry date and unit price must remain exact. A same-layer mismatch is rejected instead of merged.
- Stock mutation belongs to receiving execution/import workflow actions, not arbitrary model saves.
- Receiving and opening-balance imports enforce `Item.requires_expiry_date`: blank `expiry_date` is allowed only for catalog items marked as non-expiring.

## Receiving Types

- Receiving supports built-in and custom type codes.
- UI labels for non-built-in types are resolved from `ReceivingTypeOption`.

## Procurement-Linked Planned Receiving

- New procurement receiving plans are no longer manually approved.
- Approved SPJ contracts auto-create or re-sync exactly one linked planned `Receiving(contract!=NULL)` document.
- SPJ-linked planned receiving leftovers must be corrected through procurement amendments rather than the receiving-side `Tutup Sisa` close-items action.
- Legacy manual `Receiving(is_planned=True, contract IS NULL)` rows remain executable through compatibility routes.

## Attachments

- `ReceivingDocument` attachments are stored under `PRIVATE_MEDIA_ROOT`.
- Download links must remain authenticated.

## Admin Import Gotchas

- Keep the custom CSV import endpoint and matching CSV template download in admin aligned with the actual parser/resource behavior.
- CSV column docs must match the receiving admin parser/resource classes.
- Quick-create lookup POST mutations are covered by `@item_mutation_ratelimit`, not the user-management throttle bucket.
