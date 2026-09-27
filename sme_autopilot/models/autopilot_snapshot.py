from odoo import api, fields, models


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

    current_cash = fields.Monetary(string="Current Cash")
    overdue_receivables = fields.Monetary(string="Overdue Receivables")
    supplier_payments_due = fields.Monetary(string="Supplier Payments Due")
    stalled_quotation_value = fields.Monetary(string="Stalled Quotations")
    projected_cash = fields.Monetary(string="Projected Cash")

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