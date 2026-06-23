# Plan (STUB): B-EC (Elevator Controller) — C++ example

> **STATUS: STUB.** Seed facts below. Expand from
> [`bacnet-profile-plan-template.md`](../../bacnet-profile-plan-template.md) after the
> sample plans ([B-LD](../../BACnetProfileExample-B-LD-CPP/docs/plan.md),
> [B-BC](../../BACnetProfileExample-B-BC-CPP/docs/plan.md)) are reviewed.

**Profile:** B-EC · **Family:** Annex L.13 (Elevator Controller) · **Role:** B ·
**Archetype:** Controller · **Difficulty:** 4/5 · **Build wave:** 3 (builds on B-EM)

**Thesis:** B-EM **plus** writable control, time sync, and reinitialize — a
controllable elevator controller. Small, diff-able delta over B-EM.

## Required BIBBs (profiles.md L.13)
B-EM's set **+ DS-WP-B, DS-WPM-B; (DM-TS-B or DM-UTC-B), DM-RD-B**.

## Services to enable
- All of B-EM's services + WriteProperty (15), WritePropertyMultiple (16),
  TimeSync (24/25), ReinitializeDevice (20).

## Objects (baseline + B-EM objects)
- Same Lift / Escalator / Elevator Group objects, now with writable points.

## Shared features
- **DEFINE:** none.
- **REUSE:** everything from B-EM + F-OUTPUTS (B-SA writes), F-TIMESYNC (B-LD),
  F-REINIT (B-LSC).

## Known stack gaps
- Recipient-by-address (inherited from F-ALARM). profiles.md: ✅ S68.

## Notes / open questions
- Build **after B-EM and B-LSC** (reuses F-REINIT). Pure additive delta — keep it a
  clean diff from B-EM.
