# SME Autopilot — AI Cash-Flow Copilot for Odoo

**Team 404 | BuildOdoo 2026 | AI for SMEs**

SME Autopilot is an AI-powered cash-flow copilot built inside Odoo 19.

It analyses business data already available in Odoo, detects potential cash-flow risk, explains the underlying causes using Google Gemini, recommends supported follow-up actions, and requires explicit human approval before any action is created.

## Team 404 Project Folder

The hackathon solution developed by Team 404 is located at:

```text
custom_addons/sme_autopilot/
```

The remaining source in this repository is the Odoo 19 Community source used to run and demonstrate the module.

Team 404 does not claim authorship of the upstream Odoo source. Odoo licensing and copyright files are retained in this repository.

## The Problem

SMEs often have the information needed to identify cash-flow pressure, but the signals are spread across customer invoices, supplier bills, sales quotations and operational commitments.

This means a business owner may discover a liquidity problem only after it has already become urgent.

SME Autopilot converts those operational signals into an explainable risk-and-action workflow inside Odoo.

## What SME Autopilot Does

```text
Real Odoo Data
      ↓
Cash-Flow Analysis
      ↓
Risk Detection
      ↓
Gemini AI Explanation
      ↓
Supported Recommendations
      ↓
Human Approval
      ↓
Odoo Follow-Up Activities
      ↓
Execution Summary
      ↓
Duplicate Protection
```

## Demo Business Scenario

| Metric | Amount |
|---|---:|
| Current Cash | AED 18,600 |
| Overdue Receivables | AED 32,000 |
| Expected Receipts | AED 21,000 |
| Supplier Payments Due | AED 42,000 |
| Other Commitments | AED 29,000 |
| Stalled Quotations | AED 48,000 |
| Projected Cash | AED -31,400 |
| Risk Level | Critical |

Projected cash is calculated as:

```text
18,600 + 21,000 - 42,000 - 29,000 = -31,400 AED
```

Overdue receivables and stalled quotations are shown as important cash-flow drivers, but are deliberately not treated as guaranteed future cash.

## Real Odoo Data Used

SME Autopilot scans actual Odoo business records.

**Overdue customer invoices**

Posted customer invoices are included when they remain unpaid and their due date is earlier than today.

**Supplier payments due**

Posted vendor bills are included when they remain unpaid and fall due within the near-term analysis window.

**Stalled sales quotations**

Sales quotations are included when they remain in draft or quotation state beyond the configured inactivity threshold.

## AI Cash-Flow Analysis

The module integrates with the Google Gemini API.

Gemini receives the calculated business position and returns structured content for:

- Why the cash-flow risk is happening
- Recommended action
- Expected impact

The AI is constrained to the business data supplied by Odoo and is instructed not to invent values, guarantee collection, guarantee quotation conversion, or claim guaranteed improvement.

## Human-in-the-Loop Control

AI recommendations never execute automatically.

The user must explicitly choose:

**Approve & Create Follow-Ups**

or:

**Reject Recommendation**

A rejected recommendation causes no follow-up action to be created.

## Supported Actions

The current MVP deliberately supports only safe, reversible Odoo activities.

### Overdue Receivable Follow-Up

Creates an activity on an eligible overdue customer invoice:

```text
SME Autopilot: Follow up overdue receivable
```

### Stalled Quotation Follow-Up

Creates an activity on an eligible stalled sales quotation:

```text
SME Autopilot: Follow up stalled quotation
```

The module does not automatically move money, create payments, alter invoice amounts, post accounting entries, reschedule supplier payments or confirm quotations.

## Duplicate Protection

Before creating a follow-up activity, SME Autopilot checks whether the same active activity already exists.

If it already exists, the existing activity is retained instead of creating a duplicate.

This makes repeated analysis and approval safe for the demo workflow.

## Execution Summary

After approval, the Business Health screen records:

- Execution timestamp
- Overdue receivable follow-ups
- Stalled quotation follow-ups
- Execution result
- Duplicate-protection outcome

This keeps the AI recommendation and the resulting human-approved action visible in the same workflow.

## Risk Classification

| Projected Cash | Risk Level |
|---|---|
| Below AED 0 | Critical |
| AED 0 to AED 9,999 | High |
| AED 10,000 to AED 24,999 | Medium |
| AED 25,000 and above | Low |

## Technology

- Odoo 19 Community
- Python
- PostgreSQL
- Odoo XML Views
- Google Gemini API
- REST integration
- Git and GitHub

## Odoo Module Dependencies

```text
base
mail
crm
sale_management
account
purchase
stock
```

## Project Structure

```text
custom_addons/
└── sme_autopilot/
    ├── __init__.py
    ├── __manifest__.py
    ├── models/
    │   ├── __init__.py
    │   └── autopilot_snapshot.py
    ├── security/
    │   └── ir.model.access.csv
    └── views/
        ├── menus.xml
        └── snapshot_views.xml
```

## Gemini Configuration

The Gemini API key is not stored in this repository.

Set it as an environment variable before starting Odoo:

```text
GEMINI_API_KEY
```

On Windows PowerShell, for the current session:

```powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Never commit a real API key.

## Running the Project

Install the Python requirements required by Odoo 19, configure PostgreSQL, and ensure both the standard Odoo addons directory and `custom_addons` are available in the addons path.

Example module installation or upgrade:

```powershell
python odoo-bin `
  -d YOUR_DATABASE `
  --addons-path="addons,custom_addons" `
  -u sme_autopilot `
  --stop-after-init
```

Then start Odoo normally with the same addons path.

## Demo Flow

For the hackathon demonstration:

1. Open **SME Autopilot → Business Health**.
2. Open the demo cash-flow snapshot.
3. Click **Analyse Business**.
4. Show the projected cash position and Critical risk.
5. Show the live Odoo business drivers.
6. Show the Gemini explanation and recommendations.
7. Explain that no action executes without human approval.
8. Click **Approve & Create Follow-Ups**.
9. Show the Action Execution summary.
10. Open the overdue invoice and show the Odoo follow-up activity.
11. Open the stalled quotation and show its follow-up activity.
12. Demonstrate that a repeated approval does not create duplicate activities.
13. Show the Reject path to demonstrate human control.

## Design Principles

**Grounded** — analysis is based on supplied Odoo business data.

**Explainable** — the user can see why a risk was detected.

**Human-controlled** — recommendations require explicit approval.

**Safe** — the MVP executes only non-destructive follow-up activities.

**Auditable** — analysis, decision status and execution results remain visible.

## Current MVP Status

The complete workflow is functioning end-to-end:

```text
Odoo Data → Risk Detection → Gemini AI → Human Decision
          → Odoo Follow-Ups → Execution Summary
```

## Team 404

**Hackathon:** BuildOdoo 2026  
**Track:** AI for SMEs  
**Project:** SME Autopilot — AI Cash-Flow Copilot for Odoo
