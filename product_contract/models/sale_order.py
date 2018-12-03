# Copyright 2017 LasLabs Inc.
# Copyright 2018 ACSONE SA/NV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_contract = fields.Boolean(
        string='Is a contract', compute='_compute_is_contract'
    )
    contract_count = fields.Integer(compute='_compute_contract_count')

    @api.depends('order_line')
    def _compute_is_contract(self):
        self.is_contract = any(self.order_line.mapped('is_contract'))

    @api.multi
    def _prepare_contract_value(self, contract_template):
        self.ensure_one()
        return {
            'name': '{template_name}: {sale_name}'.format(
                template_name=contract_template.name, sale_name=self.name
            ),
            'partner_id': self.partner_id.id,
            'recurring_invoices': True,
            'contract_template_id': contract_template.id,
        }

    @api.multi
    def action_confirm(self):
        """ If we have a contract in the order, set it up """
        contract_env = self.env['account.analytic.account']
        for rec in self.filtered('is_contract'):
            line_to_create_contract = rec.order_line.filtered(
                lambda r: not r.contract_id and r.product_id.is_contract
            )
            line_to_update_contract = rec.order_line.filtered(
                lambda r: r.contract_id and r.product_id.is_contract
            )
            for contract_template in line_to_create_contract.mapped(
                'product_id.contract_template_id'
            ):
                order_lines = line_to_create_contract.filtered(
                    lambda r: r.product_id.contract_template_id
                    == contract_template
                )
                contract = contract_env.create(
                    rec._prepare_contract_value(contract_template)
                )
                contract._onchange_contract_template_id()
                order_lines.create_contract_line(contract)
                order_lines.write({'contract_id': contract.id})
            for line in line_to_update_contract:
                line.create_contract_line(line.contract_id)
        return super(SaleOrder, self).action_confirm()

    @api.multi
    @api.depends("order_line")
    def _compute_contract_count(self):
        for rec in self:
            rec.contract_count = len(rec.order_line.mapped('contract_id'))

    @api.multi
    def action_show_contracts(self):
        self.ensure_one()
        action = self.env.ref(
            "contract.action_account_analytic_sale_overdue_all"
        ).read()[0]
        contracts = (
            self.env['account.analytic.invoice.line']
            .search([('sale_order_line_id', 'in', self.order_line.ids)])
            .mapped('contract_id')
        )
        action["domain"] = [("id", "in", contracts.ids)]
        return action
