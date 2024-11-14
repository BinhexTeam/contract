# -*- coding: utf-8 -*-
import logging
import stripe

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def stripe_pay_invoice(self):
        """Paga la factura en Stripe si `is_recurrent` está activado en la suscripción."""
        for invoice in self:
            subscription = invoice.invoice_origin and self.env[
                "sale.subscription"
            ].search([("code", "=", invoice.invoice_origin)], limit=1)
            if (
                subscription
                and subscription.is_recurrent
                and subscription.stripe_customer
            ):
                provider = self.env["payment.provider"].search(
                    [("code", "=", "stripe")],
                )
                stripe.api_key = provider.stripe_secret_key
                try:
                    # Crea un PaymentIntent en Stripe para el monto de la factura
                    payment_intent = stripe.PaymentIntent.create(
                        amount=int(
                            invoice.amount_total * 100
                        ),  # Stripe maneja montos en centavos
                        currency=invoice.currency_id.name.lower(),
                        customer=subscription.stripe_customer,
                        payment_method="pm_1QL6VqRwXzxKyS2wEWj2Js5U",
                        payment_method_types=["card"],
                        description=f"Odoo Invoice {invoice.name}",
                        metadata={"odoo_invoice_id": invoice.id},
                    )

                    # Confirmar el pago y actualizar el estado de la factura en Odoo
                    if payment_intent["status"] == "succeeded":
                        invoice.action_post()
                        invoice.payment_state = "paid"
                    else:
                        raise Exception(
                            f"Error en el pago de Stripe: {payment_intent['status']}"
                        )

                except stripe.error.StripeError as e:
                    raise UserError(f"Stripe error: {e.user_message or str(e)}")

    def action_post(self):
        """Sobreescribe el método `action_post` para procesar el pago automático si `is_recurrent` está activo."""
        res = super(AccountMove, self).action_post()
        for invoice in self:
            subscription = self.env["sale.subscription"].search(
                [("code", "=", invoice.invoice_origin)], limit=1
            )
            if subscription and subscription.is_recurrent:
                invoice.stripe_pay_invoice()
        return res
