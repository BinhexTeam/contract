from datetime import datetime

from odoo import models


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    def _create_recurring_payments(self, invoices, contract_id):
        """
        Generic method for each payment mode
        :param invoices:
        :return:
        """
        self.ensure_one()
        if self.payment_method_id.code == "stripe":
            payment_token = contract_id.payment_token_id
            if payment_token:

                for invoice in invoices:
                    payment_transaction = self.create_payment_transaction_online_token(
                        payment_token, invoice, contract_id
                    )
                    payment_transaction._send_payment_request()
                    if payment_transaction.state == "done":
                        payment_transaction._set_done()
                        payment_transaction._finalize_post_processing()
                        if payment_transaction.payment_id:
                            interval = contract_id.get_relative_delta(
                                contract_id.recurring_rule_type,
                                contract_id.recurring_interval,
                            )
                            payment_transaction.payment_id.update(
                                {"contract_id": contract_id.id}
                            )
                            contract_id.update(
                                {
                                    "next_recurring_payment_date": datetime.utcnow().date()
                                                                   + interval
                                }
                            )
                            payment_lines = payment_transaction.payment_id.mapped(
                                "line_ids"
                            ).filtered(
                                lambda line: not line.reconciled
                                             and line.account_type
                                             in ["asset_receivable", "liability_payable"]
                            )
                            # Pay due invoices
                            for payment_line in payment_lines:
                                if not payment_line.reconciled:
                                    invoice.js_assign_outstanding_line(payment_line.id)
        else:
            return super()._create_recurring_payments(invoices, contract_id)

    def create_payment_transaction_online_token(self, token, invoice, contract_id):
        values = {
            "provider_id": token.provider_id.id,
            "reference": f'{invoice.name}_{token.provider_ref}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
            "amount": invoice.amount_residual_signed,
            "currency_id": contract_id.pricelist_id.currency_id.id,
            "partner_id": contract_id.partner_id.id,
            "operation": f"online_token",
            "token_id": token.id,
        }
        return self.env["payment.transaction"].sudo().create(values)
