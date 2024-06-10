from odoo import models, fields, api

class CashbackSelloutImportSerialWizard(models.TransientModel):
    _name = 'cashback.sellout.import.serial.wizard'
    _description = 'Import Serial Number Wizard'

    serial_number = fields.Text(string='Serial Number')

    def action_import(self):
        sellout_id = self.env.context.get('default_sellout_id')
        if sellout_id:
            sellout_line = self.env['cashback.sellout.line'].browse(sellout_id)
            serial_numbers = self.serial_number.strip().split('\n')
            for serial in serial_numbers:
                self.env['cashback.sellout.serial.line'].create({
                    'sellout_line_id': sellout_line.id,
                    'serial_number': serial.strip(),
                    'quantity': 1.0,  # Default quantity, adjust as needed
                })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cashback.sellout.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('dev_pos.view_cashback_sellout_wizard_form').id,  # Adjust view id as needed
            'target': 'new',
            'context': {'default_sellout_id': sellout_id}
        }

class CashbackSellout(models.Model):
    _name = 'cashback.sellout'

    doc_num = fields.Char(string='Document Number')
    partner_id = fields.Many2one('res.partner', string='Customer')
    doc_date = fields.Date(string='Date')
    sellout_ids = fields.One2many('cashback.sellout.line', 'sellout_id', string='Sellout Lines')

class CashbackSelloutLine(models.Model):
    _name = 'cashback.sellout.line'

    sellout_id = fields.Many2one('cashback.sellout', string='Sellout')
    product_id = fields.Many2one('product.product', string='Product')
    serial_line_ids = fields.One2many('cashback.sellout.serial.line', 'sellout_line_id', string='Serial Lines')

    def action_open_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cashback.sellout.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('dev_pos.view_cashback_sellout_wizard_form').id,
            'target': 'new',
            'context': {'default_sellout_id': self.id}
        }

class CashbackSelloutSerialLine(models.Model):
    _name = 'cashback.sellout.serial.line'

    sellout_line_id = fields.Many2one('cashback.sellout.line', string='Sellout Line')
    serial_number = fields.Char(string='Serial Number')
    quantity = fields.Float(string='Quantity')

class CashbackSelloutWizard(models.TransientModel):
    _name = 'cashback.sellout.wizard'

    sellout_id = fields.Many2one('cashback.sellout.line', string='Sellout Line')
    wizard_line_ids = fields.One2many('cashback.sellout.wizard.line', 'wizard_id', string='Wizard Lines')

    @api.model
    def default_get(self, fields):
        res = super(CashbackSelloutWizard, self).default_get(fields)
        sellout_id = self.env.context.get('default_sellout_id')
        if sellout_id:
            sellout_line = self.env['cashback.sellout.line'].browse(sellout_id)
            res.update({
                'sellout_id': sellout_line.id,
                'wizard_line_ids': [(0, 0, {
                    'serial_number': line.serial_number,
                    'quantity': line.quantity
                }) for line in sellout_line.serial_line_ids]
            })
        return res

    def action_save(self):
        sellout_line = self.sellout_id
        existing_lines = {line.serial_number: line for line in sellout_line.serial_line_ids}

        # Track serial numbers that should remain after save
        remaining_serial_numbers = set()

        for line in self.wizard_line_ids:
            if line.serial_number in existing_lines:
                existing_lines[line.serial_number].quantity = line.quantity
                remaining_serial_numbers.add(line.serial_number)
            else:
                self.env['cashback.sellout.serial.line'].create({
                    'sellout_line_id': sellout_line.id,
                    'serial_number': line.serial_number,
                    'quantity': line.quantity,
                })
                remaining_serial_numbers.add(line.serial_number)

        # Delete lines that are not in remaining_serial_numbers
        for serial_number, line in existing_lines.items():
            if serial_number not in remaining_serial_numbers:
                line.unlink()

        # Clear the wizard lines
        self.wizard_line_ids = [(5, 0, 0)]

        return {'type': 'ir.actions.act_window_close'}

    def action_open_import_serial_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cashback.sellout.import.serial.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('dev_pos.view_cashback_sellout_import_serial_wizard_form').id,
            'target': 'new',
            'context': {'default_sellout_id': self.sellout_id.id}
        }

class CashbackSelloutWizardLine(models.TransientModel):
    _name = 'cashback.sellout.wizard.line'

    wizard_id = fields.Many2one('cashback.sellout.wizard', string='Wizard')
    serial_number = fields.Char(string='Serial Number')
    quantity = fields.Float(string='Quantity')


