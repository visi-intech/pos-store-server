import requests
from datetime import datetime, timedelta
import pytz
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError

class PoSOrderLine(models.Model):
    _inherit = 'pos.order.line'

    is_exchange = fields.Booelan(string='Is Exchange')