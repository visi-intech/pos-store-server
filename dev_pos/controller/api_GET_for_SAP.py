import json
import werkzeug.exceptions
from odoo.exceptions import ValidationError
from odoo import http, _, fields
import pytz
import re
import decimal
from .api_utils import check_authorization, paginate_records, serialize_response, serialize_error_response

class PaymentAPI(http.Controller):
    @http.route(['/api/payment_invoice/'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_payment_invoices(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, is_integrated=None, **params):
        try:
            check_authorization()

            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []

            if q:
                domain += [('name', 'ilike', str(q))]

            # if is_integrated :
            #     domain += [('is_integrated', '=', is_integrated)]

            if not createdDateFrom and not createdDateTo and not q:
                payment_invoices = http.request.env['account.move'].sudo().search([('move_type', '=', 'out_invoice'), ('payment_state', '=', 'paid'), ('state', '=', 'posted')])
                total_records = len(payment_invoices)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                           ('create_date', '<=', created_date_to.strftime(date_format)),
                           ('state', '=', 'posted'), ('move_type', '=', 'out_invoice'), ('payment_state', '=', 'paid')]

                pageSize = int(pageSize) if pageSize else 200
            if not q:
                payment_invoices, total_records = paginate_records('account.move', domain, pageSize, page)
            else:
                payment_invoices = http.request.env['account.move'].sudo().search(domain)
                total_records = len(payment_invoices)

            jakarta_tz = pytz.timezone('Asia/Jakarta')
            data_payment_invoice = []

            for payment in payment_invoices:   
                reference = payment.ref
                invoice_id = payment.id
                invoice = payment.name
                customer_id = payment.partner_id.id
                customer_name = payment.partner_id.name
                customer_code = payment.partner_id.customer_code
                data_is_integrated = payment.is_integrated

                order_pos = http.request.env['pos.order'].sudo().search([('order_ref', '=', reference), ('state', '=', 'invoiced')], limit=1)
                for record in order_pos:
                    pickings = http.request.env['stock.picking'].sudo().search([('origin', '=', record.name)])
                    location_id = pickings.location_id.id
                    location = pickings.location_id.complete_name

                payment_invoice = http.request.env['account.move'].sudo().search([('ref', 'ilike', reference), ('move_type', '=', 'entry')])
                for pays in payment_invoice:
                    payment_id = pays.id

                pos_order = http.request.env['pos.order'].search([('order_ref', '=', reference)])
                for rec in pos_order:
                    payment_name = rec.name
                for pos in pos_order.payment_ids:
                    payment_date = pos.payment_date

                    payment_date_utc = payment_date
                    payment_date_jakarta = pytz.utc.localize(payment_date_utc).astimezone(jakarta_tz)
                    payment_method_id = pos.payment_method_id.id
                    payment_method_name = pos.payment_method_id.name

                    amount = pos.amount

                    payments_data = {
                        'id': payment_id,
                        'doc_num': payment_name,
                        'is_integrated': data_is_integrated,
                        'invoice': invoice,
                        'invoice_id': invoice_id,
                        'location_id': location_id,
                        'location': location,
                        'customer_id': customer_id,
                        'customer_name': customer_name,
                        'customer_code': customer_code,
                        'payment_date': str(payment_date_jakarta),
                        'amount': amount,
                        'create_date': str(payment_date_jakarta),
                        # 'journal_id': payment_method_id,
                        # 'journal': payment_method,
                        'payment_method_id': payment_method_id,
                        'payment_method': payment_method_name
                    }
                    data_payment_invoice.append(payments_data)

            if not createdDateFrom and not createdDateTo and not q:
                total_records = len(data_payment_invoice)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_payment_invoice, total_records, total_pages)
        
        except ValidationError as ve:
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))
        
class PaymentReturnCreditMemoAPI(http.Controller):
    @http.route(['/api/payment_creditmemo/'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_payment_credit_memo(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, is_integrated=None, **params):
        try:
            check_authorization()

            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []

            if q:
                domain += [('name', 'ilike', str(q))]

            # if is_integrated :
            #     domain += [('is_integrated', '=', is_integrated)]

            if not createdDateFrom and not createdDateTo and not q:
                payment_invoices = http.request.env['account.move'].sudo().search([('move_type', '=', 'out_refund'), ('state', '=', 'posted')])
                total_records = len(payment_invoices)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                           ('create_date', '<=', created_date_to.strftime(date_format)),
                           ('state', '=', 'posted'), ('move_type', '=', 'out_refund')]

                pageSize = int(pageSize) if pageSize else 200
            if not q:
                payment_invoices, total_records = paginate_records('account.move', domain, pageSize, page)
            else:
                payment_invoices = http.request.env['account.move'].sudo().search(domain)
                total_records = len(payment_invoices)

            jakarta_tz = pytz.timezone('Asia/Jakarta')
            data_payment_invoice = []

            for payment in payment_invoices:   
                reference = payment.ref
                invoice_id = payment.id
                invoice = payment.name
                customer_id = payment.partner_id.id
                customer_name = payment.partner_id.name
                customer_code = payment.partner_id.customer_code
                data_is_integrated = payment.is_integrated

                order_pos = http.request.env['pos.order'].sudo().search([('order_ref', '=', reference), ('state', '=', 'invoiced')], limit=1)
                for record in order_pos:
                    pickings = http.request.env['stock.picking'].sudo().search([('origin', '=', record.name)])
                    location_id = pickings.location_id.id
                    location = pickings.location_id.complete_name

                payment_invoice = http.request.env['account.move'].sudo().search([('ref', 'ilike', reference), ('move_type', '=', 'entry')])
                for pays in payment_invoice:
                    payment_id = pays.id

                pos_order = http.request.env['pos.order'].search([('order_ref', '=', reference)])
                for rec in pos_order:
                    payment_name = rec.name
                for pos in pos_order.payment_ids:
                    payment_date = pos.payment_date

                    payment_date_utc = payment_date
                    payment_date_jakarta = pytz.utc.localize(payment_date_utc).astimezone(jakarta_tz)
                    payment_method_id = pos.payment_method_id.id
                    payment_method_name = pos.payment_method_id.name

                    amount = pos.amount

                    payments_data = {
                        'id': payment_id,
                        'doc_num': payment_name,
                        'is_integrated': data_is_integrated,
                        'invoice': invoice,
                        'invoice_id': invoice_id,
                        'location_id': location_id,
                        'location': location,
                        'customer_id': customer_id,
                        'customer_name': customer_name,
                        'customer_code': customer_code,
                        'payment_date': str(payment_date_jakarta),
                        'amount': amount,
                        'create_date': str(payment_date_jakarta),
                        # 'journal_id': payment_method_id,
                        # 'journal': payment_method,
                        'payment_method_id': payment_method_id,
                        'payment_method': payment_method_name
                    }
                    data_payment_invoice.append(payments_data)

            if not createdDateFrom and not createdDateTo and not q:
                total_records = len(data_payment_invoice)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_payment_invoice, total_records, total_pages)
        
        except ValidationError as ve:
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))
      
class MasterUoMAPI(http.Controller):
    @http.route(['/api/master_uom/'], type='http', auth='public', methods=['GET'], csrf=False)
    def master_UoM_get(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")

            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo and not q:
                # Handle the case when no specific filters are provided
                uom_data = http.request.env['uom.uom'].sudo().search([])
                total_records = len(uom_data)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format))]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                uom_data, total_records = paginate_records('uom.uom', domain, pageSize, page)
            else:
                uom_data = http.request.env['uom.uom'].sudo().search(domain)
                total_records = len(uom_data)

            data_uom_data = []
            for uom in uom_data:
                uoms_data = {
                    'id': uom.id,
                    'name': uom.name,
                    'category_id': uom.category_id.id,
                    'category': uom.category_id.name,
                    'uom_type': uom.uom_type,
                    'active': uom.active,
                    'create_date': str(uom.create_date),
                    'rounding': uom.rounding,    
                }
                data_uom_data.append(uoms_data)

            if not createdDateFrom and not createdDateTo and not q:
                total_records = len(data_uom_data)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_uom_data, total_records, total_pages)
        
        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))
        
class MasterCurrencyAPI(http.Controller):
    @http.route(['/api/master_currency/'], type='http', auth='public', methods=['GET'], csrf=False)
    def master_currency_get(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")

            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo and not q:
                currency_data = http.request.env['res.currency'].sudo().search([])
                total_records = len(currency_data)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format))]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                currency_data, total_records = paginate_records('res.currency', domain, pageSize, page)
            else:
                currency_data = http.request.env['res.currency'].sudo().search(domain)
                total_records = len(currency_data)

            jakarta_tz = pytz.timezone('Asia/Jakarta')
            data_currency_data = []
            for currency in currency_data:
                create_date_utc = currency.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                currencys_data = {
                    'id': currency.id,
                    'name': currency.name,
                    'full_name': currency.full_name,
                    'active': currency.active,
                    'symbol': currency.symbol,
                    'create_date': str(create_date_jakarta),
                    'currency_unit_label': currency.currency_unit_label,
                    'currency_subunit_label': currency.currency_subunit_label,
                    'rounding': currency.rounding,
                    'decimal_places': currency.decimal_places,
                    'posisition': currency.position,
                }
                data_currency_data.append(currencys_data)

            if not createdDateFrom and not createdDateTo and not q:
                total_records = len(data_currency_data)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_currency_data, total_records, total_pages)
        
        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))
              
class MasterCategoryItem(http.Controller):
    @http.route(['/api/item_category/'], type='http', auth='public', methods=['GET'], csrf=False)
    def master_category_item_get(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")

            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo and not q:
                # Handle the case when no specific filters are provided
                category_data = http.request.env['product.category'].sudo().search([])
                total_records = len(category_data)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format))]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                category_data, total_records = paginate_records('product.category', domain, pageSize, page)
            else:
                category_data = http.request.env['product.category'].sudo().search(domain)
                total_records = len(category_data)

            data_category_data = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for category in category_data:
                create_date_utc = category.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                categorys_data = {
                    'id': category.id,
                    'category_name': category.display_name,
                    'parent_category_id': category.parent_id.id,
                    'parent_category': category.parent_id.name,
                    # 'property_account_income_categ_id': category.property_account_income_categ_id.id,
                    # 'property_account_income_categ': category.property_account_income_categ_id.name,
                    # 'property_account_expense_categ_id': category.property_account_expense_categ_id.id,
                    # 'property_account_expense_categ': category.property_account_expense_categ_id.name,
                    'create_date': str(create_date_jakarta),
                    'costing_method': category.property_cost_method,
                    # 'property_valuation': category.property_valuation,
                    # 'property_stock_valuation_account_id': category.property_stock_valuation_account_id.id,
                    # 'property_stock_valuation_account': category.property_stock_valuation_account_id.name,
                    # 'property_stock_journal_id': category.property_stock_journal.id,
                    # 'property_stock_journal': category.property_stock_journal.name,
                    # 'property_stock_account_input_categ_id': category.property_stock_account_input_categ_id.id,
                    # 'property_stock_account_input_categ': category.property_stock_account_input_categ_id.name,
                    # 'property_stock_account_output_categ_id': category.property_stock_account_output_categ_id.id,
                    # 'property_stock_account_output_categ': category.property_stock_account_output_categ_id.name,
                    # 'property_stock_account_production_cost_id': category.property_stock_account_production_cost_id.id,
                    # 'property_stock_account_production_cost': category.property_stock_account_production_cost_id.name,
                }
                data_category_data.append(categorys_data)

            if not createdDateFrom and not createdDateTo and not q:
                total_records = len(data_category_data)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_category_data, total_records, total_pages)
        
        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))
        
class MasterCustomerAPI(http.Controller):
    @http.route(['/api/master_customer/'], type='http', auth='public', methods=['GET'], csrf=False)
    def master_customer_get(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")

            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('customer_code', '=', str(q))]

            if not createdDateFrom and not createdDateTo and not q:
                customers_data = http.request.env['res.partner'].sudo().search([])
                total_records = len(customers_data)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                            ('create_date', '<=', created_date_to.strftime(date_format))]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                customers_data, total_records = paginate_records('res.partner', domain, pageSize, page)
            else:
                customers_data = http.request.env['res.partner'].sudo().search(domain)
                total_records = len(customers_data)

            data_master_customer = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for customer in customers_data:
                create_date_utc = customer.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                customer_data = {
                    'id': customer.id,
                    'create_date': str(create_date_jakarta),
                    'name': customer.name,
                    'street': customer.street,
                    'phone': customer.phone,
                    'mobile': customer.mobile,
                    'email': customer.email,
                    'website': customer.website,
                    'title': customer.title.name,
                    'customer_rank': customer.customer_rank,
                    'supplier_rank': customer.customer_rank,
                    'customer_code': customer.customer_code,
                    'property_product_pricelist_id': customer.property_product_pricelist.id,
                    'property_product_pricelist': customer.property_product_pricelist.name,
                    'property_account_receivable_id': customer.property_account_receivable_id.id,
                    'property_account_receivable': customer.property_account_receivable_id.name,
                    'property_account_payable_id': customer.property_account_payable_id.id,
                    'property_account_payable': customer.property_account_payable_id.name,
                    'property_stock_customer': customer.property_stock_customer.id,
                    'property_stock_customer': customer.property_stock_customer.name,
                    'property_stock_supplier_id': customer.property_stock_supplier.id,
                    'property_stock_supplier': customer.property_stock_supplier.name
                }
                data_master_customer.append(customer_data)

            if not createdDateFrom and not createdDateTo and not q:
                total_records = len(data_master_customer)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_master_customer, total_records, total_pages)
        
        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))
        
class MasterLocationAPI(http.Controller):
    @http.route(['/api/master_location/'], type='http', auth='public', methods=['GET'], csrf=False)
    def master_location_get(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")

            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo and not q:
                # Handle the case when no specific filters are provided
                location_data = http.request.env['stock.location'].sudo().search([])
                total_records = len(location_data)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format))]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                location_data, total_records = paginate_records('stock.location', domain, pageSize, page)
            else:
                location_data = http.request.env['stock.location'].sudo().search(domain)
                total_records = len(location_data)

            data_master_location = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for location in location_data:
                create_date_utc = location.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                locations_data = {
                    'id': location.id,
                    'name': location.name,
                    'create_date': str(create_date_jakarta),
                    'location_id': location.location_id.id,
                    'location': location.location_id.name,
                    'usage': location.usage,
                    'scrap_location': location.scrap_location,
                    'return_location': location.return_location,
                    'replenish_location': location.replenish_location,
                    'last_inventory_date': str(location.last_inventory_date),
                    'next_inventory_date': str(location.next_inventory_date),
                    
                }
                data_master_location.append(locations_data)

            if not createdDateFrom and not createdDateTo and not q:
                total_records = len(data_master_location)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_master_location, total_records, total_pages)
        
        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))
        
class MasterOperationType(http.Controller):
    @http.route(['/api/master_operation_type/'], type='http', auth='public', methods=['GET'], csrf=False)
    def master_operation_type_get(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")

            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo:
                # Handle the case when no specific filters are provided
                domain = [('name', 'ilike', str(q))] if q else [()]
                operation_type_data = http.request.env['stock.picking.type'].sudo().search(domain)
                total_records = len(operation_type_data)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format))]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                operation_type_data, total_records = paginate_records('stock.picking.type', domain, pageSize, page)
            else:
                operation_type_data = http.request.env['stock.picking.type'].sudo().search(domain)
                total_records = len(operation_type_data)

            data_master_operation_type = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for op in operation_type_data:
                create_date_utc =op.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                operations_data = {
                    'id': op.id,
                    'name': op.name,
                    'code': op.code,
                    'create_date': str(create_date_jakarta),
                    'sequence_id': op.sequence_id.id,
                    'sequence': op.sequence_id.name,
                    'sequence_code': op.sequence_code,
                    'return_picking_type_id': op.return_picking_type_id.id,
                    'return_picking_type': op.return_picking_type_id.name,
                    'default_location_return_id': op.default_location_return_id.id,
                    'default_location_return': op.default_location_return_id.name,
                    'create_backorder': op.create_backorder,
                    'default_location_src_id': op.default_location_src_id.id,
                    'default_location_src': op.default_location_src_id.name,
                    'default_location_dest_id': op.default_location_dest_id.id,
                    'default_location_dest': op.default_location_dest_id.name,       
                }
                data_master_operation_type.append(operations_data)

            if not createdDateFrom and not createdDateTo and not q:
                total_records = len(data_master_operation_type)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_master_operation_type, total_records, total_pages)
        
        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))
        
class MasterProductItemAPI(http.Controller):
    @http.route(['/api/master_item/'], type='http', auth='public', methods=['GET'], csrf=False)
    def master_product_get(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('default_code', '=', str(q))]

            if not createdDateFrom and not createdDateTo and not q:
                product_data = http.request.env['product.template'].sudo().search([])
                total_records = len(product_data)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                            ('create_date', '<=', created_date_to.strftime(date_format))]

                pageSize = int(pageSize) if pageSize else 200

                if not q:
                    product_data, total_records = paginate_records('product.template', domain, pageSize, page)
                else:
                    product_data = http.request.env['product.template'].sudo().search(domain)
                    total_records = len(product_data)

            data_master_product = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for product in product_data:
                create_date_utc = product.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                product_data = {
                    'id': product.id,
                    'product_name': product.name,
                    'product_code': product.default_code,
                    'detailed_type': product.detailed_type,
                    'invoice_policy': product.invoice_policy,
                    'uom_id': product.uom_id.id,
                    'uom': product.uom_id.name,
                    'uom_po_id': product.uom_po_id.id,
                    'uom_po': product.uom_po_id.name,
                    'list_price': product.list_price,
                    'standard_price': product.standard_price,
                    'categ_id': product.categ_id.id,
                    'categ': str(product.categ_id.parent_id.name) + ' / ' + str(product.categ_id.name),
                    'create_date': str(create_date_jakarta),
                }
                data_master_product.append(product_data)

            if not createdDateFrom and not createdDateTo and not q:
                total_records = len(data_master_product)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_master_product, total_records, total_pages)
        
        except ValidationError as ve:
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))
       
class MasterPricelistAPI(http.Controller):

    @http.route(['/api/master_pricelist/'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_pricelists(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()
            
            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo and not q:
                pricelist = http.request.env['product.pricelist'].sudo().search([])
                total_records = len(pricelist)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format))]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                pricelist, total_records = paginate_records('product.pricelist', domain, pageSize, page)
            else:
                pricelist = http.request.env['product.pricelist'].sudo().search(domain)
                total_records = len(pricelist)

            data_pricelists = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for order in pricelist:
                create_date_utc = order.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                order_data = {
                    'id': order.id,
                    'name': order.name,
                    'currency_id': order.currency_id.id,
                    'create_date': str(order.create_date)
                }
                data_pricelists.append(order_data)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_pricelists, total_records, total_pages)

        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))

    @http.route(['/api/pricelist_line/<int:order_id>'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_pricelist_lines(self, order_id, **params):
        try:
            check_authorization()

            pricelists = http.request.env['product.pricelist'].sudo().browse(order_id)
            if not pricelists:
                raise werkzeug.exceptions.NotFound(_("Pricelist not found"))

            pricelist_lines = pricelists.item_ids
            pricelist_name = pricelists.name
            currency_id = pricelists.currency_id.id
            currency = pricelists.currency_id.name
            
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            create_date_utc = pricelists.create_date
            create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
            created_date = str(create_date_jakarta)

            data_currency_lines = []
            for line_number, line in enumerate(pricelist_lines, start=1):
                date_start_utc = line.date_start
                date_start_jakarta = pytz.utc.localize(date_start_utc).astimezone(jakarta_tz)
                date_start = str(date_start_jakarta)

                date_end_utc = line.date_end
                date_end_jakarta = pytz.utc.localize(date_end_utc).astimezone(jakarta_tz)
                date_end = str(date_end_jakarta)

                def remove_currency_symbol(price):
                    # Menggunakan regular expression untuk menghapus karakter non-digit
                    return re.sub(r'[^\d.]', '', str(price))
      
                line_data = {
                    'line_number': line_number,
                    'id': line.id,
                    'product_id': line.product_tmpl_id.id,
                    'product_name': line.product_tmpl_id.name,
                    'product_code': line.product_tmpl_id.default_code,
                    'applicable_on': line.name,
                    'min_quantity': line.min_quantity,
                    'price': remove_currency_symbol(line.price),
                    'date_start': date_start,
                    'date_end': date_end
                }
                data_currency_lines.append(line_data)


            response_data = {
                'status': 200,
                'message': 'success',
                'price_list_name': pricelist_name,
                'currency_id': currency_id,
                'currency_name': currency,
                'create_date': created_date,
                'items': data_currency_lines
            }
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                response=json.dumps(response_data)
            )

        except Exception as e:
            return serialize_error_response(str(e))

class SaleOrderAPI(http.Controller):
    @http.route(['/api/sale_order/'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_sale_orders(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")
            
            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo:
                # Handle the case when no specific filters are provided
                domain = [('name', 'ilike', str(q))] if q else [('state', '=', 'sale')]
                sale_orders = http.request.env['sale.order'].sudo().search(domain)
                total_records = len(sale_orders)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format)),
                          ('state', '=', 'sale')]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                sale_orders, total_records = paginate_records('sale.order', domain, pageSize, page)
            else:
                sale_orders = http.request.env['sale.order'].sudo().search(domain)
                total_records = len(sale_orders)

            data_sale_orders = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for order in sale_orders:
                create_date_utc = order.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                order_data = {
                    'id': order.id,
                    'doc_num': order.name,
                    'customer_id': order.partner_id.id,
                    'customer_name': order.partner_id.name,
                    'pricelist_id': order.pricelist_id.id,
                    'create_date': str(create_date_jakarta),
                    'validity_date': str(order.validity_date),
                    'date_order': str(order.date_order),
                    'state': order.state
                }
                data_sale_orders.append(order_data)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_sale_orders, total_records, total_pages)

        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))

    @http.route(['/api/sale_order_line/<int:order_id>'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_sale_order_lines(self, order_id, **params):
        try:
            check_authorization()

            sale_order = http.request.env['sale.order'].sudo().browse(order_id)
            if not sale_order:
                raise werkzeug.exceptions.NotFound(_("Sale Order not found"))

            sale_order_lines = sale_order.order_line
            customer_name = sale_order.partner_id.name
            customer_id = sale_order.partner_id.id
            
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            create_date_utc = sale_order.create_date
            create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
            created_date = str(create_date_jakarta)
            
            date_order = str(sale_order.date_order)
            validity_date = str(sale_order.validity_date)
            amount_total = sale_order.amount_total
            doc_num = sale_order.name

            data_sale_order_lines = []
            for line_number, line in enumerate(sale_order_lines, start=1):
                line_data = {
                    'line_number': line_number,
                    'id': line.id,
                    'doc_no': doc_num,
                    'order_id': line.order_id.id,
                    'product_id': line.product_id.id,
                    'product_code': line.product_id.default_code,
                    'product_name': line.product_id.name,
                    'quantity': line.product_uom_qty,
                    'price_unit': line.price_unit,
                }
                data_sale_order_lines.append(line_data)


            response_data = {
                'status': 200,
                'message': 'success',
                'doc_num': doc_num,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'created_date': str(created_date),
                'date_order': date_order,
                'validity_date': validity_date,
                'items': data_sale_order_lines,
                'amount_total': amount_total
            }
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                response=json.dumps(response_data)
            )

        except Exception as e:
            return serialize_error_response(str(e))
        
class POSOrder(http.Controller):
    @http.route(['/api/pos_order/'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_pos_order(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")

            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo:
                # Handle the case when no specific filters are provided
                domain = [('name', 'ilike', str(q))] if q else [('state', '=', 'done')]
                invoice_orders = http.request.env['pos.order'].sudo().search(domain)
                total_records = len(invoice_orders)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format)),
                          ('state', '=', 'done')]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                invoice_orders, total_records = paginate_records('pos.order', domain, pageSize, page)
            else:
                invoice_orders = http.request.env['pos.order'].sudo().search(domain)
                total_records = len(invoice_orders)

            data_invoice_orders = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for order in invoice_orders:
                create_date_utc = order.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                order_data = {
                    'id': order.id,
                    'doc_num': order.name,
                    'customer_id': order.partner_id.id,
                    'customer_name': order.partner_id.name,
                    'create_date': str(create_date_jakarta),
                    'date_order': str(order.date_order),
                    'session_id': order.session_id.id,
                    'session': order.session_id.name,
                    'user_id': order.user_id.id,
                    'user': order.user_id.name,
                }
                data_invoice_orders.append(order_data)

            if not createdDateFrom and not createdDateTo and not q:
                total_records = len(data_invoice_orders)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_invoice_orders, total_records, total_pages)

        except Exception as e:
            return serialize_error_response(str(e))
        
    @http.route(['/api/pos_order_line/<int:order_id>'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_pos_order_lines(self, order_id, **params):
        try:
            check_authorization()

            pos_order = http.request.env['pos.order'].sudo().browse(order_id)
            if not pos_order:
                raise werkzeug.exceptions.NotFound(_("Invoice Order not found"))

            pos_order_lines = pos_order.lines
            customer_name = pos_order.partner_id.name
            customer_id = pos_order.partner_id.id
            doc_num = pos_order.name
            date = str(pos_order.date_order)
            session_id = pos_order.session_id.id
            session = pos_order.session_id.name
            user_id = pos_order.user_id.id
            user = pos_order.user_id.name

            data_pos_order_lines = []
            for line_number, line in enumerate(pos_order_lines, start=1):
                line_data = {
                    'line_number': line_number,
                    'id': line.id,
                    'doc_no': doc_num,
                    'product_id': line.product_id.id,
                    'product_name': line.full_product_name,
                    'product_code': line.product_id.default_code,
                    'location_id': line.product_id.property_stock_inventory.id,
                    'location': line.product_id.property_stock_inventory.name,
                    'qty': line.qty,
                    'uom_id': line.product_uom_id.id,
                    'uom': line.product_uom_id.name,
                    'discount': line.discount,
                    'price_subtotal': line.price_subtotal,
                    'price_subtotal_incl': line.price_subtotal_incl,
                }
                data_pos_order_lines.append(line_data)

            response_data = {
                'status': 200,
                'message': 'success',
                'doc_num': doc_num,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'date' : date,
                'session_id' : session_id,
                'session' : session,
                'user_id' : user_id,
                'user' : user,
                'order_line': data_pos_order_lines
            }
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                response=json.dumps(response_data)
            )

        except Exception as e:
            return serialize_error_response(str(e))
        
class InvoiceOrder(http.Controller):
    @http.route(['/api/invoice_order/'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_invoices_order(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, is_integrated = None, **params):
        try:
            # check_authorization()

            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            # if is_integrated:
            #     domain += [('is_integrated', '=', is_integrated)]

            if not createdDateFrom and not createdDateTo and not q and not is_integrated:
                # If no parameters are provided, fetch all records
                invoice_accounting = http.request.env['account.move'].sudo().search([('move_type', '=', 'out_invoice'), ('payment_state', '=', 'paid'), ('state', '=', 'posted')])
                total_records = len(invoice_accounting)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                              ('create_date', '<=', created_date_to.strftime(date_format)), 
                              ('state', '=', 'posted'), ('payment_state', '=', 'paid'), ('move_type', '=', 'out_invoice')]

                domain += [('state', '=', 'posted'), ('payment_state', '=', 'paid'), ('move_type', '=', 'out_invoice')]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                invoice_accounting, total_records = paginate_records('account.move', domain, pageSize, page)
            else:
                invoice_accounting = http.request.env['account.move'].sudo().search(domain)
                total_records = len(invoice_accounting)

            data_invoice_accounting = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            location_id = None
            location = None
            for order in invoice_accounting:
                order_pos = http.request.env['pos.order'].sudo().search([('order_ref', '=', order.ref), ('state', '=', 'invoiced')], limit=1)
                for record in order_pos:
                    pickings = http.request.env['stock.picking'].sudo().search([('origin', '=', record.name)])
                    location_id = pickings.location_id.id
                    location = pickings.location_id.complete_name

                create_date_utc = order.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                    
                order_data = {
                    'id': order.id,
                    'doc_num': order.name,
                    'customer_id': order.partner_id.id,
                    'customer_name': order.partner_id.name,
                    'customer_code': order.partner_id.customer_code,
                    'location_id': location_id,
                    'location': location,
                    'is_integrated': order.is_integrated,
                    'create_date': str(create_date_jakarta),
                    'invoice_date': str(order.invoice_date),
                    'invoice_date_due': str(order.invoice_date_due),
                    'payment_reference': order.payment_reference,
                    'journal_id': order.journal_id.id,
                    'journal': order.journal_id.name,
                    'company_id': order.company_id.id,
                    'company': order.company_id.name,
                }
                data_invoice_accounting.append(order_data)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_invoice_accounting, total_records, total_pages)

        except Exception as e:
            return serialize_error_response(str(e))

        
    @http.route(['/api/invoice_order_line/<int:order_id>'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_invoice_order_lines(self, order_id, **params):
        try:
            check_authorization()

            invoicing = http.request.env['account.move'].sudo().browse(order_id)
            if not invoicing:
                raise werkzeug.exceptions.NotFound(_("Invoice Order not found"))

            # order_pos = http.request.env['pos.order'].sudo().search([('order_ref', '=', invoicing.ref), ('state', '=', 'invoiced')], limit=1)
            location_id = None
            location = None
            # for record in order_pos:
            pickings = http.request.env['stock.picking'].sudo().search([('origin', '=', invoicing.ref)])
            location_id = pickings.location_id.id
            location = pickings.location_id.complete_name

            invoice_lines = invoicing.invoice_line_ids
            customer_name = invoicing.partner_id.name
            customer_id = invoicing.partner_id.id
            doc_num = invoicing.name
            company_id = invoicing.company_id.id
            company = invoicing.company_id.name
            is_integrated = invoicing.is_integrated
            invoice_date = str(invoicing.invoice_date)
            
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            create_date_utc = invoicing.create_date
            create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
            create_date = str(create_date_jakarta)

            invoice_date_due = str(invoicing.invoice_date_due)
            payment_reference = invoicing.payment_reference
            journal_id = invoicing.journal_id.id
            journal = invoicing.journal_id.name
            amount = invoicing.amount_total

            data_invoice_lines = []
            for line_number, line in enumerate(invoice_lines, start=1):
                line_data = {
                    'line_number': line_number,
                    'id': line.id,
                    'doc_no': doc_num,
                    'product_id': line.product_id.id,
                    'product_name': line.name,
                    'product_code': line.product_id.default_code,
                    'location_id': location_id,
                    'location': location,
                    'quantity': line.quantity,
                    'uom_id': line.product_uom_id.id,
                    'uom': line.product_uom_id.name,
                    # 'tax_id': line.tax_id.ids,
                    # 'tax': line.tax_id.name,
                    'price_unit': line.price_subtotal,
                }
                data_invoice_lines.append(line_data)

            response_data = {
                'status': 200,
                'message': 'success',
                'doc_num': doc_num,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'create_date': create_date,
                'invoice_date': invoice_date,
                'invoice_date_due': invoice_date_due,
                'is_integrated': is_integrated,
                'payment_reference': payment_reference,
                'journal_id': journal_id,
                'journal': journal,
                'company_id': company_id,
                'company': company,
                'order_line': data_invoice_lines,
                'amount': amount
            }
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                response=json.dumps(response_data)
            )

        except Exception as e:
            return serialize_error_response(str(e))

class ReturOrderAPI(http.Controller):
    @http.route(['/api/return_order/'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_return_orders(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")
            
            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo:
                # Handle the case when no specific filters are provided
                domain = [('name', 'ilike', str(q))] if q else [('state', '=', 'done'), ('picking_type_id.name', '=', 'Return')]
                return_orders = http.request.env['stock.picking'].sudo().search(domain)
                total_records = len(return_orders)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format)),
                          ('picking_type_id.name', '=', 'Return'),
                          ('state', '=', 'done')]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                return_orders, total_records = paginate_records('stock.picking', domain, pageSize, page)
            else:
                return_orders = http.request.env['stock.picking'].sudo().search(domain)
                total_records = len(return_orders)

            data_return_orders = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for order in return_orders:
                create_date_utc = order.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                order_data = {
                    'id': order.id,
                    'doc_num': order.name,
                    'source_document': order.origin,
                    'customer_id': order.partner_id.id,
                    'location_id': order.location_id.id,
                    'location_name': order.location_id.name,
                    'location_destination_id': order.location_dest_id.id,
                    'location_destination': order.location_dest_id.name,
                    'picking_type_id': order.picking_type_id.id,
                    'picking_type': order.picking_type_id.name,
                    'create_date': str(create_date_jakarta),
                    'scheduled_date': str(order.scheduled_date),
                    'date_done': str(order.date_done),
                    'state': order.state
                }
                data_return_orders.append(order_data)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_return_orders, total_records, total_pages)

        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))

    @http.route(['/api/return_order_line/<int:order_id>'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_return_order_lines(self, order_id, **params):
        try:
            check_authorization()

            return_order = http.request.env['stock.picking'].sudo().browse(order_id)
            if not return_order:
                raise werkzeug.exceptions.NotFound(_("Sale Order not found"))
            
            # Ensure the order is a 'Return' type
            if return_order.picking_type_id.name != 'Return':
                raise werkzeug.exceptions.NotFound(_("Order is not a Return Order"))

            return_order_lines = return_order.move_ids_without_package
            doc_num = return_order.name
            customer_name = return_order.partner_id.name
            customer_id = return_order.partner_id.id
            location_id = return_order.location_id.id
            location = return_order.location_id.name
            location_dest_id = return_order.location_dest_id.id
            location_dest = return_order.location_dest_id.name
            picking_type_id = return_order.picking_type_id.id
            picking_type = return_order.picking_type_id.name
            scheduled_date = str(return_order.scheduled_date)

            jakarta_tz = pytz.timezone('Asia/Jakarta')
            create_date_utc = return_order.create_date
            create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
            created_date = str(create_date_jakarta)
            date_done = str(return_order.date_done)

            data_return_order_lines = []
            for line_number, line in enumerate(return_order_lines, start=1):
                line_data = {
                    'line_number': line_number,
                    'id': line.id,
                    'doc_no': doc_num,
                    'location_id': line.location_id.id,
                    'location': line.location_id.name,
                    'location_dest_id': line.location_dest_id.id,
                    'location_dest': line.location_dest_id.name,
                    'product_id': line.product_id.id,
                    'product_code': line.product_id.default_code,
                    'product_name': line.product_id.name,
                    'demand_qty': line.product_uom_qty,
                    'quantity': line.quantity,
                    'product_uom': line.product_uom.name,
                }
                data_return_order_lines.append(line_data)


            response_data = {
                'status': 200,
                'message': 'success',
                'doc_num': doc_num,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'location_id': location_id,
                'location': location,
                'location_destination_id': location_dest_id,
                'location_destination': location_dest,
                'picking_type_id': picking_type_id,
                'picking_type': picking_type,
                'created_date': created_date,
                'scheduled_date': scheduled_date,
                'date_done': date_done,
                'items': data_return_order_lines,
            }
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                response=json.dumps(response_data)
            )

        except Exception as e:
            return serialize_error_response(str(e))
        
class CrediNoteAPI(http.Controller):
    @http.route(['/api/credit_memo/'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_credit_memo(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, is_integrated = None, **params):
        try:
            # check_authorization()

            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            # if is_integrated:
            #     domain += [('is_integrated', '=', is_integrated)]

            if not createdDateFrom and not createdDateTo and not q and not is_integrated:
                # If no parameters are provided, fetch all records
                invoice_accounting = http.request.env['account.move'].sudo().search([('move_type', '=', 'out_refund'), ('state', '=', 'posted')])
                total_records = len(invoice_accounting)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                              ('create_date', '<=', created_date_to.strftime(date_format)), 
                              ('state', '=', 'posted'), ('move_type', '=', 'out_refund')]

                domain += [('state', '=', 'posted'), ('move_type', '=', 'out_refund')]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                invoice_accounting, total_records = paginate_records('account.move', domain, pageSize, page)
            else:
                invoice_accounting = http.request.env['account.move'].sudo().search(domain)
                total_records = len(invoice_accounting)

            data_invoice_accounting = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            location_id = None
            location = None
            for order in invoice_accounting:
                order_pos = http.request.env['pos.order'].sudo().search([('order_ref', '=', order.ref), ('state', '=', 'invoiced')], limit=1)
                for record in order_pos:
                    pickings = http.request.env['stock.picking'].sudo().search([('origin', '=', record.name)])
                    location_id = pickings.location_dest_id.id
                    location = pickings.location_dest_id.complete_name

                create_date_utc = order.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                    
                order_data = {
                    'id': order.id,
                    'doc_num': order.name,
                    'customer_id': order.partner_id.id,
                    'customer_name': order.partner_id.name,
                    'customer_code': order.partner_id.customer_code,
                    'location_id': location_id,
                    'location': location,
                    'is_integrated': order.is_integrated,
                    'create_date': str(create_date_jakarta),
                    'invoice_date': str(order.invoice_date),
                    'invoice_date_due': str(order.invoice_date_due),
                    'payment_reference': order.payment_reference,
                    'journal_id': order.journal_id.id,
                    'journal': order.journal_id.name,
                    'company_id': order.company_id.id,
                    'company': order.company_id.name,
                }
                data_invoice_accounting.append(order_data)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_invoice_accounting, total_records, total_pages)

        except Exception as e:
            return serialize_error_response(str(e))

        
    @http.route(['/api/credit_memo_line/<int:order_id>'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_credit_memo_lines(self, order_id, **params):
        try:
            check_authorization()

            invoicing = http.request.env['account.move'].sudo().browse(order_id)
            if not invoicing:
                raise werkzeug.exceptions.NotFound(_("Invoice Order not found"))

            # order_pos = http.request.env['pos.order'].sudo().search([('order_ref', '=', invoicing.ref), ('state', '=', 'invoiced')], limit=1)
            location_id = None
            location = None
            # for record in order_pos:
            pickings = http.request.env['stock.picking'].sudo().search([('origin', '=', invoicing.ref)])
            location_id = pickings.location_dest_id.id
            location = pickings.location_dest_id.complete_name

            invoice_lines = invoicing.invoice_line_ids
            customer_name = invoicing.partner_id.name
            customer_id = invoicing.partner_id.id
            doc_num = invoicing.name
            company_id = invoicing.company_id.id
            company = invoicing.company_id.name
            is_integrated = invoicing.is_integrated
            invoice_date = str(invoicing.invoice_date)
            
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            create_date_utc = invoicing.create_date
            create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
            create_date = str(create_date_jakarta)

            invoice_date_due = str(invoicing.invoice_date_due)
            payment_reference = invoicing.payment_reference
            journal_id = invoicing.journal_id.id
            journal = invoicing.journal_id.name
            amount = invoicing.amount_total

            data_invoice_lines = []
            for line_number, line in enumerate(invoice_lines, start=1):
                line_data = {
                    'line_number': line_number,
                    'id': line.id,
                    'doc_no': doc_num,
                    'product_id': line.product_id.id,
                    'product_name': line.name,
                    'product_code': line.product_id.default_code,
                    'location_id': location_id,
                    'location': location,
                    'quantity': line.quantity,
                    'uom_id': line.product_uom_id.id,
                    'uom': line.product_uom_id.name,
                    # 'tax_id': line.tax_id.ids,
                    # 'tax': line.tax_id.name,
                    'price_unit': line.price_subtotal,
                }
                data_invoice_lines.append(line_data)

            response_data = {
                'status': 200,
                'message': 'success',
                'doc_num': doc_num,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'create_date': create_date,
                'invoice_date': invoice_date,
                'invoice_date_due': invoice_date_due,
                'is_integrated': is_integrated,
                'payment_reference': payment_reference,
                'journal_id': journal_id,
                'journal': journal,
                'company_id': company_id,
                'company': company,
                'order_line': data_invoice_lines,
                'amount': amount
            }
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                response=json.dumps(response_data)
            )

        except Exception as e:
            return serialize_error_response(str(e))
        
class GoodsReceiptAPI(http.Controller):
    @http.route(['/api/goods_receipt/'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_goods_receipts(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")
            
            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo:
                # Handle the case when no specific filters are provided
                domain = [('name', 'ilike', str(q))] if q else [('state', '=', 'done'), ('picking_type_id.name', '=', 'Goods Receipt')]
                goods_receipt = http.request.env['stock.picking'].sudo().search(domain)
                total_records = len(goods_receipt)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format)),
                          ('picking_type_id.name', '=', 'Goods Receipt'),
                          ('state', '=', 'done')]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                goods_receipt, total_records = paginate_records('stock.picking', domain, pageSize, page)
            else:
                goods_receipt = http.request.env['stock.picking'].sudo().search(domain)
                total_records = len(goods_receipt)

            data_goods_receipt = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for order in goods_receipt:
                create_date_utc = order.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                order_data = {
                    'id': order.id,
                    'doc_num': order.name,
                    'source_document': order.origin,
                    'customer_id': order.partner_id.id,
                    'location_id': order.location_id.id,
                    'location_name': order.location_id.name,
                    'location_destination_id': order.location_dest_id.id,
                    'location_destination': order.location_dest_id.name,
                    'picking_type_id': order.picking_type_id.id,
                    'picking_type': order.picking_type_id.name,
                    'create_date': str(create_date_jakarta),
                    'scheduled_date': str(order.scheduled_date),
                    'date_done': str(order.date_done),
                    'state': order.state
                }
                data_goods_receipt.append(order_data)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_goods_receipt, total_records, total_pages)

        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))

    @http.route(['/api/goods_receipt_line/<int:order_id>'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_goods_receipt_lines(self, order_id, **params):
        try:
            check_authorization()

            goods_receipt = http.request.env['stock.picking'].sudo().browse(order_id)
            if not goods_receipt:
                raise werkzeug.exceptions.NotFound(_("Goods Receipt not found"))
            
            # Ensure the order is a 'Return' type
            if goods_receipt.picking_type_id.name != 'Goods Receipt':
                raise werkzeug.exceptions.NotFound(_("Goods Receipt is not a Goods Receipt"))

            goods_receipt_lines = goods_receipt.move_ids_without_package
            doc_num = goods_receipt.name
            customer_name = goods_receipt.partner_id.name
            customer_id = goods_receipt.partner_id.id
            location_id = goods_receipt.location_id.id
            location = goods_receipt.location_id.name
            location_dest_id = goods_receipt.location_dest_id.id
            location_dest = goods_receipt.location_dest_id.name
            picking_type_id = goods_receipt.picking_type_id.id
            picking_type = goods_receipt.picking_type_id.name
            scheduled_date = str(goods_receipt.scheduled_date)

            jakarta_tz = pytz.timezone('Asia/Jakarta')
            create_date_utc = goods_receipt.create_date
            create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
            created_date = str(create_date_jakarta)
            date_done = str(goods_receipt.date_done)

            data_goods_receipt_lines = []
            for line_number, line in enumerate(goods_receipt_lines, start=1):
                line_data = {
                    'line_number': line_number,
                    'id': line.id,
                    'doc_no': doc_num,
                    'location_id': line.location_id.id,
                    'location': line.location_id.name,
                    'location_dest_id': line.location_dest_id.id,
                    'location_dest': line.location_dest_id.name,
                    'product_id': line.product_id.id,
                    'product_code': line.product_id.default_code,
                    'product_name': line.product_id.name,
                    'demand_qty': line.product_uom_qty,
                    'quantity': line.quantity,
                    'product_uom': line.product_uom.name,
                }
                data_goods_receipt_lines.append(line_data)

            response_data = {
                'status': 200,
                'message': 'success',
                'doc_num': doc_num,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'location_id': location_id,
                'location': location,
                'location_destination_id': location_dest_id,
                'location_destination': location_dest,
                'picking_type_id': picking_type_id,
                'picking_type': picking_type,
                'created_date': created_date,
                'scheduled_date': scheduled_date,
                'date_done': date_done,
                'items': data_goods_receipt_lines,
            }
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                response=json.dumps(response_data)
            )

        except Exception as e:
            return serialize_error_response(str(e))
        
class GoodsIssueAPI(http.Controller):
    @http.route(['/api/goods_issue/'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_goods_issue(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")
            
            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo:
                # Handle the case when no specific filters are provided
                domain = [('name', 'ilike', str(q))] if q else [('state', '=', 'done'), ('picking_type_id.name', '=', 'Goods Issue')]
                goods_issue = http.request.env['stock.picking'].sudo().search(domain)
                total_records = len(goods_issue)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format)),
                          ('picking_type_id.name', '=', 'Goods Issue'),
                          ('state', '=', 'done')]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                goods_issue, total_records = paginate_records('stock.picking', domain, pageSize, page)
            else:
                goods_issue = http.request.env['stock.picking'].sudo().search(domain)
                total_records = len(goods_issue)

            data_goods_issue = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for order in goods_issue:
                create_date_utc = order.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                order_data = {
                    'id': order.id,
                    'doc_num': order.name,
                    'source_document': order.origin,
                    'customer_id': order.partner_id.id,
                    'location_id': order.location_id.id,
                    'location_name': order.location_id.name,
                    'location_destination_id': order.location_dest_id.id,
                    'location_destination': order.location_dest_id.name,
                    'picking_type_id': order.picking_type_id.id,
                    'picking_type': order.picking_type_id.name,
                    'create_date': str(create_date_jakarta),
                    'scheduled_date': str(order.scheduled_date),
                    'date_done': str(order.date_done),
                    'state': order.state
                }
                data_goods_issue.append(order_data)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_goods_issue, total_records, total_pages)

        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))

    @http.route(['/api/goods_receipt_line/<int:order_id>'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_goods_issue_lines(self, order_id, **params):
        try:
            check_authorization()

            goods_issue = http.request.env['stock.picking'].sudo().browse(order_id)
            if not goods_issue:
                raise werkzeug.exceptions.NotFound(_("Goods Receipt not found"))
            
            # Ensure the order is a 'Return' type
            if goods_issue.picking_type_id.name != 'Goods Receipt':
                raise werkzeug.exceptions.NotFound(_("Goods Receipt is not a Goods Receipt"))

            goods_issue_lines = goods_issue.move_ids_without_package
            doc_num = goods_issue.name
            customer_name = goods_issue.partner_id.name
            customer_id = goods_issue.partner_id.id
            location_id = goods_issue.location_id.id
            location = goods_issue.location_id.name
            location_dest_id = goods_issue.location_dest_id.id
            location_dest = goods_issue.location_dest_id.name
            picking_type_id = goods_issue.picking_type_id.id
            picking_type = goods_issue.picking_type_id.name
            scheduled_date = str(goods_issue.scheduled_date)
            
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            create_date_utc = goods_issue.create_date
            create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
            created_date = str(create_date_jakarta)
            date_done = str(goods_issue.date_done)

            data_goods_issue_lines = []
            for line_number, line in enumerate(goods_issue_lines, start=1):
                line_data = {
                    'line_number': line_number,
                    'id': line.id,
                    'doc_no': doc_num,
                    'location_id': line.location_id.id,
                    'location': line.location_id.name,
                    'location_dest_id': line.location_dest_id.id,
                    'location_dest': line.location_dest_id.name,
                    'product_id': line.product_id.id,
                    'product_code': line.product_id.default_code,
                    'product_name': line.product_id.name,
                    'demand_qty': line.product_uom_qty,
                    'quantity': line.quantity,
                    'product_uom': line.product_uom.name,
                }
                data_goods_issue_lines.append(line_data)

            response_data = {
                'status': 200,
                'message': 'success',
                'doc_num': doc_num,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'location_id': location_id,
                'location': location,
                'location_destination_id': location_dest_id,
                'location_destination': location_dest,
                'picking_type_id': picking_type_id,
                'picking_type': picking_type,
                'created_date': created_date,
                'scheduled_date': scheduled_date,
                'date_done': date_done,
                'items': data_goods_issue_lines,
            }
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                response=json.dumps(response_data)
            )

        except Exception as e:
            return serialize_error_response(str(e))
        
class InternalTransferAPI(http.Controller):
    @http.route(['/api/internal_transfer/'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_internal_transfer(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")
            
            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo:
                # Handle the case when no specific filters are provided
                domain = [('name', 'ilike', str(q))] if q else [('state', '=', 'done'), ('picking_type_id.name', '=', 'Internal Transfer')]
                internal_transfers = http.request.env['stock.picking'].sudo().search(domain)
                total_records = len(internal_transfers)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format)),
                          ('picking_type_id.name', '=', 'Internal Transfer'),
                          ('state', '=', 'done')]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                internal_transfers, total_records = paginate_records('stock.picking', domain, pageSize, page)
            else:
                internal_transfers = http.request.env['stock.picking'].sudo().search(domain)
                total_records = len(internal_transfers)

            data_internal_transfers = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for order in internal_transfers:
                create_date_utc = order.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                order_data = {
                    'id': order.id,
                    'doc_num': order.name,
                    'source_document': order.origin,
                    'customer_id': order.partner_id.id,
                    'location_id': order.location_id.id,
                    'location_name': order.location_id.name,
                    'location_destination_id': order.location_dest_id.id,
                    'location_destination': order.location_dest_id.name,
                    'picking_type_id': order.picking_type_id.id,
                    'picking_type': order.picking_type_id.name,
                    'create_date': str(create_date_jakarta),
                    'scheduled_date': str(order.scheduled_date),
                    'date_done': str(order.date_done),
                    'state': order.state
                }
                data_internal_transfers.append(order_data)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_internal_transfers, total_records, total_pages)

        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))

    @http.route(['/api/internal_transfers_line/<int:order_id>'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_internal_transfer_lines(self, order_id, **params):
        try:
            check_authorization()

            internal_transfers = http.request.env['stock.picking'].sudo().browse(order_id)
            if not internal_transfers:
                raise werkzeug.exceptions.NotFound(_("Goods Receipt not found"))
            
            # Ensure the order is a 'Return' type
            if internal_transfers.picking_type_id.name != 'Goods Receipt':
                raise werkzeug.exceptions.NotFound(_("Goods Receipt is not a Goods Receipt"))

            internal_transfers_lines = internal_transfers.move_ids_without_package
            doc_num = internal_transfers.name
            customer_name = internal_transfers.partner_id.name
            customer_id = internal_transfers.partner_id.id
            location_id = internal_transfers.location_id.id
            location = internal_transfers.location_id.name
            location_dest_id = internal_transfers.location_dest_id.id
            location_dest = internal_transfers.location_dest_id.name
            picking_type_id = internal_transfers.picking_type_id.id
            picking_type = internal_transfers.picking_type_id.name
            scheduled_date = str(internal_transfers.scheduled_date)

            jakarta_tz = pytz.timezone('Asia/Jakarta')
            create_date_utc = internal_transfers.create_date
            create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
            created_date = str(create_date_jakarta)
            date_done = str(internal_transfers.date_done)

            data_internal_transfers_lines = []
            for line_number, line in enumerate(internal_transfers_lines, start=1):
                line_data = {
                    'line_number': line_number,
                    'id': line.id,
                    'doc_no': doc_num,
                    'location_id': line.location_id.id,
                    'location': line.location_id.name,
                    'location_dest_id': line.location_dest_id.id,
                    'location_dest': line.location_dest_id.name,
                    'product_id': line.product_id.id,
                    'product_code': line.product_id.default_code,
                    'product_name': line.product_id.name,
                    'demand_qty': line.product_uom_qty,
                    'quantity': line.quantity,
                    'product_uom': line.product_uom.name,
                }
                data_internal_transfers_lines.append(line_data)

            response_data = {
                'status': 200,
                'message': 'success',
                'doc_num': doc_num,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'location_id': location_id,
                'location': location,
                'location_destination_id': location_dest_id,
                'location_destination': location_dest,
                'picking_type_id': picking_type_id,
                'picking_type': picking_type,
                'created_date': created_date,
                'scheduled_date': scheduled_date,
                'date_done': date_done,
                'items': data_internal_transfers_lines,
            }
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                response=json.dumps(response_data)
            )

        except Exception as e:
            return serialize_error_response(str(e))
        
class TsOutAPI(http.Controller):
    @http.route(['/api/transit_out/'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_transit_out(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")
            
            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo:
                # Handle the case when no specific filters are provided
                domain = [('name', 'ilike', str(q))] if q else [('state', '=', 'done'), ('picking_type_id.name', '=', 'Transit Out')]
                transit_out = http.request.env['stock.picking'].sudo().search(domain)
                total_records = len(transit_out)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format)),
                          ('picking_type_id.name', '=', 'Transit Out'),
                          ('state', '=', 'done')]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                transit_out, total_records = paginate_records('stock.picking', domain, pageSize, page)
            else:
                transit_out = http.request.env['stock.picking'].sudo().search(domain)
                total_records = len(transit_out)

            data_transit_out = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for order in transit_out:
                create_date_utc = order.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                order_data = {
                    'id': order.id,
                    'doc_num': order.name,
                    'source_document': order.origin,
                    'customer_id': order.partner_id.id,
                    'location_id': order.location_id.id,
                    'location_name': order.location_id.name,
                    'location_destination_id': order.location_dest_id.id,
                    'location_destination': order.location_dest_id.name,
                    'picking_type_id': order.picking_type_id.id,
                    'picking_type': order.picking_type_id.name,
                    'create_date': str(create_date_jakarta),
                    'scheduled_date': str(order.scheduled_date),
                    'date_done': str(order.date_done),
                    'state': order.state
                }
                data_transit_out.append(order_data)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_transit_out, total_records, total_pages)

        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))

    @http.route(['/api/internal_transfers_line/<int:order_id>'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_transit_out_lines(self, order_id, **params):
        try:
            check_authorization()

            transit_out = http.request.env['stock.picking'].sudo().browse(order_id)
            if not transit_out:
                raise werkzeug.exceptions.NotFound(_("Transit Out not found"))
            
            # Ensure the order is a 'Return' type
            if transit_out.picking_type_id.name != 'Transit Out':
                raise werkzeug.exceptions.NotFound(_("Transit Out is not a Goods Receipt"))

            transit_out_lines = transit_out.move_ids_without_package
            doc_num = transit_out.name
            customer_name = transit_out.partner_id.name
            customer_id = transit_out.partner_id.id
            location_id = transit_out.location_id.id
            location = transit_out.location_id.name
            location_dest_id = transit_out.location_dest_id.id
            location_dest = transit_out.location_dest_id.name
            picking_type_id = transit_out.picking_type_id.id
            picking_type = transit_out.picking_type_id.name
            scheduled_date = str(transit_out.scheduled_date)

            jakarta_tz = pytz.timezone('Asia/Jakarta')
            create_date_utc = transit_out.create_date
            create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
            created_date = str(create_date_jakarta)
            date_done = str(transit_out.date_done)

            data_transit_out_lines = []
            for line_number, line in enumerate(transit_out_lines, start=1):
                line_data = {
                    'line_number': line_number,
                    'id': line.id,
                    'doc_no': doc_num,
                    'location_id': line.location_id.id,
                    'location': line.location_id.name,
                    'location_dest_id': line.location_dest_id.id,
                    'location_dest': line.location_dest_id.name,
                    'product_id': line.product_id.id,
                    'product_code': line.product_id.default_code,
                    'product_name': line.product_id.name,
                    'demand_qty': line.product_uom_qty,
                    'quantity': line.quantity,
                    'product_uom': line.product_uom.name,
                }
                data_transit_out_lines.append(line_data)

            response_data = {
                'status': 200,
                'message': 'success',
                'doc_num': doc_num,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'location_id': location_id,
                'location': location,
                'location_destination_id': location_dest_id,
                'location_destination': location_dest,
                'picking_type_id': picking_type_id,
                'picking_type': picking_type,
                'created_date': created_date,
                'scheduled_date': scheduled_date,
                'date_done': date_done,
                'items': data_transit_out_lines,
            }
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                response=json.dumps(response_data)
            )

        except Exception as e:
            return serialize_error_response(str(e))
        
class TsInAPI(http.Controller):
    @http.route(['/api/transit_in/'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_transit_in(self, createdDateFrom=None, createdDateTo=None, pageSize=200, page=1, q=None, **params):
        try:
            check_authorization()

            # if not q and (not createdDateFrom or not createdDateTo or not pageSize or not page):
            #     raise ValidationError("One or more required parameters are missing.")
            
            if int(page) == 0:
                return serialize_response([], 0, 0)

            date_format = '%Y-%m-%d'
            domain = []  # Initialize domain here

            if q:
                domain += [('name', 'ilike', str(q))]

            if not createdDateFrom and not createdDateTo:
                # Handle the case when no specific filters are provided
                domain = [('name', 'ilike', str(q))] if q else [('state', '=', 'done'), ('picking_type_id.name', '=', 'Transit In')]
                transit_in = http.request.env['stock.picking'].sudo().search(domain)
                total_records = len(transit_in)
            else:
                if createdDateFrom or createdDateTo:
                    created_date_from = fields.Date.from_string(createdDateFrom) if createdDateFrom else fields.Date.today()
                    created_date_to = fields.Date.from_string(createdDateTo) if createdDateTo else fields.Date.today()

                    domain += [('create_date', '>=', created_date_from.strftime(date_format)),
                          ('create_date', '<=', created_date_to.strftime(date_format)),
                          ('picking_type_id.name', '=', 'Goods Issue'),
                          ('state', '=', 'done')]

                pageSize = int(pageSize) if pageSize else 200

            if not q:  # Check if q is provided
                transit_in, total_records = paginate_records('stock.picking', domain, pageSize, page)
            else:
                transit_in = http.request.env['stock.picking'].sudo().search(domain)
                total_records = len(transit_in)

            data_transit_in = []
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            for order in transit_in:
                create_date_utc = order.create_date
                create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
                order_data = {
                    'id': order.id,
                    'doc_num': order.name,
                    'source_document': order.origin,
                    'customer_id': order.partner_id.id,
                    'location_id': order.location_id.id,
                    'location_name': order.location_id.name,
                    'location_destination_id': order.location_dest_id.id,
                    'location_destination': order.location_dest_id.name,
                    'picking_type_id': order.picking_type_id.id,
                    'picking_type': order.picking_type_id.name,
                    'create_date': str(create_date_jakarta),
                    'scheduled_date': str(order.scheduled_date),
                    'date_done': str(order.date_done),
                    'state': order.state
                }
                data_transit_in.append(order_data)

            total_pages = (total_records + pageSize - 1) // pageSize

            return serialize_response(data_transit_in, total_records, total_pages)

        except ValidationError as ve:
            # If any required parameter is missing, return HTTP 500 error
            error_response = {
                'error': 'One or more required parameters are missing.',
                'status': 500
            }
            return http.Response(json.dumps(error_response), content_type='application/json', status=500)

        except Exception as e:
            return serialize_error_response(str(e))

    @http.route(['/api/transit_in_line/<int:order_id>'], type='http', auth='public', methods=['GET'], csrf=False)
    def get_transit_in_lines(self, order_id, **params):
        try:
            check_authorization()

            transit_in = http.request.env['stock.picking'].sudo().browse(order_id)
            if not transit_in:
                raise werkzeug.exceptions.NotFound(_("Transit In not found"))
            
            # Ensure the order is a 'Return' type
            if transit_in.picking_type_id.name != 'Transit Out':
                raise werkzeug.exceptions.NotFound(_("Transit In is not a Goods Receipt"))

            transit_in_lines = transit_in.move_ids_without_package
            doc_num = transit_in.name
            customer_name = transit_in.partner_id.name
            customer_id = transit_in.partner_id.id
            location_id = transit_in.location_id.id
            location = transit_in.location_id.name
            location_dest_id = transit_in.location_dest_id.id
            location_dest = transit_in.location_dest_id.name
            picking_type_id = transit_in.picking_type_id.id
            picking_type = transit_in.picking_type_id.name
            scheduled_date = str(transit_in.scheduled_date)

            jakarta_tz = pytz.timezone('Asia/Jakarta')
            create_date_utc = transit_in.create_date
            create_date_jakarta = pytz.utc.localize(create_date_utc).astimezone(jakarta_tz)
            created_date = str(create_date_jakarta)
            date_done = str(transit_in.date_done)

            data_transit_in_lines = []
            for line_number, line in enumerate(transit_in_lines, start=1):
                line_data = {
                    'line_number': line_number,
                    'id': line.id,
                    'doc_no': doc_num,
                    'location_id': line.location_id.id,
                    'location': line.location_id.name,
                    'location_dest_id': line.location_dest_id.id,
                    'location_dest': line.location_dest_id.name,
                    'product_id': line.product_id.id,
                    'product_code': line.product_id.default_code,
                    'product_name': line.product_id.name,
                    'demand_qty': line.product_uom_qty,
                    'quantity': line.quantity,
                    'product_uom': line.product_uom.name,
                }
                data_transit_in_lines.append(line_data)

            response_data = {
                'status': 200,
                'message': 'success',
                'doc_num': doc_num,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'location_id': location_id,
                'location': location,
                'location_destination_id': location_dest_id,
                'location_destination': location_dest,
                'picking_type_id': picking_type_id,
                'picking_type': picking_type,
                'created_date': created_date,
                'scheduled_date': scheduled_date,
                'date_done': date_done,
                'items': data_transit_in_lines,
            }
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                response=json.dumps(response_data)
            )

        except Exception as e:
            return serialize_error_response(str(e))