import requests
from datetime import datetime, timedelta
import pytz
from odoo import models, fields, api, SUPERUSER_ID
from odoo.exceptions import UserError

class POSIntegration(models.Model):
    _inherit = 'pos.order'

    order_ref = fields.Char(string='Reference')

    def update_pos_order(self):
        orders = self.env['pos.order'].search([('state', '=', 'draft')])
        for order in orders:
            ids = [3, 5]
            for line in order.lines:  # Accessing pos.order.line records related to pos.order
                line.write({'tax_ids_after_fiscal_position': [(6, 0, ids)]})