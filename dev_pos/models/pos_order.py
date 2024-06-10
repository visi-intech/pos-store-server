import requests
from datetime import datetime, timedelta
import pytz
from odoo import models, fields, api, SUPERUSER_ID
from odoo.exceptions import UserError

class POSIntegration(models.Model):
    _inherit = 'pos.order'

    vit_trxid = fields.Char(string='Transaction ID')
    is_integrated = fields.Boolean(string="Integrated", default=False)