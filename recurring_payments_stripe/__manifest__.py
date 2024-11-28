{
    "name": "Recurring Payments with Stripe",
    "version": "16.0.1.0.0",
    "summary": """ Recurring Payments with Stripe """,
    "author": "Binhex, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/contract",
    "license": "AGPL-3",
    "category": "Subscription Management",
    "depends": ["subscription_oca", "payment_stripe", "payment"],
    "data": [
        "views/sale_subscription_views.xml",
        "data/ir_cron.xml",
    ],
    "installable": True,
    "auto_install": False,
}
