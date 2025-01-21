from datetime import datetime

from odoo import models


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    def create_payment_order_line(
        self, contract_id, invoice_move_line, account_payment_order_id
    ):
        if invoice_move_line.currency_id:
            currency_id = invoice_move_line.currency_id.id
            amount_currency = invoice_move_line.amount_residual_currency
        else:
            currency_id = invoice_move_line.company_id.currency_id.id
            amount_currency = invoice_move_line.amount_residual
        values = {
            "partner_id": contract_id.partner_id.id,
            "move_line_id": invoice_move_line.id,
            "date": datetime.now().date(),
            "currency_id": currency_id,
            "amount_currency": amount_currency,
            "communication_type": "normal",
            "communication": invoice_move_line.move_id.name,
            "mandate_id": contract_id.mandate_id.id,
            "order_id": account_payment_order_id.id,
            "partner_bank_id": contract_id.res_partner_bank_id.id,
        }
        self.env["account.payment.line"].sudo().create(values)

    def _create_recurring_payments(self, invoices, contract_id):
        """
        Generic method for each payment mode
        :param invoices:
        :return:
        """
        self.ensure_one()
        if self.payment_method_id.code == "ACH-In":
            active_payment_order = self.env["account.payment.order"].search(
                [
                    (
                        "journal_id",
                        "=",
                        contract_id.payment_mode_id.fixed_journal_id.id,
                    ),
                    ("state", "=", "draft"),
                    ("payment_type", "=", "inbound"),
                    (
                        "payment_mode_id.payment_method_id.code",
                        "=",
                        self.payment_method_id.code,
                    ),
                ],
                limit=1,
            )

            if active_payment_order:
                for invoice in invoices:
                    invoice_move_line = self.get_reconciled_line_from_moves(invoice)
                    self.create_payment_order_line(
                        contract_id=contract_id,
                        invoice_move_line=invoice_move_line,
                        account_payment_order_id=active_payment_order,
                    )
            else:
                company_partner_bank_id = (
                    self.env["res.partner.bank"]
                    .sudo()
                    .search(
                        [("partner_id", "=", contract_id.company_id.partner_id.id)],
                        limit=1,
                    )
                )
                account_payment_order = (
                    self.env["account.payment.order"]
                    .sudo()
                    .create(
                        {
                            "payment_mode_id": self.id,
                            "journal_id": self.fixed_journal_id.id,
                            "description": "Payment order generated automatically from contract",
                            "company_id": contract_id.company_id.id,
                            "company_partner_bank_id": company_partner_bank_id.id,
                        }
                    )
                )

                for invoice in invoices:
                    invoice_move_line = self.get_reconciled_line_from_moves(invoice)
                    self.create_payment_order_line(
                        contract_id, invoice_move_line, account_payment_order
                    )

        else:
            return super()._create_recurring_payments(invoices, contract_id)

    def get_reconciled_line_from_moves(self, invoice):
        return invoice.mapped("line_ids").filtered(
            lambda line: not line.reconciled and line.account_id.reconcile == True
        )
