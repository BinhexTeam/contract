import logging

import stripe

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_register_payment(self):
        """
        Override `action_register_payment` to automatically process Stripe
        payment on subscriptions.
        """
        for invoice in self:
            # Find the subscription associated with the invoice, if it exists
            subscription = invoice.subscription_id

            # Check if the subscription is recurring and has a payment method
            if subscription and subscription.charge_automatically:
                provider = subscription.provider_id
                stripe.api_key = provider.stripe_secret_key
                token = self.env["payment.token"].search(
                    [("provider_id", "=", provider.id)]
                )
                try:
                    # Create the PaymentIntent and confirm it immediately
                    payment_intent = stripe.PaymentIntent.create(
                        # Stripe usa centavos
                        amount=int(invoice.amount_total * 100),
                        currency=invoice.currency_id.name.lower(),
                        customer=token.provider_ref,
                        payment_method=token.stripe_payment_method,
                        # Para pagos automáticos sin intervención del usuario
                        off_session=True,
                        # Confirmar el PaymentIntent inmediatamente
                        confirm=True,
                        metadata={"odoo_invoice_id": str(invoice.id)},
                    )

                    # Manejar el resultado del PaymentIntent
                    if payment_intent["status"] == "succeeded":
                        # If the payment is successful, record the payment on the invoice
                        Payment = self.env["account.payment"].sudo()
                        payment_vals = {
                            "journal_id": self.env["account.journal"]
                            .search([("type", "=", "bank")], limit=1)
                            .id,
                            "amount": invoice.amount_total,
                            "payment_type": "inbound",
                            "partner_type": "customer",
                            "partner_id": invoice.partner_id.id,
                            "payment_method_id": self.env.ref(
                                "account.account_payment_method_manual_in"
                            ).id,
                            "ref": f"Stripe PaymentIntent {payment_intent['id']}",
                        }
                        payment = Payment.create(payment_vals)
                        payment.action_post()
                        invoice.payment_state = "paid"
                    elif payment_intent["status"] == "requires_action":
                        raise UserError(
                            _("Payment requires additional authentication (3D Secure).")
                        )
                    else:
                        raise UserError(
                            f"Stripe payment error: {payment_intent['status']}"
                        )

                except stripe.StripeError as e:
                    raise UserError(f"Stripe error: {e}")

            else:
                return super(AccountMove, self).action_register_payment()

    @api.model
    def cron_process_due_invoices(self):
        """Process payment of overdue invoices for recurring subscriptions."""

        for invoice in self:
            # Find the subscription associated with the invoice
            subscription = invoice.subscription_id

            # Check if it's a recurring subscription with Stripe
            if subscription and subscription.charge_automatically:
                try:
                    # Register the payment
                    invoice.action_register_payment()
                except Exception as e:
                    _logger.error(f"Error Processing Due Invoices: {str(e)}")
