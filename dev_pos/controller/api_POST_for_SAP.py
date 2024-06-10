from odoo import http
from odoo.http import request
from datetime import datetime

class POSTMasterItem(http.Controller):
    @http.route('/api/master_item', type='http', auth='public', methods=['POST'], csrf=False)
    def post_master_item(self, **kw):
        data = request.httprequest.get_json()
        product_name = data.get('product_name')
        product_code = data.get('product_code')
        product_type = data.get('product_type')
        invoicing_policy = data.get('invoice_policy')
        create_date = data.get('create_date')
        sales_price = data.get('sales_price')
        cost = data.get('cost')
        uom_id = data.get('uom_id')
        uom_po_id = data.get('uom_po_id')
        categ_id = data.get('categ_id')

        items = request.env['product.template'].sudo().create({
            'name': product_name,
            'default_code': product_code,
            'detailed_type': product_type,
            'invoice_policy': invoicing_policy,
            'create_date': create_date,
            'list_price': sales_price,
            'standard_price': cost,
            'uom_id': uom_id,
            'uom_po_id': uom_po_id,
            'categ_id': categ_id,
        })
        
        return {
            'status': 200,
            'message': 'success',
            'item_id': items.id,
            'item_name': items.name,
        }

class POSTPricelist(http.Controller):
    @http.route('/api/master_pricelist', type='json', auth='public', methods=['POST'], csrf=False)
    def post_pricelist(self, **kw):
        data = request.httprequest.get_json()
        name = data.get('name')
        currency_id = data.get('currency_id')
        items_lines = data.get('pricelist_ids', [])
        items_lines_data = []

        for line in items_lines:
            product_code = line.get('product_code')
            product_uom_qty = line.get('quantity')
            conditions = line.get('conditions')
            compute_price = line.get('compute_price')
            percent_price = line.get('percent_price')
            fixed_price = line.get('fixed_price')
            price = line.get('price')
            date_start = line.get('date_start')
            date_end = line.get('date_end')

            # Convert datetime strings to the correct format
            date_start = datetime.strptime(date_start.split('.')[0], '%Y-%m-%d %H:%M:%S')
            date_end = datetime.strptime(date_end.split('.')[0], '%Y-%m-%d %H:%M:%S')

            # Search for the product by default_code
            product = request.env['product.product'].sudo().search([('default_code', '=', product_code)], limit=1)

            if product:
                # Create order line data with the correct format
                order_line_data = {
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'applied_on': conditions,
                    'compute_price': compute_price,
                    'percent_price': percent_price,
                    'fixed_price': fixed_price,
                    'min_quantity': product_uom_qty,
                    'price': price,
                    'date_start': date_start,
                    'date_end': date_end,
                }
                items_lines_data.append(order_line_data)

        # Create the pricelist with the prepared item lines
        price_list = request.env['product.pricelist'].sudo().create({
            'name': name,
            'currency_id': currency_id,
            'item_ids': [(0, 0, line_data) for line_data in items_lines_data],
        })

        return {
            'status': 200,
            'message': 'success',
            'price_list_id': price_list.id,
            'price_list_name': price_list.name,
        }

class POSTMasterCustomer(http.Controller):
    @http.route('/api/master_customer', type='json', auth='public', methods=['POST'], csrf=False)
    def post_master_customer(self, **kw):
        data = request.httprequest.get_json()
        name = data.get('name')
        street = data.get('street')
        phone = data.get('phone')
        email = data.get('email')
        mobile = data.get('mobile')
        website = data.get('website')
        title = data.get('title')    

        customers = request.env['res.partner'].sudo().create({
            'name': name,
            'street': street,
            'phone': phone,
            'email': email,
            'mobile': mobile,
            'website': website,
            'title': title
        })

        return {
            'status': 200,
            'message': 'success',
            'customer_id': customers.id,
            'customer_name': customers.name,
        }
    
class POSTMasterWarehouse(http.Controller):
    @http.route('/api/master_warehouse', type='json', auth='public', methods=['POST'], csrf=False)
    def post_master_warehouse(self, **kw):
        data = request.httprequest.get_json()
        name = data.get('name')
        location_id = data.get('location_id')
        location_type = data.get('location_type')
        scrap_location = data.get('scrap_location')
        return_location = data.get('return_location')
        replenish_location = data.get('replenish_location')

        locations = request.env['stock.location'].sudo().create({
            'name': name,
            'location_id': location_id,
            'usage': location_type,
            'scrap_location': scrap_location,
            'return_location': return_location,
            'replenish_location': replenish_location
        })
        
        return {
            'status': 200,
            'message': 'success',
            'location_id': locations.id,
            'location_name': locations.name,
        }

class POSTGoodsReceipt(http.Controller):
    @http.route('/api/goods_receipt', type='json', auth='public', methods=['POST'], csrf=False)
    def post_goods_receipt(self, **kw):
        data = request.httprequest.get_json()
        customer_id = data.get('customer_id')
        picking_type_id = data.get('picking_type_id')
        location_id = data.get('location_id')
        location_dest_id = data.get('location_dest_id')
        scheduled_date = data.get('scheduled_date')
        date_done = data.get('date_done')
        source_document = data.get('origin')
        is_integrated = data.get('is_integrated')
        items_lines = data.get('move_ids_without_package', [])
        items_lines_data = []

        for line in items_lines:
            product_code = line.get('product_code')
            demand_quantity = line.get('demand')
            quantity = line.get('quantity')
       
            product = request.env['product.product'].sudo().search([('default_code', '=', product_code)], limit=1)

            if product:
                # Create order line data with the correct format
                receipt_line_data = {
                    'product_id': product.id,
                    'product_uom_qty': demand_quantity,
                    'quantity': quantity,
                }
                items_lines_data.append(receipt_line_data)

        # Create the pricelist with the prepared item lines
        goods_receipt = request.env['stock.picking'].sudo().create({
            'partner_id': customer_id,
            'picking_type_id': picking_type_id,
            'location_dest_id': location_dest_id,
            'scheduled_date': scheduled_date,
            'date_done': date_done,
            'origin': source_document,
            'is_integrated': is_integrated,
            'item_ids': [(0, 0, line_data) for line_data in items_lines_data],
        })

        return {
            'status': 200,
            'message': 'success',
            'goods_receipt_id': goods_receipt.id,
            'goods_receipt': goods_receipt.name,
        }
    
class POSTGoodsIssuet(http.Controller):
    @http.route('/api/goods_issue', type='json', auth='public', methods=['POST'], csrf=False)
    def post_goods_issue(self, **kw):
        data = request.httprequest.get_json()
        customer_id = data.get('customer_id')
        picking_type_id = data.get('picking_type_id')
        location_dest_id = data.get('location_dest_id')
        scheduled_date = data.get('scheduled_date')
        date_done = data.get('date_done')
        source_document = data.get('origin')
        is_integrated = data.get('is_integrated')
        items_lines = data.get('move_ids_without_package', [])
        items_lines_data = []

        for line in items_lines:
            product_code = line.get('product_code')
            demand_quantity = line.get('demand')
            quantity = line.get('quantity')
       
            product = request.env['product.product'].sudo().search([('default_code', '=', product_code)], limit=1)

            if product:
                # Create order line data with the correct format
                issue_line_data = {
                    'product_id': product.id,
                    'product_uom_qty': demand_quantity,
                    'quantity': quantity,
                }
                items_lines_data.append(issue_line_data)

        # Create the pricelist with the prepared item lines
        goods_issue = request.env['stock.picking'].sudo().create({
            'partner_id': customer_id,
            'picking_type_id': picking_type_id,
            'location_dest_id': location_dest_id,
            'scheduled_date': scheduled_date,
            'date_done': date_done,
            'origin': source_document,
            'is_integrated': is_integrated,
            'item_ids': [(0, 0, line_data) for line_data in items_lines_data],
        })

        return {
            'status': 200,
            'message': 'success',
            'goods_issue_id': goods_issue.id,
            'goods_issue': goods_issue.name,
        }