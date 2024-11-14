from odoo import models, fields, api
from odoo.exceptions import UserError
import stripe


class SaleSubscriptionPaymentWizard(models.TransientModel):
    _name = "sale.subscription.payment.wizard"
    _description = "Wizard para Tokenizar Método de Pago de Suscripción"

    subscription_id = fields.Many2one(
        "sale.subscription", string="Suscripción", required=True
    )
    card_number = fields.Char(string="Número de Tarjeta", required=True)
    card_exp_month = fields.Char(string="Mes de Expiración (MM)", required=True)
    card_exp_year = fields.Char(string="Año de Expiración (YYYY)", required=True)
    card_cvc = fields.Char(string="CVC", required=True)

    @api.model
    def default_get(self, fields):
        res = super(SaleSubscriptionPaymentWizard, self).default_get(fields)
        subscription_id = self.env.context.get("active_id")
        if subscription_id:
            res["subscription_id"] = subscription_id
        return res

    def action_create_token(self):
        """Crea un token en Stripe usando los datos de la tarjeta y lo guarda en la suscripción."""
        provider = self.env["payment.provider"].search(
            [("code", "=", "stripe")],
        )
        stripe.api_key = provider.stripe_secret_key

        # Intenta crear un token en Stripe
        try:
            token = stripe.Token.create(
                card={
                    "number": self.card_number,
                    "exp_month": self.card_exp_month,
                    "exp_year": self.card_exp_year,
                    "cvc": self.card_cvc,
                },
            )

            # Vincular el token de tarjeta con el cliente en Stripe
            subscription = self.subscription_id
            if not subscription.stripe_customer:
                customer = stripe.Customer.create(
                    email=subscription.partner_id.email,
                    name=subscription.partner_id.name,
                )
                subscription.stripe_customer = customer["id"]

            # Crear y vincular el método de pago a la suscripción
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={"token": token.id},
            )
            stripe.PaymentMethod.attach(
                payment_method.id, customer=subscription.stripe_customer
            )
            stripe.Customer.modify(
                subscription.stripe_customer,
                invoice_settings={"default_payment_method": payment_method.id},
            )

            # Guardar detalles del método de pago en la suscripción
            subscription.stripe_payment_method_id = payment_method.id
            subscription.card_last4 = token.card.last4
            subscription.card_brand = token.card.brand

        except stripe.error.StripeError as e:
            raise UserError(f"Error en Stripe: {e.user_message or str(e)}")
