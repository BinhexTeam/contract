from odoo import models, fields, _


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    payment_token_id = fields.Many2one(
        string=_("Payment Token"),
        comodel_name="payment.token",
    )
