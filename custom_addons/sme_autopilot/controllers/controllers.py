# from odoo import http


# class SmeAutopilot(http.Controller):
#     @http.route('/sme_autopilot/sme_autopilot', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sme_autopilot/sme_autopilot/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sme_autopilot.listing', {
#             'root': '/sme_autopilot/sme_autopilot',
#             'objects': http.request.env['sme_autopilot.sme_autopilot'].search([]),
#         })

#     @http.route('/sme_autopilot/sme_autopilot/objects/<model("sme_autopilot.sme_autopilot"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sme_autopilot.object', {
#             'object': obj
#         })

