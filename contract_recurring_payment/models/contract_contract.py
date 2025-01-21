from datetime import datetime

from odoo import api, fields, models

SELECTION_PAYMENT_TYPE = [
    ("fixed_date", "Fixed Date"),
    ("invoice_due_date", "Invoice Due Date"),
]


class ContractContract(models.Model):
    _inherit = "contract.contract"

    allow_use_payment_token = fields.Boolean(
        default=False,
        string="Allow use payment token",
        help="Allow use payment token on recurring payment",
    )

    payment_mode_code = fields.Char(related="payment_mode_id.payment_method_id.code")
    payment_ids = fields.One2many(
        "account.payment",
        "contract_id",
        string="Payments",
    )
    next_recurring_payment_date = fields.Date(string="Next Payment Date")

    @api.model
    def cron_recurring_payment(self):
        """
        Check contracts and generate recurring payments
        :return:
        """
        contracts = self.search(
            [("active", "=", True), ("allow_use_payment_token", "=", True)]
        )

        for contract in contracts:
            if contract.next_recurring_payment_date == datetime.utcnow().date():
                if contract.payment_mode_id:
                    invoices = contract._get_related_invoices().filtered(
                        lambda account_move: account_move.state == "posted"
                        and account_move.amount_residual_signed > 0
                        and account_move.payment_state in ["not_paid", "partial"]
                    )
                    if invoices:
                        contract.payment_mode_id._create_recurring_payments(
                            invoices=invoices, contract_id=contract
                        )
