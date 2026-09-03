# cybersecurity — Phase 3 RECOMMEND and Phase 4 EXECUTE in full: aggregation, dedup, framework-aware suppression tables and report structure

> Reference for the `cybersecurity` skill. Read it **only** after ALL agents have returned (Phase 3) and when you write the final report (Phase 4). Companion references: `scoring-rubric.md` (per-finding formula), `false-positive-suppression.md` (full rules), `report-template.md` (finding/report formats), `compliance-matrix.md` (with `--compliance`).

## Phase 3: RECOMMEND — Aggregation & Analysis

After ALL 8 agents return, aggregate results:

### Step 3.1: Score Calculation

```
Weighted Score = (Agent1_Score × 0.20) + (Agent2_Score × 0.15) +
                 (Agent3_Score × 0.10) + (Agent4_Score × 0.10) +
                 (Agent5_Score × 0.10) + (Agent6_Score × 0.15) +
                 (Agent7_Score × 0.10) + (Agent8_Score × 0.10)

Grade:
  90-100 = A (Excellent security posture)
  75-89  = B (Good with minor issues)
  50-74  = C (Needs significant improvement)
  25-49  = D (Serious security concerns)
  0-24   = F (Critical — immediate action required)
```

**Per-finding scoring**: Each agent MUST apply the formula from `references/scoring-rubric.md`:
```
Finding Score = Base Severity (CVSS-aligned) × Confidence (0.3-1.0) × Exploitability (0.5-1.0) ± Context (-20 to +20)
```

### Step 3.2: Auto-CRITICAL Gate

If ANY agent reports a HIGH-confidence CRITICAL finding, the overall report MUST:
- Flag it in the Executive Summary with a warning banner
- Ensure it appears as #1 in the remediation priority queue
- Note that the overall grade is capped at C regardless of other scores

### Step 3.3: Attack Path Chaining

Review findings across ALL agents for cross-cutting attack chains:
- Do any medium findings from different agents combine into a critical path?
- Are there information disclosure findings that enable exploitation of other findings?
- Document chains in the report's "Attack Path Analysis" section

### Step 3.4: Compliance Mapping

If `--compliance` flag is set, map EVERY finding to the relevant compliance requirement.
Load `references/compliance-matrix.md` and cross-reference:
- PCI DSS 4.0 requirements (especially 6.2.4, 6.4, 8.x)
- HIPAA technical safeguards (164.312)
- SOC 2 CC criteria (CC6, CC7, CC8)
- GDPR Article 25 (data protection by design), Article 32 (security of processing)

### Step 3.5: Deduplicate Findings

**Algorithm:**
1. If same `file:line` flagged by multiple agents → keep finding with highest severity, note cross-agent confirmation (increases confidence by one tier)
2. If different `file:line` locations share the same root cause → merge into ONE finding listing all affected locations
3. Cross-agent detection = higher confidence: if Agent 1 (vuln) AND Agent 8 (logic) both flag the same endpoint, the finding confidence goes UP
4. Remove INFO-level findings if the same code has a higher-severity finding
5. Renumber all findings sequentially (VULN-001, VULN-002, ...) after deduplication

---

## Phase 4: EXECUTE — Report Delivery

Present the final report using the template from `references/report-template.md`.

### Report Structure

```markdown
# Security Audit Report

## Executive Summary
- **Overall Security Score**: XX/100 (Grade: X)
- **Findings**: Critical: X | High: X | Medium: X | Low: X | Info: X
- **Tech Stack**: [detected]
- **Scope**: [full/quick/diff] | Files analyzed: X
- **Audit Date**: [date]
[If auto-critical gate triggered: WARNING BANNER]

## Top 5 Critical/High Findings
[VULN-001 through VULN-005 summaries]

## Category Scores
| Category | Score | Grade | Weight | Key Finding |
|----------|-------|-------|--------|-------------|
| Vulnerability Detection | XX | X | 20% | ... |
| Authorization & Access Control | XX | X | 15% | ... |
| Secret Management | XX | X | 10% | ... |
| Dependency Security | XX | X | 10% | ... |
| Infrastructure Security | XX | X | 10% | ... |
| Threat Intelligence | XX | X | 15% | ... |
| AI Code Patterns | XX | X | 10% | ... |
| Logic & Design | XX | X | 10% | ... |

## Detailed Findings

### Critical Severity
[All CRITICAL findings with full detail]

### High Severity
[All HIGH findings]

### Medium Severity
[All MEDIUM findings]

### Low Severity
[All LOW findings — collapsed/summarized]

### Informational
[Brief list — no detail needed]

## Threat Intelligence Report
[MITRE ATT&CK mapping table]
[Malware indicator summary if any]
[Supply chain risk assessment]

## Attack Path Analysis
[CHAIN-XXX findings showing how medium issues combine]

## Compliance Status
[If --compliance flag: requirement-by-requirement status]

## Remediation Priority Queue
### Fix Now (Critical)
1. [Finding] — [1-line fix guidance]

### Fix This Sprint (High)
1. [Finding] — [1-line fix guidance]

### Fix This Month (Medium)
1. [Finding] — [1-line fix guidance]

### Backlog (Low)
[Summarized list]

## Methodology
- OWASP Top 10:2021, CWE Top 25:2024, OWASP API Security Top 10:2023
- STRIDE threat modeling, MITRE ATT&CK v15
- Framework-aware false-positive suppression
- 4-tier confidence scoring (HIGH/MEDIUM/LOW/INFO)
- 8 specialist agents with weighted scoring
```

## Framework-Aware False Positive Suppression

CRITICAL: Load `references/false-positive-suppression.md` and apply these rules.

The #1 complaint about security scanners is noise. Our skill MUST be calibrated.

**Automatic confidence reduction (MEDIUM → LOW or suppress entirely):**

| Framework | Auto-Protected Pattern | Why |
|-----------|----------------------|-----|
| Django | `{{ variable }}` in templates | Auto-escaped by default |
| Django ORM | `.filter()`, `.get()`, `.exclude()` | Parameterized by default |
| SQLAlchemy | Query builder methods | Parameterized by default |
| React | JSX `{variable}` | Auto-escaped by default |
| Angular | `{{ interpolation }}` | Auto-sanitized by default |
| Vue | `{{ mustache }}` | Auto-escaped by default |
| Spring MVC | `@RequestParam`, `@PathVariable` | Type-converted by framework |
| Rails | ActiveRecord queries | Parameterized by default |
| Express + helmet | Security headers | Handled by middleware |

**Automatic confidence INCREASE:**
| Pattern | Why |
|---------|-----|
| `dangerouslySetInnerHTML` (React) | Explicitly bypasses protection |
| `mark_safe()` (Django) | Explicitly bypasses auto-escaping |
| `v-html` (Vue) | Explicitly bypasses protection |
| `bypassSecurityTrust*` (Angular) | Explicitly bypasses sanitizer |
| `| safe` (Jinja2) | Explicitly bypasses auto-escaping |
| `.raw()` / `.extra()` (Django ORM) | Bypasses parameterization |
| `text()` (SQLAlchemy) | Raw SQL, may bypass parameterization |

## Report Footer

Do NOT append any promotional footer, marketing banner, emojis, or external community links to the report. End the report after the last substantive section.
