import logging

from odoo import fields

from odoo.addons.subscription_recurring_payment_stripe.tests.common import (
    SubscriptionRecurringPaymentStripe,
)

_logger = logging.getLogger(__name__)


class TestAccountMove(SubscriptionRecurringPaymentStripe):
    def test_process_due_invoices(self):
        # Create a test subscription
        subscription = self.sub1

        # Create a test invoice associated with the subscription
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": subscription.partner_id.id,
                "invoice_date_due": fields.Date.today(),
                "subscription_id": subscription.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_1.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        # Execute the cron_process_due_invoices method
        # Post the invoice
        invoice.action_post()

        # Prepare payment data
        provider = invoice.subscription_id.provider_id
        payment_method = self.env["account.payment.method"].search(
            [("code", "=", provider.code)]
        )
        method_line = self.env["account.payment.method.line"].create(
            {
                "payment_provider_id": provider.id,
                "payment_method_id": payment_method.id,
                "journal_id": self.bank_journal.id,
            }
        )
        payment_register = self.env["account.payment.register"]

        payment_vals = {
            "currency_id": invoice.currency_id.id,
            "journal_id": self.bank_journal.id,
            "company_id": invoice.company_id.id,
            "partner_id": invoice.partner_id.id,
            "communication": invoice.name,
            "payment_type": "inbound",
            "partner_type": "customer",
            "payment_difference_handling": "open",
            "writeoff_label": "Write-Off",
            "payment_date": fields.Date.today(),
            "amount": invoice.amount_total,
            "payment_method_line_id": method_line.id,
            "payment_token_id": subscription.payment_token_id.id,
        }
        # Create payment and pay the invoice
        payment_register.with_context(
            active_model="account.move",
            active_ids=invoice.ids,
            active_id=invoice.id,
        ).create(payment_vals).action_create_payments()

        # Verify that the payment has been registered correctly
        self.assertEqual(invoice.state, "posted", "Invoice not posted.")
        self.assertEqual(invoice.payment_state, "paid", "Invoice not paid.")
