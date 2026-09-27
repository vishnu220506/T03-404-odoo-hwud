import json
import logging
import os
import random
import time
from datetime import timedelta

import requests

from odoo import api, fields, models


_logger = logging.getLogger(__name__)


class SMEAutopilotSnapshot(models.Model):
    _name = "sme.autopilot.snapshot"
    _description = "SME Autopilot Business Snapshot"
    _order = "generated_at desc"

    name = fields.Char(
        string="Snapshot",
        required=True,
        default="Business Health Snapshot",
    )

    generated_at = fields.Datetime(
        string="Generated At",
        default=fields.Datetime.now,
        required=True,
    )

    current_cash = fields.Monetary(
        string="Current Cash"
    )

    overdue_receivables = fields.Monetary(
        string="Overdue Receivables"
    )

    expected_receipts = fields.Monetary(
        string="Expected Receipts"
    )

    supplier_payments_due = fields.Monetary(
        string="Supplier Payments Due"
    )

    other_commitments = fields.Monetary(
        string="Other Commitments"
    )

    stalled_quotation_value = fields.Monetary(
        string="Stalled Quotations"
    )

    projected_cash = fields.Monetary(
        string="Projected Cash",
        compute="_compute_projected_cash",
        store=True,
    )

    risk_level = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Risk Level",
        compute="_compute_risk_level",
        store=True,
    )

    ai_explanation = fields.Text(
        string="Why Is This Happening?"
    )

    ai_recommendation = fields.Text(
        string="Recommended Action"
    )

    ai_expected_impact = fields.Text(
        string="Expected Impact"
    )

    approval_status = fields.Selection(
        [
            ("pending", "Pending Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Action Status",
        default="pending",
        required=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Currency",
        readonly=True,
    )

    @api.depends(
        "current_cash",
        "expected_receipts",
        "supplier_payments_due",
        "other_commitments",
    )
    def _compute_projected_cash(self):
        for record in self:
            record.projected_cash = (
                record.current_cash
                + record.expected_receipts
                - record.supplier_payments_due
                - record.other_commitments
            )

    @api.depends("projected_cash")
    def _compute_risk_level(self):
        for record in self:
            if record.projected_cash < 0:
                record.risk_level = "critical"
            elif record.projected_cash < 10000:
                record.risk_level = "high"
            elif record.projected_cash < 25000:
                record.risk_level = "medium"
            else:
                record.risk_level = "low"

    def _build_ai_prompt(self):
        self.ensure_one()

        currency = self.currency_id.name or "AED"

        return f"""
You are an AI cash-flow copilot embedded inside Odoo for an SME.

Analyse only the business information supplied below.

BUSINESS DATA

Current Cash: {currency} {self.current_cash:.2f}
Overdue Receivables: {currency} {self.overdue_receivables:.2f}
Expected Receipts: {currency} {self.expected_receipts:.2f}
Supplier Payments Due: {currency} {self.supplier_payments_due:.2f}
Other Commitments: {currency} {self.other_commitments:.2f}
Stalled Quotations: {currency} {self.stalled_quotation_value:.2f}
Projected Cash: {currency} {self.projected_cash:.2f}
Risk Level: {self.risk_level}

TASK

Produce:

1. A concise explanation of why the cash-flow risk exists.
2. Specific recommended actions for the SME.
3. A concise description of the expected impact.

STRICT RULES

- Use only the business data supplied above.
- Do not invent financial amounts.
- Do not invent customers, suppliers, dates, probabilities or savings.
- Overdue receivables are unpaid amounts, not guaranteed collections.
- Stalled quotations are sales pipeline, not guaranteed revenue or cash.
- Do not treat quotations as confirmed receipts.
- Always use the term "stalled quotations".
- Do not promise that the risk level will improve.
- Expected impact must be conditional, not guaranteed.
- Recommendations require human approval before execution.
- Do not claim that any recommended action has already been performed.
- Keep the answer professional and concise.
"""

    def _build_gemini_payload(self):
        self.ensure_one()

        return {
            "contents": [
                {
                    "parts": [
                        {
                            "text": self._build_ai_prompt(),
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseFormat": {
                    "text": {
                        "mimeType": "APPLICATION_JSON",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "explanation": {
                                    "type": "string",
                                    "description": (
                                        "Concise explanation of the "
                                        "cash-flow problem."
                                    ),
                                },
                                "recommendation": {
                                    "type": "string",
                                    "description": (
                                        "Specific actions requiring "
                                        "human approval."
                                    ),
                                },
                                "expected_impact": {
                                    "type": "string",
                                    "description": (
                                        "Conditional expected business "
                                        "impact without guarantees."
                                    ),
                                },
                            },
                            "required": [
                                "explanation",
                                "recommendation",
                                "expected_impact",
                            ],
                            "additionalProperties": False,
                        },
                    }
                }
            },
        }

    def _request_gemini_model(
        self,
        model_name,
        payload,
        api_key,
        attempts=2,
    ):
        self.ensure_one()

        url = (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/{model_name}:generateContent"
        )

        transient_statuses = {
            408,
            429,
            500,
            502,
            503,
            504,
        }

        last_error = None

        for attempt in range(attempts):
            try:
                response = requests.post(
                    url,
                    headers={
                        "x-goog-api-key": api_key,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=20,
                )

                if (
                    response.status_code in transient_statuses
                    and attempt < attempts - 1
                ):
                    delay = (
                        1.0 * (2 ** attempt)
                        + random.uniform(0.0, 0.5)
                    )

                    _logger.warning(
                        "Gemini model %s returned HTTP %s. "
                        "Retrying in %.2f seconds.",
                        model_name,
                        response.status_code,
                        delay,
                    )

                    time.sleep(delay)
                    continue

                response.raise_for_status()

                response_data = response.json()

                ai_text = (
                    response_data["candidates"][0]
                    ["content"]["parts"][0]["text"]
                )

                insight = json.loads(ai_text)

                return insight

            except (
                requests.RequestException,
                KeyError,
                IndexError,
                TypeError,
                ValueError,
            ) as exc:
                last_error = exc

                status_code = None

                if isinstance(exc, requests.RequestException):
                    if exc.response is not None:
                        status_code = exc.response.status_code

                retryable = (
                    status_code is None
                    or status_code in transient_statuses
                )

                if retryable and attempt < attempts - 1:
                    delay = (
                        1.0 * (2 ** attempt)
                        + random.uniform(0.0, 0.5)
                    )

                    _logger.warning(
                        "Gemini model %s request failed. "
                        "Retrying in %.2f seconds.",
                        model_name,
                        delay,
                    )

                    time.sleep(delay)
                    continue

                raise

        if last_error:
            raise last_error

        raise RuntimeError(
            f"Gemini request failed for model {model_name}"
        )

    def _generate_ai_insight(self):
        self.ensure_one()

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            self.ai_explanation = (
                "AI analysis is unavailable because the Gemini API key "
                "is not configured for the Odoo process."
            )

            self.ai_recommendation = (
                "Configure GEMINI_API_KEY and run Analyse Business again."
            )

            self.ai_expected_impact = (
                "No AI-generated action has been approved or executed."
            )

            return

        payload = self._build_gemini_payload()

        models_to_try = [
            ("gemini-3.8-flash", 2),
            ("gemini-3.5-flash-lite", 2),
        ]

        for model_name, attempts in models_to_try:
            try:
                insight = self._request_gemini_model(
                    model_name=model_name,
                    payload=payload,
                    api_key=api_key,
                    attempts=attempts,
                )

                self.ai_explanation = insight["explanation"]
                self.ai_recommendation = insight["recommendation"]
                self.ai_expected_impact = insight["expected_impact"]

                _logger.info(
                    "SME Autopilot AI analysis completed using %s "
                    "for snapshot %s",
                    model_name,
                    self.id,
                )

                return

            except Exception:
                _logger.exception(
                    "Gemini model %s failed for snapshot %s",
                    model_name,
                    self.id,
                )

        self.ai_explanation = (
            "The business figures were analysed successfully, "
            "but the AI insight service is temporarily unavailable."
        )

        self.ai_recommendation = (
            "Retry Analyse Business after checking the AI connection."
        )

        self.ai_expected_impact = (
            "No AI-generated action has been approved or executed."
        )

    def _schedule_follow_up_once(
        self,
        target,
        summary,
        note,
        deadline,
    ):
        activity_type = self.env.ref(
            "mail.mail_activity_data_todo"
        )

        existing_activity = target.activity_ids.filtered(
            lambda activity: (
                activity.activity_type_id == activity_type
                and activity.summary == summary
            )
        )

        if existing_activity:
            return

        target.activity_schedule(
            "mail.mail_activity_data_todo",
            date_deadline=deadline,
            summary=summary,
            note=note,
        )

    def action_approve_recommendation(self):
        today = fields.Date.context_today(self)
        stalled_before = fields.Datetime.now() - timedelta(days=7)

        for record in self:
            overdue_invoices = self.env["account.move"].search([
                ("company_id", "=", record.company_id.id),
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("invoice_date_due", "<", today),
                ("amount_residual", ">", 0),
            ])

            stalled_quotations = self.env["sale.order"].search([
                ("company_id", "=", record.company_id.id),
                ("state", "in", ["draft", "sent"]),
                ("date_order", "<=", stalled_before),
            ])

            for invoice in overdue_invoices:
                record._schedule_follow_up_once(
                    target=invoice,
                    summary=(
                        "SME Autopilot: Follow up overdue receivable"
                    ),
                    note=(
                        "Human-approved follow-up created by SME Autopilot "
                        "after cash-flow analysis."
                    ),
                    deadline=today + timedelta(days=1),
                )

            for quotation in stalled_quotations:
                record._schedule_follow_up_once(
                    target=quotation,
                    summary=(
                        "SME Autopilot: Follow up stalled quotation"
                    ),
                    note=(
                        "Human-approved commercial follow-up created by "
                        "SME Autopilot after cash-flow analysis."
                    ),
                    deadline=today + timedelta(days=1),
                )

            record.approval_status = "approved"

    def action_reject_recommendation(self):
        for record in self:
            record.approval_status = "rejected"

    def action_analyse_business(self):
        today = fields.Date.context_today(self)
        vendor_horizon = today + timedelta(days=14)
        stalled_before = fields.Datetime.now() - timedelta(days=7)

        for record in self:
            overdue_invoices = self.env["account.move"].search([
                ("company_id", "=", record.company_id.id),
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("invoice_date_due", "<", today),
                ("amount_residual", ">", 0),
            ])

            upcoming_vendor_bills = self.env["account.move"].search([
                ("company_id", "=", record.company_id.id),
                ("move_type", "=", "in_invoice"),
                ("state", "=", "posted"),
                ("invoice_date_due", ">=", today),
                ("invoice_date_due", "<=", vendor_horizon),
                ("amount_residual", ">", 0),
            ])

            stalled_quotations = self.env["sale.order"].search([
                ("company_id", "=", record.company_id.id),
                ("state", "in", ["draft", "sent"]),
                ("date_order", "<=", stalled_before),
            ])

            record.overdue_receivables = sum(
                overdue_invoices.mapped("amount_residual")
            )

            record.supplier_payments_due = sum(
                upcoming_vendor_bills.mapped("amount_residual")
            )

            record.stalled_quotation_value = sum(
                stalled_quotations.mapped("amount_total")
            )

            record.generated_at = fields.Datetime.now()
            record.approval_status = "pending"

            record._generate_ai_insight()