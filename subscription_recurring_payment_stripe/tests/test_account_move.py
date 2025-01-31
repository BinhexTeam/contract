from odoo import fields
from odoo.addons.subscription_recurring_payment_stripe.tests.common import (
    SubscriptionRecurringPaymentStripe,
)

import logging

_logger = logging.getLogger(__name__)


class TestAccountMove(SubscriptionRecurringPaymentStripe):

    def test_cron_process_due_invoices(self):
        # Crear una suscripción de prueba
        subscription = self.sub1

        # Crear una factura de prueba asociada a la suscripción
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

        # Ejecutar el método cron_process_due_invoices
        invoice.cron_process_due_invoices()

        # Verificar que el pago se haya registrado correctamente
        transaction = self.env["payment.transaction"].search(
            [("reference", "=", invoice.name)], limit=1
        )
        self.assertTrue(transaction.payment_id, "Payment not found.")
        self.assertEqual(invoice.state, "posted", "Invoice not posted.")
        self.assertEqual(invoice.payment_state, "paid", "Invoice not paid.")
        self.assertEqual(
            transaction.partner_email,
            invoice.partner_id.email,
            "Partner email not set correctly.",
        )
