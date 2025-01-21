{
    "name": "ACH recurring payment from  contract",
    "summary": """
       Stripe recurring payment from  contract""",
    "author": "Binhex, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/contract",
    "category": "Contract",
    "version": "16.0.1.0.1",
    "depends": [
        "contract_recurring_payment",
        "account_banking_mandate",
        "account_banking_ach_direct_debit",
    ],
    "data": [
        "views/contract_view.xml",
    ],
    "images": ["static/src/description/icon.png"],
}
