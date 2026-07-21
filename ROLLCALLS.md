# Voting Record Matrix — Phase 1: Roll-Call Index

This maps **every row of the tax tracker** (the 32 increases in `html`) to the **legislative roll call that enacted it**, with the legislature, session, and date. It's the data foundation for the "By Legislator" voting matrix. Machine-readable source of truth: [`roll-calls.json`](./roll-calls.json).

## The core finding

Legislators vote on **bills**, not on individual taxes. The 32 tracker rows collapse onto **9 bills plus 3 non-votes**:

- **11 rows** ride inside **one bill** — the FY26–27 budget change package (LD 210 / PL 2025 c. 388).
- **8 rows** ride inside the **2026 supplemental** (LD 2212 / PL 2025 c. 650).
- The rest are spread across 7 older bills (2019–2024) and 3 rows that have **no attributable roll call at all**.

So on the matrix, same-bill taxes share a single ✕ decision — a member can't have voted for the streaming tax but against the cannabis tax; both were in c. 388.

## Two red flags before any member-level publication

1. **2026 supplemental (LD 2212) — House passed it "under the hammer."** There appears to be **no member-level House roll call on final passage**; the nearest recorded House vote was **75–68 to strip the emergency preamble**, which is a procedural vote, not a clean up/down on the taxes. This affects rows **9, 11, 12, 13, 14, 15, 29, 32** (including the marquee millionaire's surtax, row 9). Resolve what you'll attribute before publishing.
2. **Tallies marked "TBD" need the official journal.** The official Maine Legislature roll-call pages block automated access, so exact yea/nay lists must be pulled by hand from `legislature.maine.gov` roll calls / LawMakerWeb before any "Rep. X voted yes" claim goes live.

## The index

| # | Increase | Enacting bill | Legislature | Recorded roll call & date | Status |
|---|----------|---------------|-------------|---------------------------|--------|
| 1 | Cigarette / tobacco tax +75% | LD 210 · PL 2025 c.388 | 132nd (2025) | House **74–73**, Senate **19–15** · enacted **Jun 18 2025** | reported |
| 2 | Streaming services tax (new) | LD 210 · PL 2025 c.388 | 132nd (2025) | *(same vote as #1)* | reported |
| 3 | Canned software taxable | LD 2214 · PL 2023 c.643 *(+ c.673)* | 131st (2024) | enacted **Apr 2024** · tally TBD | date-confirmed |
| 4 | Cannabis sales tax +40% | LD 210 · PL 2025 c.388 | 132nd (2025) | *(same vote as #1)* | reported |
| 5 | Real estate transfer tax +173% | LD 210 · PL 2025 c.388 | 132nd (2025) | *(same vote as #1)* | reported |
| 6 | Service provider tax base expanded | LD 210 · PL 2025 c.388 | 132nd (2025) | *(same vote as #1)* | reported |
| 7 | Lease-stream taxation timing | LD 2214 · PL 2023 c.643 *(+ c.673)* | 131st (2024) | enacted **Apr 2024** · tally TBD | date-confirmed |
| 8 | Tobacco definition expanded | PL 2023 c.613 Pt.B | 131st (2024) | LD # & tally TBD | needs-lookup |
| 9 | 2% income surtax over $1M | LD 2212 · PL 2025 c.650 | 132nd (2026) | **⚠ no clean House roll call** — House 75–68 (strip emergency preamble); passage "under the hammer" · Apr 10 2026 | attribution-risk |
| 10 | PFML: new 1% payroll tax | LD 258 · PL 2023 c.412 | 131st (2023) | enacted **Jul 6 2023** · tally TBD | date-confirmed |
| 11 | BETR eliminated for retail | LD 2212 · PL 2025 c.650 | 132nd (2026) | *(same bill as #9 — see flag)* | attribution-risk |
| 12 | Federal conformity phased | LD 2212 · PL 2025 c.650 | 132nd (2026) | *(same bill as #9)* | attribution-risk |
| 13 | Decoupled from OBBBA business breaks | LD 2212 · PL 2025 c.650 | 132nd (2026) | *(same bill as #9)* | attribution-risk |
| 14 | Employer FMLA credit repealed | LD 2212 · PL 2025 c.650 | 132nd (2026) | *(same bill as #9)* | attribution-risk |
| 15 | Declined OBBBA individual cuts | LD 2212 · PL 2025 c.650 | 132nd (2026) | *(same bill as #9)* | attribution-risk |
| 16 | 80% NOL limitation | — (TY2021 conformity) | 130th (2021)? | no standalone vote — conformity mechanic | attribution-risk |
| 17 | Corporate nexus standards | HP 891 · PL 2021 c.245 | 130th (2021) | LD #, date, tally TBD | needs-lookup |
| 18 | Decoupled from CARES Act business provisions | LD 220 · PL 2021 c.1 | 130th (2021) | date & tally TBD | date-confirmed |
| 19 | FDII add-back + MCIC cut | LD 1671 · PL 2019 c.527 *(MCIC)* **+** LD 220 · PL 2021 c.1 *(FDII)* | 129th (2019) **+** 130th (2021) | two bills · dates & tallies TBD | date-confirmed |
| 20 | Hospital SPT rate +46% | LD 2214 · PL 2023 c.643 | 131st (2024) | enacted **Apr 2024** · tally TBD | date-confirmed |
| 21 | Hospital base year updated (repeated) | — (recurring rider) | 129th–132nd | no single vote — refreshed in every budget | attribution-risk |
| 22 | PTDZ/ETIF/MCIC programs sunset | LD 258 · PL 2023 c.412 | 131st (2023) | enacted **Jul 6 2023** · tally TBD | date-confirmed |
| 23 | Pension exemption phase-out | LD 210 · PL 2025 c.388 | 132nd (2025) | *(same vote as #1)* | reported |
| 24 | Senior property-tax freeze repealed | LD 258 · PL 2023 c.412 | 131st (2023) | enacted **Jul 6 2023** · tally TBD | date-confirmed |
| 25 | Paint fee tripled | LD 210 · PL 2025 c.388 | 132nd (2025) | *(same vote as #1)* | reported |
| 26 | Hunting & fishing license fees | LD 210 · PL 2025 c.388 | 132nd (2025) | *(same vote as #1)* | reported |
| 27 | Concealed carry permit fees | LD 210 · PL 2025 c.388 | 132nd (2025) | *(same vote as #1)* | reported |
| 28 | Arborist license fee | LD 210 · PL 2025 c.388 | 132nd (2025) | *(same vote as #1)* | reported |
| 29 | Manufactured housing transfer fee | LD 2212 · PL 2025 c.650 | 132nd (2026) | *(same bill as #9)* | attribution-risk |
| 30 | PaintCare stewardship fee | — (DEP administrative) | n/a | **not a legislative vote** — exclude from matrix | no-roll-call |
| 31 | Property tax relief funds raided | LD 210 · PL 2025 c.388 | 132nd (2025) | *(same vote as #1)* | reported |
| 32 | Budget stabilization fund drained | LD 2212 · PL 2025 c.650 | 132nd (2026) | *(same bill as #9)* | attribution-risk |

## What this means for the matrix

- **Clean columns (11 rows, one vote):** everything in **PL 2025 c.388** (LD 210) — the strongest, most recent, fully-attributable column. House 74–73 / Senate 19–15, June 18 2025.
- **The problem column (8 rows):** **PL 2025 c.650** (LD 2212). Until the under-the-hammer question is resolved, present these with a footnote, not a confident ✕ per member.
- **Older bills (2019–2024):** identity and dates are set; pull exact yea/nay lists from the official journal per bill.
- **Drop from the matrix:** row 30 (PaintCare) — no legislator voted on it. Consider footnoting rows 16 and 21 (conformity mechanic / recurring rider) rather than giving them member columns.

*Verification statuses are defined in `roll-calls.json` → `_meta.verification_key`. Sources are attached per bill in that file.*
