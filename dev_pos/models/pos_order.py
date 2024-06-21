import requests
from datetime import datetime, timedelta
import pytz
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError

class POSIntegration(models.Model):
    _inherit = 'pos.order'

    order_ref = fields.Char(string='Reference')


    def action_pos_order_invoice(self):
        """
        This method is overridden to create an invoice from a POS order without posting it immediately.
        It also creates a stock picking for the POS order with operation type 'PoS Orders'.
        """
        for order in self:
            if any(line.qty < 0 for line in self.lines):
                if not order.partner_id:
                    raise UserError(_('Please provide a partner for the sale.'))

                # self.ensure_one()
                invoice_refund_vals = {
                    'move_type': 'out_invoice',
                    'ref': self.name,
                    'partner_id': self.partner_id.id,
                    'invoice_origin': self.name,
                    'invoice_user_id': self.user_id.id,
                    'currency_id': self.currency_id.id,
                    # 'invoice_payment_term_id': self.payment_term_id.id,
                    'fiscal_position_id': self.fiscal_position_id.id or self.partner_id.property_account_position_id.id,
                    'invoice_line_ids': [],
                }
                move_refund = self.env['account.move'].sudo().create(invoice_refund_vals)
                order._create_invoice_line(move_refund)

                # Link the invoice to the POS order
                order.write({'account_move': move_refund.id, 'state': 'invoiced'})

                # Add a message to the invoice
                move_refund.message_post(body=_("Invoice created from POS order %s") % order.name)
                refund_operation_type = order.picking_type_id.name

                refund_type = self.env['stock.picking.type'].search([('name', '=', refund_operation_type)], limit=1)

                picking_vals = {
                    'partner_id': order.partner_id.id,
                    'picking_type_id': order.picking_type_id.id,
                    'location_id': refund_type.default_location_src_id.id,
                    'location_dest_id': refund_type.default_location_dest_id.id,
                    'origin': order.name,
                    'move_type': 'direct',
                    # 'state': 'draft',
                    'pos_order_id': order.id,
                }
                picking_in = self.env['stock.picking'].create(picking_vals)

                # Create stock move lines for each product in the POS order
                for res in order.lines.filtered(lambda l: not l.is_exchange):
                    move_line_vals = {
                        'name': res.product_id.name,
                        'product_id': res.product_id.id,
                        'product_uom_qty': abs(res.qty),
                        'quantity': abs(res.qty),
                        'product_uom': res.product_id.uom_id.id,
                        'location_id': refund_type.default_location_src_id.id,
                        'location_dest_id': refund_type.default_location_dest_id.id,
                        'picking_id': picking_in.id,
                    }
                    self.env['stock.move'].create(move_line_vals)

                # Confirm the stock picking
                picking_in.button_validate()

                picking_refund_inv_vals = {
                    'partner_id': order.partner_id.id,
                    'picking_type_id': order.picking_type_id.id,
                    'location_id':refund_type.default_location_dest_id.id,
                    'location_dest_id': refund_type.default_location_src_id.id,
                    'origin': order.name,
                    'move_type': 'direct',
                    # 'state': 'draft',
                    'pos_order_id': order.id,
                }
                picking_out = self.env['stock.picking'].create(picking_refund_inv_vals)

                # Create stock move lines for each product in the POS order
                for refund_inv in order.lines.filtered(lambda l: l.is_exchange):
                    move_line_refund_inv_vals = {
                        'name': refund_inv.product_id.name,
                        'product_id': refund_inv.product_id.id,
                        'product_uom_qty': abs(refund_inv.qty),
                        'quantity': abs(refund_inv.qty),
                        'product_uom': refund_inv.product_id.uom_id.id,
                        'location_id': refund_type.default_location_dest_id.id,
                        'location_dest_id': refund_type.default_location_src_id.id,
                        'picking_id': picking_out.id,
                    }
                    self.env['stock.move'].create(move_line_refund_inv_vals)

                # Confirm the stock picking
                picking_out.button_validate()
                move_refund.action_post()

                return {
                    'name': _('Customer Invoice'),
                    'view_mode': 'form',
                    'view_id': self.env.ref('account.view_move_form').id,
                    'view_type': 'form',
                    'res_model': 'account.move',
                    'type': 'ir.actions.act_window',
                    'res_id': move_refund.id,
                    'context': {'create': False},
                }
            else:
                if not order.partner_id:
                    raise UserError(_('Please provide a partner for the sale.'))

                self.ensure_one()
                invoice_vals = {
                    'move_type': 'out_invoice',
                    'ref': self.name,
                    'partner_id': self.partner_id.id,
                    'invoice_origin': self.name,
                    'invoice_user_id': self.user_id.id,
                    'currency_id': self.currency_id.id,
                    # 'invoice_payment_term_id': self.payment_term_id.id,
                    'fiscal_position_id': self.fiscal_position_id.id or self.partner_id.property_account_position_id.id,
                    'invoice_line_ids': [],
                }
                move = self.env['account.move'].sudo().create(invoice_vals)

                order._create_invoice_line(move)
                # Link the invoice to the POS order
                order.write({'account_move': move.id, 'state': 'invoiced'})

                # Add a message to the invoice
                move.message_post(body=_("Invoice created from POS order %s") % order.name)

                operation_type = order.picking_type_id.name

                type = self.env['stock.picking.type'].search([('name', '=', operation_type)], limit=1)

                picking_vals = {
                    'partner_id': order.partner_id.id,
                    'picking_type_id': order.picking_type_id.id,
                    'location_id': type.default_location_src_id.id,
                    'location_dest_id': type.default_location_dest_id.id,
                    'origin': order.name,
                    'move_type': 'direct',
                    # 'state': 'draft',
                    'pos_order_id': order.id,
                }
                picking = self.env['stock.picking'].create(picking_vals)

                # Create stock move lines for each product in the POS order
                for line in order.lines:
                    move_line_vals = {
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.qty,
                        'product_uom': line.product_id.uom_id.id,
                        'location_id': type.default_location_src_id.id,
                        'location_dest_id': type.default_location_dest_id.id,
                        'picking_id': picking.id,
                    }
                    self.env['stock.move'].create(move_line_vals)

                # Confirm the stock picking
                picking.button_validate()
                move.action_post()

                return {
                    'name': _('Customer Invoice'),
                    'view_mode': 'form',
                    'view_id': self.env.ref('account.view_move_form').id,
                    'view_type': 'form',
                    'res_model': 'account.move',
                    'type': 'ir.actions.act_window',
                    'res_id': move.id,
                    'context': {'create': False},
                }


    def _create_invoice_line(self, move):
        for line in self.lines:
            product_tax = line.product_id.product_tmpl_id  # Menggunakan product_tmpl_id untuk mendapatkan product.template
            taxes_ids = [(6, 0, product_tax.taxes_id.ids)] if product_tax.taxes_id else False

            self.env['account.move.line'].sudo().create({
                'move_id': move.id,
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.qty,
                'product_uom_id': line.product_id.uom_id.id,
                'price_unit': line.price_unit,
                'tax_ids': taxes_ids,
                # 'account_id': line.get_account_id(),
            })

    def action_credit_note_invoice(self):
        """
        This method is overridden to create an invoice from a POS order without posting it immediately.
        It also creates a stock picking for the POS order with operation type 'PoS Orders'.
        """
        AccountMove = self.env['account.move']
        StockPicking = self.env['stock.picking']
        for order in self:
            if not order.partner_id:
                raise UserError(_('Please provide a partner for the sale.'))

            # self.ensure_one()
            invoice_vals = {
                'move_type': 'out_refund',
                'ref': self.name,
                'partner_id': self.partner_id.id,
                'invoice_origin': self.name,
                'invoice_user_id': self.user_id.id,
                'currency_id': self.currency_id.id,
                'fiscal_position_id': self.fiscal_position_id.id or self.partner_id.property_account_position_id.id,
                'invoice_line_ids': [],
            }
            move = AccountMove.sudo().create(invoice_vals)

            # Add the invoice lines
            order._create_credit_note_line(move)

            # Link the invoice to the POS order
            order.write({'account_move': move.id, 'state': 'invoiced'})

            # Add a message to the invoice
            move.message_post(body=_("Invoice created from POS order %s") % order.name)

            operation_type = order.picking_type_id.name

            type = self.env['stock.picking.type'].search([('name', '=', operation_type)], limit=1)

            # Create stock picking for outgoing products
            picking_out_vals = {
                'partner_id': order.partner_id.id,
                'picking_type_id': order.picking_type_id.id,
                'location_id': type.default_location_src_id.id,
                'location_dest_id': type.default_location_dest_id.id,
                'origin': order.name,
                'move_type': 'direct',
                'pos_order_id': order.id,
            }
            picking_out = StockPicking.create(picking_out_vals)

            # Create stock move lines for each product in the POS order
            for line in order.lines:
                move_line_out_vals = {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': type.default_location_src_id.id,
                    'location_dest_id': type.default_location_dest_id.id,
                    'picking_id': picking_out.id,
                }
                self.env['stock.move'].create(move_line_out_vals)

            picking_out.button_validate()
            move.action_post()

            # Create stock picking for incoming products (sample code, adjust as needed)
            picking_refund_vals = {
                'partner_id': order.partner_id.id,
                'picking_type_id': order.picking_type_id.id,
                'location_id': type.default_location_dest_id.id,
                'location_dest_id': type.default_location_src_id.id,
                'origin': order.name,
                'move_type': 'direct',
                'pos_order_id': order.id,
            }
            picking_refund = StockPicking.create(picking_refund_vals)

            # Create stock move lines for exchange products
            for refunds in order.lines.filtered(lambda l: l.is_exchange):
                move_line_refund_vals = {
                    'name': refunds.product_id.name,
                    'product_id': refunds.product_id.id,
                    'product_uom_qty': abs(refunds.qty),
                    'quantity': abs(refunds.qty),
                    'product_uom': refunds.product_id.uom_id.id,
                    'location_id': type.default_location_dest_id.id,
                    'location_dest_id': type.default_location_src_id.id,
                    'picking_id': picking_refund.id,
                }
                self.env['stock.move'].create(move_line_refund_vals)

            picking_refund.button_validate()

        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'view_type': 'form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'res_id': move.id,
            'context': {'create': False},
        }


    def _create_credit_note_line(self, move):
        for line in self.lines:
            product_tax = line.product_id.product_tmpl_id  # Menggunakan product_tmpl_id untuk mendapatkan product.template
            taxes_ids = [(6, 0, product_tax.taxes_id.ids)] if product_tax.taxes_id else False

            if not line.is_exchange:
                quantity = -line.qty
                price_unit = abs(line.price_unit)
            else:
                quantity = abs(line.qty)
                price_unit = abs(line.price_unit)

            self.env['account.move.line'].sudo().create({
                'move_id': move.id,
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': quantity,
                'product_uom_id': line.product_id.uom_id.id,
                'price_unit': price_unit,
                'tax_ids': taxes_ids,
                # 'account_id': line.get_account_id(),
            })
