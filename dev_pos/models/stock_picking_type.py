from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
  

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    @api.model
    def create(self, vals):
        # Panggil metode create asli untuk membuat record
        record = super(StockPickingType, self).create(vals)
        # Ambil ID dari record yang baru saja dibuat
        sequence_id = record.sequence_id

        sequences = self.env['ir.sequence'].search([('id', '=', sequence_id.id)])

        if sequences:
            for sequence in sequences:
                sequence.write({
                    'warehouse_name': record.warehouse_id.name,
                })
        
        return record

