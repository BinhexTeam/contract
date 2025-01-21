{
    "name": "Generic contract recurring payment",
    "summary": """
        Generic Contract recurring payment".""",
    "author": "Binhex,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/contract",
    "category": "Contract",
    "version": "16.0.1.0.1",
    "depends": [
        "account",
        "contract",
        "contract_payment_mode",
        "payment",
    ],
    "license": "AGPL-3",
    "data": [
        "data/ir_cron_recurring_payment.xml",
        "views/contract_contract_view.xml",
    ],
    "images": ["static/src/description/icon.png"],
}
