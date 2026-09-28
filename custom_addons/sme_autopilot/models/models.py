# from odoo import models, fields, api


# class sme_autopilot(models.Model):
#     _name = 'sme_autopilot.sme_autopilot'
#     _description = 'sme_autopilot.sme_autopilot'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

