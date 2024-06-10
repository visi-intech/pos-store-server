from odoo import http
from odoo.http import request
import json
from .api_utils import check_authorization, paginate_records, serialize_response, serialize_error_response

class MasterCustomerPATCH(http.Controller):
    @http.route(['/api/master_customer/<int:return_id>'], type='http', auth='public', methods=['PATCH'], csrf=False)
    def update_master_customer(self, return_id, **kwargs):
        check_authorization()
        data = json.loads(request.httprequest.data)
        master_customer_id = data.get('id')
        name = data.get('name')
        street = data.get('street')
        email = data.get('email')
        mobile = data.get('mobile')
        website = data.get('website')
        title = data.get('title')
        is_integrated = data.get('is_integrated')

        if is_integrated:
            master_customer = request.env['res.partner'].sudo().browse(int(master_customer_id))
            if master_customer.exists():
                master_customer.write({'is_integrated': is_integrated,
                                       'name': name, 
                                       'street': street, 
                                       'email': email, 
                                       'mobile': mobile, 
                                       'website': website, 
                                       'title': title})
                return json.dumps({'code': 200, 'status': 'success', 'message': 'Master Customer updated successfully', 'id': return_id})
            else:
                return json.dumps({'code': 404, 'status': 'error', 'message': 'Master Customer not found', 'id': return_id})
        else:
            return json.dumps({'code': 500, 'status': 'error', 'message': 'Invalid data', 'id': return_id})
        
class MasterPricelistPATCH(http.Controller):
    @http.route(['/api/master_pricelist/<int:return_id>'], type='http', auth='public', methods=['PATCH'], csrf=False)
    def update_master_pricelist(self, return_id, **kwargs):
        try:
            check_authorization()
            data = json.loads(request.httprequest.data)
            name = data.get('name')
            currency_id = data.get('currency_id')
            pricelist_ids = data.get('pricelist_ids')

            master_pricelist = request.env['product.pricelist'].sudo().browse(int(return_id))

            # Update name and currency_id
            master_pricelist.write({
                'name': name,
                'currency_id': currency_id,
            })

            # Update pricelist_ids
            for item in pricelist_ids:
                # Fetch the specific pricelist item to be updated
                pricelist_item = request.env['product.pricelist.item'].sudo().search([('id', '=', item['id'])])
                
                # Check if the pricelist item exists before attempting to update
                if pricelist_item.exists():
                    pricelist_item.write({
                        'product_id': item['product_id'],
                        'min_quantity': item['quantity'],
                        'fixed_price': item['price'],
                        'date_start': item['date_start'],
                        'date_end': item['date_end'],
                    })
                else:
                    # Handle the case where the pricelist item does not exist (optional)
                    return json.dumps({"code": 404, "status": 'failed', "message": f"Pricelist item with ID {item['id']} not found", "id": return_id})

            return json.dumps({'code': 200, 'status': 'success', 'message': 'Master Pricelist updated successfully', 'id': return_id})

        except Exception as e:
            return json.dumps({"code": 500, "status": 'failed', "message": str(e), "id": return_id})



class ReturnPATCH(http.Controller):
    @http.route(['/api/return_order/<int:return_id>'], type='http', auth='public', methods=['PATCH'], csrf=False)
    def update_return(self, return_id, **kwargs):
        check_authorization()
        data = json.loads(request.httprequest.data)
        is_integrated = data.get('is_integrated')

        if is_integrated:
            return_order = request.env['stock.picking'].sudo().search([('id', '=', return_id), ('picking_type_id.name', '=', 'Return')], limit=1)
            if return_order.exists():
                return_order.write({'is_integrated': is_integrated})
                return json.dumps({'code': 200, 'status': 'success', 'message': 'Return Order updated successfully', 'id': return_id})
            else:
                return json.dumps({'code': 404, 'status': 'error', 'message': 'Return Order not found', 'id': return_id})
        else:
            return json.dumps({'code': 500, 'status': 'error', 'message': 'Invalid data', 'id': return_id})

class GoodsIssuePATCH(http.Controller):
    @http.route(['/api/goods_issue/<int:return_id>'], type='http', auth='public', methods=['PATCH'], csrf=False)
    def update_goods_issue_order(self, return_id, **kwargs):
        check_authorization()
        data = json.loads(request.httprequest.data)
        is_integrated = data.get('is_integrated')

        if is_integrated:
            goods_issue_order = request.env['stock.picking'].sudo().search([('id', '=', return_id), ('picking_type_id.name', '=', 'Goods Issue')], limit=1)
            if goods_issue_order.exists():
                goods_issue_order.write({'is_integrated': is_integrated})
                return json.dumps({'code': 200, 'status': 'success', 'message': 'Goods Issue updated successfully', 'id': return_id})
            else:
                return json.dumps({'code': 404, 'status': 'error', 'message': 'Goods Issue not found', 'id': return_id})
        else:
            return json.dumps({'code': 500, 'status': 'error', 'message': 'Invalid data', 'id': return_id})
        
class GoodsReceiptPATCH(http.Controller):
    @http.route(['/api/goods_receipt/<int:return_id>'], type='http', auth='public', methods=['PATCH'], csrf=False)
    def update_goods_receipt_order(self, return_id, **kwargs):
        check_authorization()
        data = json.loads(request.httprequest.data)
        is_integrated = data.get('is_integrated')

        if is_integrated:
            goods_receipt_order = request.env['stock.picking'].sudo().search([('id', '=', return_id), ('picking_type_id.name', '=', 'Goods Receipt')], limit=1)
            if goods_receipt_order.exists():
                goods_receipt_order.write({'is_integrated': is_integrated})
                return json.dumps({'code': 200, 'status': 'success', 'message': 'Goods Receipt updated successfully', 'id': return_id})
            else:
                return json.dumps({'code': 404, 'status': 'error', 'message': 'Goods Receipt not found', 'id': return_id})
        else:
            return json.dumps({'code': 500, 'status': 'error', 'message': 'Invalid data', 'id': return_id})
        
class InternalTransferPATCH(http.Controller):
    @http.route(['/api/internal_transfer/<int:return_id>'], type='json', auth='public', methods=['PATCH'], csrf=False)
    def update_internal_transfer_order(self, return_id, **kwargs):
        try:
            check_authorization()
            data = json.loads(request.httprequest.data)
            is_integrated = data.get('is_integrated')

            if is_integrated:
                internal_trasnfer_order = request.env['stock.picking'].sudo().search([('id', '=', return_id), ('picking_type_id.name', '=', 'Internal Transfer')], limit=1)
                if internal_trasnfer_order.exists():
                    internal_trasnfer_order.write({'is_integrated': is_integrated})
                    return json.dumps({'code': 200, 'status': 'success', 'message': 'Internal Transfer updated successfully', 'id': return_id})
                else:
                    return json.dumps({'code': 404, 'status': 'error', 'message': 'Internal Transfer not found', 'id': return_id})
            else:
                return json.dumps({'code': 500, 'status': 'error', 'message': 'Invalid data', 'id': return_id})
        except Exception as e:
            return serialize_error_response(str(e))

class TsOutPATCH(http.Controller):
    @http.route(['/api/transit_out/<int:return_id>'], type='http', auth='public', methods=['PATCH'], csrf=False)
    def update_transit_out_order(self, return_id, **kwargs):
        try:
            check_authorization()
            data = json.loads(request.httprequest.data)
            is_integrated = data.get('is_integrated')

            if is_integrated:
                transit_out_order = request.env['stock.picking'].sudo().search([('id', '=', return_id), ('picking_type_id.name', '=', 'Transit Out')], limit=1)
                if transit_out_order.exists():
                    transit_out_order.write({'is_integrated': is_integrated})
                    return json.dumps({'code': 200, 'status': 'success', 'message': 'Transit Out updated successfully', 'id': return_id})
                else:
                    return json.dumps({'code': 404, 'status': 'error', 'message': 'Transit Out not found', 'id': return_id})
            else:
                return json.dumps({'code': 500, 'status': 'error', 'message': 'Invalid data', 'id': return_id})
        except Exception as e:
            return serialize_error_response(str(e))
        
class TsInPATCH(http.Controller):
    @http.route(['/api/transit_in/<int:return_id>'], type='http', auth='public', methods=['PATCH'], csrf=False)
    def update_transit_in_order(self, return_id, **kwargs):
        try:
            check_authorization()
            data = json.loads(request.httprequest.data)
            is_integrated = data.get('is_integrated')

            if is_integrated:
                transit_in_order = request.env['stock.picking'].sudo().search([('id', '=', return_id), ('picking_type_id.name', '=', 'Transit Out')], limit=1)
                if transit_in_order.exists():
                    transit_in_order.write({'is_integrated': is_integrated})
                    return json.dumps({'code': 200, 'status': 'success', 'message': 'Transit In updated successfully', 'id': return_id})
                else:
                    return json.dumps({'code': 404, 'status': 'error', 'message': 'Transit In not found', 'id': return_id})
            else:
                return json.dumps({'code': 500, 'status': 'error', 'message': 'Invalid data', 'id': return_id})
        except Exception as e:
            return serialize_error_response(str(e))

class InvoicePATCH(http.Controller):
    @http.route(['/api/invoice_order/<int:return_id>'], type='http', auth='public', methods=['PATCH'], csrf=False)
    def update_invoice_order(self, return_id, **kwargs):
        try:
            check_authorization()
            data = json.loads(request.httprequest.data)
            is_integrated = data.get('is_integrated')

            if is_integrated:
                invoice_order = request.env['account.move'].sudo().search([('id', '=', return_id), ('move_type', '=', 'out_invoice')], limit=1)
                if invoice_order.exists():
                    invoice_order.write({'is_integrated': is_integrated})
                    return json.dumps({'code': 200, 'status': 'success', 'message': 'Invoice updated successfully', 'id': return_id})
                else:
                    return json.dumps({'code': 404, 'status': 'error', 'message': 'Invoice not found', 'id': return_id})
            else:
                return json.dumps({'code': 500, 'status': 'error', 'message': 'Invalid data', 'id': return_id})
        except Exception as e:
            return serialize_error_response(str(e))
        
class CreditMemoPATCH(http.Controller):
    @http.route(['/api/credit_memo/<int:return_id>'], type='http', auth='public', methods=['PATCH'], csrf=False)
    def update_credit_memo(self, return_id, **kwargs):
        try:
            check_authorization()
            data = json.loads(request.httprequest.data)
            is_integrated = data.get('is_integrated')

            if is_integrated:
                invoice_order = request.env['account.move'].sudo().search([('id', '=', return_id), ('move_type', '=', 'out_refund')], limit=1)
                if invoice_order.exists():
                    invoice_order.write({'is_integrated': is_integrated})
                    return json.dumps({'code': 200, 'status': 'success', 'message': 'Credit Memo updated successfully', 'id': return_id})
                else:
                    return json.dumps({'code': 404, 'status': 'error', 'message': 'Credit Memo not found', 'id': return_id})
            else:
                return json.dumps({'code': 500, 'status': 'error', 'message': 'Invalid data', 'id': return_id})
        except Exception as e:
            return serialize_error_response(str(e))
        
class PaymentPATCH(http.Controller):
    @http.route(['/api/payment_invoice/<int:return_id>'], type='json', auth='public', methods=['PATCH'], csrf=False)
    def update_payment_invoice(self, return_id, **kwargs):
        try:
            check_authorization()
            data = json.loads(request.httprequest.data)
            is_integrated = data.get('is_integrated')

            if is_integrated:
                payment_invoice= request.env['account.payment'].sudo().browse(return_id)
                if payment_invoice.exists():
                    payment_invoice.write({'is_integrated': is_integrated})
                    return json.dumps({'code': 200, 'status': 'success', 'message': 'Payment Invoice updated successfully', 'id': return_id})
                else:
                    return json.dumps({'code': 404, 'status': 'error', 'message': 'Payment Invoice not found', 'id': return_id})
            else:
                return json.dumps({'code': 500, 'status': 'error', 'message': 'Invalid data', 'id': return_id})
        except Exception as e:
            return serialize_error_response(str(e))

