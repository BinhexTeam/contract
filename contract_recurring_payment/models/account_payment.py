from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    contract_id = fields.Many2one("contract.contract", string="Contract")
