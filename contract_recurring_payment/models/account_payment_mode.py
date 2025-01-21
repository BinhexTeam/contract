from odoo import models


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    def _create_recurring_payments(self, invoices, contract_id):
        """
        Generic method for each payment mode
        :param invoices:
        :param contract_id:
        :return:
        """
