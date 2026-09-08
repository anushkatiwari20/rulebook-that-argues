# Planted Contradictions — Answer Key

Three contradictions were deliberately written into the corpus. This file
is the ground truth used to verify the `conflict` response type and to
calibrate/spot-check the system. It is not part of the corpus itself and
is not ingested by the application.

## Contradiction 1 — Attendance eligibility threshold

- **Section A:** `§1.4 Exam Eligibility Attendance Requirement`
  (`corpus/01_attendance_and_exams.md`) — "A student shall be permitted to
  sit for the semester-end examination in a course only if the student has
  attained a minimum of seventy-five percent (75%) attendance..."
- **Section B:** `§2.2 Medical Exemption Attendance Threshold`
  (`corpus/02_medical_exemptions.md`) — "...a student with attendance not
  less than sixty-five percent (65%) in the affected course shall be
  deemed eligible to appear in the semester-end examination
  notwithstanding §1.4."
- **The conflict:** §1.4 sets an absolute 75% floor; §2.2 explicitly
  overrides it down to 65% for medically-exempted students. A student is
  left unable to determine their real eligibility threshold without
  knowing which clause a human reader would prioritize.
- **Sample question that should trigger `conflict`:** "What is the
  minimum attendance percentage I need to sit for my exam?" or "I have 70%
  attendance — am I eligible for the exam?"

## Contradiction 2 — Who has authority to waive attendance

- **Section A:** `§1.6 Departmental Discretion in Condonation`
  (`corpus/01_attendance_and_exams.md`) — "...the Head of Department may,
  at their discretion... condone an attendance shortfall of up to ten (10)
  percentage points..."
- **Section B:** `§8.3 Powers of the University Examination Committee`
  (`corpus/08_grievance_committee.md`) — "Only the University Examination
  Committee holds the authority to waive or condone attendance
  requirements for the purpose of examination eligibility; no individual
  officer, including a Head of Department or Dean, may grant such a
  waiver on their own authority."
- **The conflict:** §1.6 explicitly grants the HOD condonation power; §8.3
  explicitly denies that any individual officer, naming the HOD, may
  exercise it. Both clauses cannot be correct simultaneously.
- **Sample question that should trigger `conflict`:** "Who do I ask to
  waive my attendance shortfall — my Head of Department or the Examination
  Committee?"

## Contradiction 3 — Late fee amount (prose vs. table)

- **Section A:** `§5.2 Late Payment Fee` (`corpus/05_fee_policy.md`) — "A
  student who pays the semester fee after the due date... shall be charged
  a flat late fee of five hundred rupees (₹500)... irrespective of how
  many days late the payment is."
- **Section B:** `§5.5 Fee Payment Schedule and Deadlines`
  (`corpus/fee_deadlines_table.md`, table footnote) — "Payments received
  after the due date... are subject to a late fine calculated at the rate
  of one hundred rupees (₹100) per day of delay..."
- **The conflict:** §5.2 describes a flat one-time fee; §5.5 describes a
  per-day accruing fine. These produce different amounts for any delay
  other than exactly five days, and one is a flat structure while the
  other is not — deliberately spans prose and a table to test cross-format
  conflict detection.
- **Sample question that should trigger `conflict`:** "How much is the
  late fee if I pay my semester fee ten days after the due date?"

## Implementation note

These three pairs are registered verbatim (by section ID) in
`app/conflicts.py`. Detection is deterministic: if retrieval surfaces both
sides of a registered pair for a given question, the response type is
`conflict` regardless of which single section scores highest.
