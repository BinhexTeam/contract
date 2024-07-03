from odoo import fields, models


class ContractContract(models.Model):
    _inherit = "contract.contract"

    res_partner_bank_id = fields.Many2one("res.partner.bank", string="Bank Account")
    mandate_id = fields.Many2one("account.banking.mandate", string="Mandate")
