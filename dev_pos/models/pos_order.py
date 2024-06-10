import requests
from datetime import datetime, timedelta
import pytz
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError

class POSIntegration(models.Model):
    _inherit = 'pos.order'

    order_ref = fields.Char(string='Reference')

    # def action_pos_order_invoice(self):
    #     """
    #     This method is overridden to create an invoice from a POS order without posting it immediately.
    #     It also creates a stock picking for the POS order with operation type 'PoS Orders'.
    #     """
    #     AccountMove = self.env['account.move']
    #     StockPicking = self.env['stock.picking']
    #     for order in self:
    #         if not order.partner_id:
    #             raise UserError(_('Please provide a partner for the sale.'))

    #         # Create invoice values
    #         invoice_vals = order._prepare_invoice_vals()
    #         move = AccountMove.sudo().create(invoice_vals)
    #         # move.action_post()

    #         # Add the invoice lines
    #         order._create_invoice_line(move)

    #         # Link the invoice to the POS order
    #         order.write({'account_move': move.id, 'state': 'invoiced'})

    #         # Add a message to the invoice
    #         move.message_post(body=_("Invoice created from POS order %s") % order.name)

    #         operation_type = order.picking_type_id.name

    #         type = self.env['stock.picking.type'].search([('name', '=', operation_type)], limit=1)

    #         picking_vals = {
    #             'partner_id': order.partner_id.id,
    #             'picking_type_id': order.picking_type_id.id,
    #             'location_id': type.default_location_src_id.id,
    #             'location_dest_id': type.default_location_dest_id.id,
    #             'origin': order.name,
    #             'move_type': 'direct',
    #             # 'state': 'draft',
    #             'pos_order_id': order.id,
    #         }
    #         picking = StockPicking.create(picking_vals)

    #         # Create stock move lines for each product in the POS order
    #         for line in order.lines:
    #             move_line_vals = {
    #                 'name': line.product_id.name,
    #                 'product_id': line.product_id.id,
    #                 'product_uom_qty': line.qty,
    #                 'product_uom': line.product_id.uom_id.id,
    #                 'location_id': type.default_location_src_id.id,
    #                 'location_dest_id': type.default_location_dest_id.id,
    #                 'picking_id': picking.id,
    #             }
    #             self.env['stock.move'].create(move_line_vals)

    #         # Confirm the stock picking
    #         picking.button_validate()
    #         move.action_post()

    #     return {
    #         'name': _('Customer Invoice'),
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('account.view_move_form').id,
    #         'view_type': 'form',
    #         'res_model': 'account.move',
    #         'type': 'ir.actions.act_window',
    #         'res_id': move.id,
    #         'context': {'create': False},
    #     }


    # def _prepare_invoice_vals(self):
    #     self.ensure_one()
    #     invoice_vals = {
    #         'move_type': 'out_invoice',
    #         'partner_id': self.partner_id.id,
    #         'invoice_origin': self.name,
    #         'invoice_user_id': self.user_id.id,
    #         'currency_id': self.currency_id.id,
    #         # 'invoice_payment_term_id': self.payment_term_id.id,
    #         'fiscal_position_id': self.fiscal_position_id.id or self.partner_id.property_account_position_id.id,
    #         'invoice_line_ids': [],
    #     }
    #     return invoice_vals

    # def _create_invoice_line(self, move):
    #     for line in self.lines:
    #         product_tax = line.product_id.product_tmpl_id  # Menggunakan product_tmpl_id untuk mendapatkan product.template
    #         taxes_ids = [(6, 0, product_tax.taxes_id.ids)] if product_tax.taxes_id else False

    #         self.env['account.move.line'].sudo().create({
    #             'move_id': move.id,
    #             'product_id': line.product_id.id,
    #             'name': line.name,
    #             'quantity': line.qty,
    #             'product_uom_id': line.product_id.uom_id.id,
    #             'price_unit': line.price_unit,
    #             'tax_ids': taxes_ids,
    #             # 'account_id': line.get_account_id(),
    #         })
