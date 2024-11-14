# -*- coding: utf-8 -*-
import logging
import stripe

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    is_recurrent = fields.Boolean(string="Pago Automático Recurrente")
    # ID del cliente en Stripe
    stripe_customer = fields.Char(string="Stripe Customer ID")

    def create_stripe_customer(self):
        """Crea o recupera el cliente de Stripe asociado a la suscripción."""
        provider = self.env["payment.provider"].search(
            [("code", "=", "stripe")],
        )
        stripe.api_key = provider.stripe_secret_key

        if not self.stripe_customer:
            customer = stripe.Customer.create(
                email=self.env.user.email,
                name=self.env.user.name,
                metadata={"odoo_subscription": self.id},
            )
            self.stripe_customer = customer["id"]
        return self.stripe_customer

    @api.onchange("is_recurrent")
    def _onchange_is_recurrent(self):
        for record in self:
            if record.is_recurrent:
                record.create_stripe_customer()
