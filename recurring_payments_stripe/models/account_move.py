# -*- coding: utf-8 -*-
import logging
import stripe
from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    # def stripe_pay_invoice(self):
    #     """Paga la factura en Stripe si `is_recurrent` está activado en la suscripción."""
    #     for invoice in self:
    #         subscription = invoice.invoice_date and self.env[
    #             "sale.subscription"
    #         ].search([("code", "=", invoice.invoice_date)], limit=1)
    #         if (
    #             subscription
    #             and subscription.is_recurrent
    #             and subscription.stripe_customer
    #         ):
    #             provider = self.env["payment.provider"].search(
    #                 [("code", "=", "stripe")],
    #             )
    #             stripe.api_key = provider.stripe_secret_key
    #             token = self.env["payment.token"].search(
    #                 [("provider_id", "=", provider.id)]
    #             )
    #             try:
    #                 # Crea un PaymentIntent en Stripe para el monto de la factura
    #                 payment_intent = stripe.PaymentIntent.create(
    #                     # Stripe maneja montos en centavos
    #                     amount=int(invoice.amount_total * 100),
    #                     currency=invoice.currency_id.name.lower(),
    #                     customer=token.provider_ref,
    #                     payment_method=token.stripe_payment_method,
    #                     payment_method_types=["card"],
    #                     # Para pagos automáticos sin intervención del usuario
    #                     off_session=True,
    #                     # Confirmar el PaymentIntent inmediatamente
    #                     confirm=True,
    #                     metadata={"odoo_invoice_id": invoice.id},
    #                 )

    #                 # Confirmar el pago y actualizar el estado de la factura en Odoo
    #                 if payment_intent["status"] == "succeeded":
    #                     invoice.action_post()
    #                     invoice.payment_state = "paid"
    #                 else:
    #                     raise Exception(
    #                         f"Error en el pago de Stripe: {payment_intent['status']}"
    #                     )

    #             except stripe.StripeError as e:
    #                 raise UserError(f"Stripe error: {e.user_message or str(e)}")

    # def action_post(self):
    #     """Sobreescribe el método `action_post` para procesar el pago automático si `is_recurrent` está activo."""
    #     res = super(AccountMove, self).action_post()
    #     for invoice in self:
    #         subscription = self.env["sale.subscription"].search(
    #             [("code", "=", invoice.invoice_date)], limit=1
    #         )
    #         if subscription and subscription.is_recurrent:
    #             invoice.stripe_pay_invoice()
    #     return res

    def action_register_payment(self):
        """Sobreescribe `action_register_payment` para procesar automáticamente el pago con Stripe en suscripciones."""
        for invoice in self:
            # Buscar la suscripción asociada a la factura, si existe
            subscription = self.env["sale.subscription"].search(
                [("code", "=", invoice.invoice_origin)], limit=1
            )

            # Verificar si la suscripción es recurrente y tiene método de pago en Stripe
            if subscription and subscription.is_recurrent:
                provider = self.env["payment.provider"].search(
                    [("code", "=", "stripe")],
                )
                stripe.api_key = provider.stripe_secret_key
                token = self.env["payment.token"].search(
                    [("provider_id", "=", provider.id)]
                )
                try:
                    # Crear el PaymentIntent en Stripe y confirmarlo inmediatamente
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
                        metadata={"odoo_invoice_id": invoice.id},
                    )

                    # Manejar el resultado del PaymentIntent
                    if payment_intent["status"] == "succeeded":
                        # Si el pago es exitoso, registrar el pago en la factura
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
                            "El pago requiere autenticación adicional (3D Secure)."
                        )
                    else:
                        raise UserError(
                            f"Error en el pago de Stripe: {payment_intent['status']}"
                        )

                except stripe.StripeError as e:
                    raise UserError(f"Error de Stripe: {e.user_message or str(e)}")

            else:
                # Si no es una suscripción recurrente o no tiene método de pago en Stripe, llama al método original
                return super(AccountMove, self).action_register_payment()

    @api.model
    def cron_process_due_invoices(self):
        """Procesa el pago de facturas vencidas para suscripciones recurrentes."""
        # Obtener la fecha de hoy
        today = date.today()

        # Buscar facturas de suscripciones recurrentes que vencen hoy y están abiertas
        invoices = self.search(
            [
                ("state", "=", "posted"),
                ("payment_state", "=", "not_paid"),
            ]
        )

        for invoice in invoices:
            # Buscar la suscripción asociada a la factura
            subscription = self.env["sale.subscription"].search(
                [("code", "=", invoice.invoice_origin)], limit=1
            )

            # Verificar si es una suscripción recurrente con Stripe
            if subscription and subscription.is_recurrent:
                try:
                    # Intentar registrar el pago en la factura
                    invoice.action_register_payment()
                except Exception as e:
                    # Capturar excepciones en caso de error en el registro de pago
                    _logger.error(
                        f"Error al procesar el pago de la factura {invoice.id}: {str(e)}"
                    )
