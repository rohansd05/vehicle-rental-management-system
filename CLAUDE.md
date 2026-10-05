# CLAUDE.md — Project Rules for Claude Code

This file is read automatically at the start of every Claude Code session
in this repository. Follow it exactly. If any instruction here conflicts
with a request in chat, ask before proceeding rather than silently
picking one.

## What this project is

Vehicle Rental Management System (VRMS) — a Django REST Framework backend
+ React/TypeScript frontend, built from a fixed academic SRS. This is not
a greenfield app where you can invent requirements. Every business rule,
status, and field name already exists in `docs/experiments/` and must be
matched exactly, not reinterpreted.

## Non-negotiable source of truth

- `docs/experiments/AC_2024300049_ROHAN_SE_EXP1 (1).pdf` is the
  authoritative specification. If code and SRS disagree, the SRS wins —
  flag the conflict, don't silently resolve it.
- Business rules are BR-1 through BR-16 (Section 5.5 of the SRS). Never
  invent a business rule or a numeric threshold (grace periods, deposit
  amounts, cancellation percentages, service intervals) — look it up.
- Requirement IDs (e.g. `Book.Done.Store`, `Handover.Refuse`,
  `Search.Available`) should appear as comments or docstrings next to the
  code that implements them, so the traceability matrix stays honest.
- The 19 classes and their attributes/methods in Exp 3 (Class Diagram) are
  the starting model shape. Extend them where the SRS requires fields the
  diagram omitted (e.g. `VehicleDocument`, `PartUsed`, `AddOn`, `Ledger`,
  `AuditLog`) — don't rename or drop existing ones.

## Hard technical constraints

- **Money:** always `DecimalField` / `Decimal`. Never `float` for any
  monetary value, anywhere, including in tests and fixtures (CO-6).
- **Time:** store everything in UTC. Convert to local time only at the
  presentation layer (CO-6).
- **Booking overlap:** must be enforced at the database level via a
  PostgreSQL exclusion constraint on the booking time range, not just in
  application code. This is what makes Reliability-1 (100 concurrent
  confirmations, exactly one succeeds) actually pass.
- **Security:**
  - All business logic (availability, pricing, eligibility) is enforced
    server-side. Client-side checks are UX only, never the sole control
    (CO-3).
  - Every endpoint needs an explicit DRF permission class. Never rely on
    hiding a button in the UI to restrict access (SE-4).
  - Passwords: bcrypt, work factor ≥ 12. Never log, email, or display a
    password or card detail (SE-2, CO-2).
  - No card numbers, expiry, or CVV touch our backend or logs — payment
    gateway hosted fields/tokens only.
- **External services:** Payment Gateway, Notification Service, and Maps
  Service must each sit behind an interface in `integrations/` with at
  least a sandbox/mock implementation, so tests never hit a real network
  call.
- **Audit log:** any create/update/delete of vehicle, tariff, branch,
  user, or blacklist data must write an audit entry. Audit entries are
  append-only — no update or delete endpoint should ever touch them.
- **Invoices and ledger entries** are immutable once created. Corrections
  are new records (credit notes / adjustments) that reference the
  original, never edits.

## Workflow expectations

- Before implementing a feature, state which SRS section and requirement
  IDs it covers, in one or two lines, before writing code.
- Write tests alongside the code, not after — especially anything
  touching pricing, availability, or settlement (target: 100% coverage
  on those per Maintainability-2).
- Prefer small, reviewable commits scoped to one app or one feature.
  Don't bundle backend and frontend changes for unrelated features in
  one commit.
- Don't add new dependencies without checking they're MIT/Apache 2.0/BSD
  licensed (CO-7).
- Ask before running destructive commands (`migrate --fake`, dropping a
  database, force-pushing, deleting migrations).

## Things to never do

- Never invent a UI flow, field, or role that isn't in the SRS or use
  case descriptions without flagging it as a proposed addition first.
- Never silently change a requirement ID, business rule number, or model
  field name that's already used elsewhere in the codebase or docs —
  these are cross-referenced in the traceability matrix.
- Never commit `.env`, credentials, or real payment gateway keys.