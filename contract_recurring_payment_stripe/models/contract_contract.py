from odoo import fields, models


class ContractContract(models.Model):
    _inherit = "contract.contract"

    payment_token_id = fields.Many2one("payment.token")
