# Feature Research

**Domain:** University/academic library management system (ILS-lite, request-and-approval circulation model)
**Researched:** 2026-06-08
**Confidence:** MEDIUM-HIGH (well-established domain with decades of prior art; project's specific request-approval model is a deliberate deviation from standard self-checkout ILS patterns, so some judgment calls are scoped to this project rather than industry-standard)

## Feature Landscape

Academic library systems are a mature domain — Integrated Library Systems (ILS) like Koha, Ex Libris Alma, and Sierra have set patron expectations for decades. The standard ILS bundles cataloging, circulation, acquisitions, serials, and OPAC (public catalog) into one platform. This project intentionally scopes down to a subset: catalog + circulation + fines + notifications, with a request-approval flow instead of self-checkout. That's a reasonable v1 cut — but a few standard ILS features are commonly assumed by patrons and librarians, and it's worth being explicit about which of those this project picks up vs. defers.

### Table Stakes (Users Expect These)

Features users assume exist. Missing these makes the system feel broken or incomplete relative to "a real library system."

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Catalog search by title/author/ISBN/category | Baseline OPAC behavior — patrons search by these fields without asking staff | LOW | Already in scope. Needs indexed columns / full-text search (Postgres `tsvector` or `pg_trgm` for fuzzy ISBN/title matching) to perform at "thousands of books" scale |
| Real-time availability status (available / checked out / reserved) | Patrons expect to know *before* walking to the library whether a copy is on the shelf | LOW-MEDIUM | Drives the "core value" stated in PROJECT.md directly. Requires copy-level (not just title-level) availability tracking — see Architecture note below |
| Loan history / "my current loans" view for students | Patrons expect to see what they have, due dates, and renewal eligibility in one place | LOW | Already in scope ("view current loans, due dates, request status") |
| Due-date reminders | Universally expected; prevents silent overdue accrual and patron frustration | LOW-MEDIUM | Already in scope via email notifications. Standard practice: 1 reminder a few days before due date |
| Overdue notices | Patrons expect to be told when something is late, not just fined silently | LOW | Already in scope. Standard practice across universities is *staged* notices (e.g., day 1, day 7, day 28/billing) — see Pitfalls implications |
| Fine calculation and visibility | Patrons expect to see what they owe and why (which book, how many days late, rate) | LOW-MEDIUM | Already in scope ("calculates overdue fines automatically"). Needs to be visible to the student, not just tracked internally — implies a "my fines" view even if payment itself is out of scope |
| Borrowing limits enforcement (max books, loan duration) | Standard at every library; patrons expect to be told *why* a request was denied ("you've reached your limit") | LOW-MEDIUM | Already in scope as "fixed borrowing rules." Must surface the *reason* for rejection, not just reject silently |
| Librarian catalog management (add/edit/remove books & copies) | Baseline staff expectation — someone must maintain the collection | MEDIUM | Already in scope. Note: "books" vs. "copies" is a real data-modeling distinction (see Dependencies) — a title can have N physical copies, each independently loanable |
| Account registration/login | Baseline for any system that tracks "who has what" | LOW-MEDIUM | Already in scope (email/password). Standard for v1; SSO correctly deferred (see Anti-Features) |
| Renewal of loans | Extremely standard — nearly every academic library lets patrons extend a loan if no one else is waiting | LOW-MEDIUM | **NOT currently in scope — flag this.** This is one of the most universally expected circulation features (every library researched allows 2-15 renewals). Its absence will be felt immediately by students who can't finish a book in the loan period and must physically return + re-request. Strongly recommend adding even a simple "renew once if no pending request" to v1 or immediate v1.x |

### Differentiators (Where This Project Can Stand Out)

These aren't required by "what a library system is" — they're where the request-approval model and a from-scratch build can actually be *better* than legacy ILS UX, which is notoriously dated and clunky.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Clear request-status visibility (pending/approved/rejected/handed-over/returned) | Legacy ILSes hide circulation-desk workflow from patrons; this project's request-approval model can make the *entire pipeline* transparent to the student in real time | LOW-MEDIUM | This is the natural payoff of choosing a request-approval model — lean into it. Directly serves "Core Value" from PROJECT.md |
| Librarian dashboard: "who has what, what's due/overdue at a glance" | Legacy ILS staff interfaces are notoriously dense and dated; a clean queue-based view of pending requests + overdue items is a major quality-of-life win over spreadsheets (the explicit baseline being replaced) | LOW-MEDIUM | This is literally the stated "Core Value" — prioritize it. A simple sortable/filterable table beats most ILS staff UIs |
| Modern, fast, mobile-friendly search UI | Most academic OPACs are desktop-era, slow, and ugly; a clean React search/browse experience is an immediate, visible win for students | LOW-MEDIUM | Low cost relative to payoff — this is "table stakes that's also a differentiator" because the bar set by legacy systems is so low |
| Plain-language email notifications with context | Legacy systems send terse, system-generated emails ("Item XYZ123 due"); friendly emails with book title, cover info, due date, and clear next steps build goodwill cheaply | LOW | Cheap to do well once the email infrastructure (already in scope) exists |
| Request reason/notes field or estimated pickup window | Helps librarians triage and plan physical handoffs, and sets student expectations ("come by after 2pm") | LOW | Small addition on top of the existing request flow; improves the human-handoff process the system is designed around |

### Anti-Features (Commonly Found in ILS, Deliberately Worth Skipping for v1)

| Feature | Why Requested | Why Problematic (at this stage) | Alternative |
|---------|---------------|-----------------|-------------|
| University SSO / ID-card integration | "Every university system integrates with central auth" | High integration effort (SAML/OAuth/LDAP), requires university IT cooperation, blocks launch on external dependency | Email/password now (already decided); SSO is a clean v2 add-on once core value is proven — confirmed correct call |
| Self-service checkout (patron marks book borrowed) | "Modern libraries use self-checkout kiosks/RFID" | Breaks the request-approval model that keeps inventory and physical handoff in sync; risks desync between system state and shelf reality, which is the exact spreadsheet problem being solved | Keep librarian-mediated handoff (already decided) — this is the *right* call for a system replacing manual tracking, not a compromise |
| Bulk/batch catalog import (MARC records, CSV, spreadsheet ingestion) | "Librarians have an existing spreadsheet, don't make them retype everything" | Real spreadsheet data is messy (duplicate entries, inconsistent formats, missing ISBNs); building robust import/dedup tooling is a project unto itself and risks polluting a fresh catalog with legacy cruft | Manual re-entry for v1 (already decided) — also functions as a natural data-quality gate; import tooling is a legitimate v1.x/v2 feature once the schema is proven |
| Acquisitions / vendor / budget management module | "Real ILSes have this" | Entirely separate workflow (purchasing, vendors, budgets) with no connection to the stated core value (who has what book); massive scope expansion | Not needed — out of scope entirely, don't even plan for it |
| Serials / journal issue tracking | "Real ILSes manage periodicals" | Different lifecycle (issues, volumes, subscriptions) than monograph circulation; adds a whole data model for a use case not mentioned in project scope | Not needed for a book-lending system — skip entirely |
| Faculty/staff differentiated borrowing rules (extended loans, higher limits) | "Real universities have different rules per user type" | Requires a role/policy matrix and configuration UI; multiplies testing surface for circulation-rule edge cases | Single student role + fixed rules (already decided) — correct v1 cut; revisit only if/when non-student patron types materialize |
| Configurable/admin-editable borrowing rules (loan length, fine rates, limits as settings) | "Librarians will want to tweak the numbers" | Turns a simple fixed-constant feature into a settings/config subsystem with validation, audit trail, and "what rules applied to this loan historically" questions | Hard-code sensible fixed defaults (already decided as "fixed borrowing rules"); if rules need to change, it's a deploy-time config value, not a UI feature, until proven necessary |
| Hold/reservation queue on currently-checked-out items | "Standard OPAC feature — patrons expect to be able to reserve a book that's out" | This is the single biggest scope-creep risk: it requires a fairness/queue data model, position-in-queue visibility, automatic notification when available, and a hold-expiry/grace-period mechanism — effectively a second circulation subsystem layered on the first | **See "Validating Project Scope" below — this is the one omission that may bite hardest at university scale** |
| In-app fine payment processing | "Patrons expect to pay fines online" | Pulls in PCI compliance, payment gateway integration, refund/dispute handling — an entirely different domain (fintech) bolted onto a library system | Calculate and *display* fines (already in scope); let payment happen in person or via existing university bursar/payment systems, as many universities already do |
| SMS notifications | "Some students don't check email" | Requires SMS gateway integration, cost-per-message, opt-in/consent flows, international number handling | Email-only (already decided) — correct v1 cut; the stated rationale ("students need to be reachable outside the app") is satisfied by email alone |

## Feature Dependencies

```
Catalog (titles + copies data model)
    └──requires──> Copy-level availability tracking
                       └──requires──> Real-time status display in search/browse
                                          └──enables──> "Is this available before I walk over?" (Core Value)

Borrow Request
    └──requires──> Catalog availability check (can't request what doesn't exist/has no available copy)
    └──requires──> Borrowing-rule enforcement (max books, eligibility check at request time)

Librarian Approval
    └──requires──> Borrow Request
    └──enables──> Physical Handoff recording (checked-out state)
                       └──requires──> Loan record creation (due date calculated from fixed loan period)

Loan Tracking
    └──requires──> Loan record (from handoff)
    └──enables──> Due-date reminder notifications
    └──enables──> Overdue detection
                       └──enables──> Overdue notifications
                       └──enables──> Fine calculation (triggered at Return)

Returns
    └──requires──> active Loan record
    └──enables──> Fine calculation (days-late × rate, computed at return time)
    └──enables──> Copy availability reset (copy becomes available again)
                       └──conflicts-if-missing──> Hold queue (without it, "available" copies may be claimed first-come, first-served only — see note)

Email Notifications
    └──requires──> Email infrastructure (SMTP/transactional email service)
    └──enables──> Approval notices, due-date reminders, overdue notices
    └──enhances──> Borrow Request UX (instant feedback loop)

Renewal (CURRENTLY MISSING FROM SCOPE)
    └──requires──> active Loan record
    └──requires──> "no pending request from another student" check
    └──conflicts-if-absent──> patron satisfaction with loan-tracking ("why can't I just extend it?")
```

### Dependency Notes

- **Copy-level vs. title-level data modeling is foundational.** A "book" in the catalog (title, author, ISBN) is distinct from a physical "copy" (barcode/ID, condition, current status: available/checked-out/lost). Get this right in the schema from day one — retrofitting copy-level tracking onto a title-only model is a painful migration. This affects Phase 1 catalog design directly.
- **Borrow Request → Approval → Handoff → Loan is a strict pipeline.** Each stage requires the prior stage's state. The roadmap should sequence these as a single connected vertical slice rather than building catalog, then requests, then loans as separate disconnected phases — they share one state machine (copy status + request status + loan status).
- **Fines depend on Returns, not on Overdue-detection alone.** The system can *flag* something as overdue (for notification purposes) before it's returned, but the fine amount is typically finalized at the return event (days between due_date and actual_return_date × rate). Don't conflate "is overdue" (a notification trigger) with "fine amount" (a return-time calculation) — they're related but computed at different times.
- **Renewal conflicts with a missing hold queue.** If renewals are added without any visibility into "does someone else want this book," a student could renew indefinitely and starve other students — exactly the kind of inventory problem the request-approval model is meant to prevent. At minimum, renewal logic needs to check "is there an active pending request for this title" before allowing renewal. This is a good argument for *some* minimal visibility into pending demand even without a full hold queue.
- **Email infrastructure is a shared dependency** for approval notices, due-date reminders, AND overdue notices — build the notification-sending capability once (templated, queued/async) and all three notification types become thin wrappers around it. This argues for treating "notification infrastructure" as its own buildable unit rather than three separate features.

## MVP Definition

### Launch With (v1) — matches current PROJECT.md scope, validated as sound

- [ ] Catalog search/browse (title, author, genre, ISBN, availability) — table stakes, core value
- [ ] Borrow request + librarian approval/rejection — table stakes, the project's defining workflow choice
- [ ] Handoff recording (checked-out state) — required to keep system state in sync with reality
- [ ] Loan tracking (current loans, due dates, status) — table stakes, core value
- [ ] Returns recording — required to close the loop and free up copies
- [ ] Fixed borrowing rules enforcement (max books, fixed loan duration) — table stakes, keeps v1 simple
- [ ] Automatic overdue fine calculation — table stakes, explicitly named in core value
- [ ] Manual catalog management (add/edit/remove books & copies) — table stakes, required before anything else can work
- [ ] Email/password registration and login — table stakes, minimum viable auth
- [ ] Email notifications (approval, due-date reminder, overdue) — table stakes, the stated "most requested touchpoint"

### Add After Validation (v1.x) — strong recommendation to pull at least the first one forward

- [ ] **Loan renewal (self-service, with a "no pending demand" check)** — *trigger: as soon as real students start hitting loan-period limits, which will happen in week one of any pilot.* This is the single most likely "wait, I can't even extend it?" complaint. Strongly consider including in v1 rather than deferring — it's LOW-MEDIUM complexity and sits directly on top of the loan-tracking data model already being built.
- [ ] Minimal "interest queue" or "notify me when available" (lightweight precursor to full holds) — *trigger: librarians/students start asking "can I get in line for this book?"* Doesn't need full hold-queue mechanics; even a simple "email me when this copy is returned" toggle defuses most of the pressure for a full reservation system.
- [ ] Fine payment status tracking (marking fines as paid in-person, by librarian) — *trigger: librarians need to reconcile who has settled fines vs. who hasn't, beyond just "calculated."* Doesn't require payment processing — just a status field + librarian action.
- [ ] Bulk catalog import tooling — *trigger: manual entry proves too slow once the pilot validates the concept and librarians want to onboard the full collection.*

### Future Consideration (v2+)

- [ ] University SSO / ID integration — defer until institutional buy-in justifies the integration cost
- [ ] Full hold/reservation queue with position visibility and auto-notify — defer until "interest queue" usage data shows real demand pressure on specific titles
- [ ] Faculty/staff differentiated rules — defer until non-student patron types are actually requested
- [ ] In-app fine payment — defer to integration with existing university payment/bursar systems rather than building a payment processor
- [ ] SMS notifications — defer; email has been validated as sufficient by the project's own rationale
- [ ] Configurable borrowing-rule admin UI — defer; fixed constants serve until proven insufficient

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Catalog search/browse with availability | HIGH | MEDIUM | P1 |
| Borrow request + approval workflow | HIGH | MEDIUM | P1 |
| Loan tracking + due dates | HIGH | LOW-MEDIUM | P1 |
| Returns + fine calculation | HIGH | MEDIUM | P1 |
| Manual catalog management | HIGH | MEDIUM | P1 |
| Email notifications (approval/reminder/overdue) | HIGH | MEDIUM | P1 |
| Email/password auth | HIGH | LOW | P1 |
| Loan renewal | HIGH | LOW-MEDIUM | **P1 (recommend pulling forward from "missing")** |
| Lightweight "notify me when available" | MEDIUM | LOW | P2 |
| Fine payment status (mark as settled) | MEDIUM | LOW | P2 |
| Bulk catalog import | MEDIUM | HIGH | P2/P3 |
| Full hold/reservation queue | MEDIUM | HIGH | P3 |
| University SSO | LOW (for v1 audience) | HIGH | P3 |
| Faculty/staff rules | LOW (no current need) | MEDIUM | P3 |

## Validating Project Scope (Direct Response to Downstream Questions)

The brief asked specifically whether the request-approval model, fixed rules, manual catalog entry, and email/password auth create problems "at whole-university scale." Findings:

1. **Request-approval vs. self-checkout: VALIDATED, no change recommended.** Every mainstream ILS supports both self-checkout and staff-mediated checkout; the project's choice to mirror the existing physical handoff process is sound and arguably *reduces* risk of inventory desync compared to self-checkout (which requires trustworthy patron-side state updates). The only scale concern is *librarian throughput* — at "thousands of books, hundreds/thousands of students," a librarian-approval bottleneck could create request backlogs during peak periods (semester start). This isn't a feature gap, but the roadmap/UX should ensure the librarian dashboard supports fast batch-style triage (approve/reject in bulk, sort by wait time) so the human bottleneck doesn't become a system complaint. Recommend flagging this as a UX requirement for the librarian-facing approval queue, not a scope change.

2. **Fixed borrowing rules: VALIDATED for v1, but expect this to be the first rule to get questioned.** All researched university libraries have *some* differentiation (grad students vs. undergrads, fine caps, renewal limits tied to hold status). Fixed rules are the right v1 simplification — but expect the very first real-world friction point to be "why can't renewals happen" (see Renewal gap above) rather than the fixed-limits themselves. The limits are accepted; the *lack of renewal* is what creates friction.

3. **Manual catalog entry: VALIDATED, with one caveat.** At "thousands of books" scale, manual entry by librarians is a real time investment (hours to days of data entry), but it's a one-time cost and — as noted in Anti-Features — doubles as a data-quality gate. No change recommended, but the roadmap should account for the fact that the system may launch with a *partial* catalog (librarians entering books incrementally), meaning search/browse needs to handle a growing, possibly-sparse catalog gracefully (no "hardcoded assumption the catalog is complete").

4. **Email/password auth: VALIDATED, no change recommended.** Standard, low-risk, unblocks everything else — exactly as the project's rationale states. The only recommendation: ensure password reset / account recovery is included even if not explicitly itemized (it's an implicit table-stakes companion to "register and log in" — omitting it generates support burden immediately).

5. **The one real gap found: Renewal.** This is the strongest finding from this research. It is near-universal in academic and public libraries (every system surveyed supports 2-15 renewals), sits directly on the loan-tracking data model already in scope, and its absence will likely generate the first wave of user complaints in any pilot. Recommend either (a) including it in v1, or (b) explicitly documenting it as a known, deliberate v1 gap with a clear v1.x trigger so it isn't forgotten.

## Sources

- [Integrated Library System — Wikipedia](https://en.wikipedia.org/wiki/Integrated_library_system) — MEDIUM confidence (general reference, cross-checked against multiple ILS vendor pages)
- [Integrated Library System: Features & Benefits for University 2025 — HashMicro](https://www.hashmicro.com/blog/7-key-features-of-an-integrated-library-system-for-university/) — MEDIUM confidence
- [Key Features of An Integrated Library System — Biblionix](https://www.biblionix.com/key-features-of-an-integrated-library-system/) — MEDIUM confidence
- [The Integrated Library System (ILS) Primer — Lucidea](https://lucidea.com/special-libraries/the-integrated-library-system-ils-primer/) — MEDIUM confidence
- [Understanding Integrated Library Systems — LIS Academy](https://lis.academy/ict-in-libraries/integrated-library-systems-types-categories/) — MEDIUM confidence
- [Fines Assessment Policy — UNT Libraries](https://library.unt.edu/policies/fines/) — HIGH confidence (primary-source institutional policy)
- [Fines and Fees for Borrowed Materials — UCLA Library](https://www.library.ucla.edu/about/policies/fines-and-fees-for-borrowed-materials/) — HIGH confidence (primary source)
- [Length of Loans & Fines — University of Pittsburgh Library System](https://library.pitt.edu/length-loans-fines) — HIGH confidence (primary source)
- [Overdue Fines and Replacement Costs — University of Missouri Libraries](https://libraryguides.missouri.edu/librarypolicies/policy10) — HIGH confidence (primary source)
- [Fines and Overdues — ALA](https://www.ala.org/tools/atoz/fines-and-overdues) — MEDIUM confidence (industry association reference)
- [What is an OPAC — OpenEduCat](https://openeducat.org/glossary/what-is-opac/) — MEDIUM confidence
- [Key features and components of a typical OPAC — LIS Edu Network](https://www.lisedunetwork.com/key-features-and-components-of-a-typical-opac-system/) — MEDIUM confidence
- [Understanding Book Reservation Systems — LIS Edu Network](https://www.lisedunetwork.com/understanding-book-reservation-systems-in-the-library/) — MEDIUM confidence
- [Borrowing Limits and Loan Periods — King County Library System](https://kcls.org/faq/borrowing-limits-and-loan-periods/) — HIGH confidence (primary source, renewal policy data point)
- [Checkout Limits & Renewals — Denver Public Library](https://www.denverlibrary.org/content/checkout-limits-renewals) — HIGH confidence (primary source)
- [Renewing Books — University of Rhode Island LibGuides](https://uri.libguides.com/circulation/renew) — HIGH confidence (primary source, academic library specifically)
- [Koha Library Software — LIS Edu Network](https://www.lisedunetwork.com/koha-library-software-features-benefits-and-why-libraries-love-it/) — MEDIUM confidence (open-source ILS feature reference)

---
*Feature research for: university/academic library management system*
*Researched: 2026-06-08*
