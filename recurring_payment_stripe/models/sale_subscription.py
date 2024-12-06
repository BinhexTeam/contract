import stripe

from odoo import api, fields, models


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    charge_automatically = fields.Boolean()
    stripe_customer = fields.Char("Stripe Customer ID")
    provider_id = fields.Many2one(
        string="Provider",
        domain=[("code", "=", "stripe")],
        comodel_name="payment.provider",
    )

    def create_stripe_customer(self):
        provider = self.provider_id
        if provider:
            stripe.api_key = provider.stripe_secret_key

            if not self.stripe_customer:
                customer = stripe.Customer.create(
                    email=self.env.user.email,
                    name=self.env.user.name,
                    metadata={"odoo_subscription": str(self.id)},
                )
                self.stripe_customer = customer["id"]
            return self.stripe_customer

    @api.onchange("charge_automatically")
    def _onchange_charge_automatically(self):
        for record in self:
            if record.charge_automatically:
                record.create_stripe_customer()
