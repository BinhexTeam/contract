import logging

from odoo import fields

from odoo.addons.subscription_recurring_payment_stripe.tests.common import (
    SubscriptionRecurringPaymentStripe,
)

_logger = logging.getLogger(__name__)


class TestAccountMove(SubscriptionRecurringPaymentStripe):
    def test_cron_process_due_invoices(self):
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
        if subscription.charge_automatically:
            invoice.cron_process_due_invoices()

            # Verify that the payment has been registered correctly
            self.assertEqual(invoice.state, "posted", "Invoice not posted.")
            self.assertEqual(invoice.payment_state, "paid", "Invoice not paid.")
