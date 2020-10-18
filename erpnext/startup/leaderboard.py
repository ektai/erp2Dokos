
from __future__ import unicode_literals, print_function
import frappe
from frappe import _
from frappe.utils import cint
from frappe.translate import send_translations, get_dict

def get_leaderboards():
	leaderboards = {
		"Customer": {
			"fields": [
				{'fieldname': 'total_sales_amount', 'fieldtype': 'Currency', 'label': _('Total Sales Amount')},
				{'fieldname': 'total_qty_sold', 'label': _("Total Qty Sold")},
				{'fieldname': 'outstanding_amount', 'fieldtype': 'Currency', 'label': _("Outstanding Amount")}
			],
			"method": "erpnext.startup.leaderboard.get_all_customers",
		},
		"Item": {
			"fields": [
				{'fieldname': 'total_sales_amount', 'fieldtype': 'Currency', 'label': _("Total Sales Amount")},
				{'fieldname': 'total_qty_sold', 'label': _('Total Qty Sold')},
				{'fieldname': 'total_purchase_amount', 'fieldtype': 'Currency', 'label': _('Total Purchase Amount')},
				{'fieldname': 'total_qty_purchased', 'label': _('Total Qty Purchased')},
				{'fieldname': 'available_stock_qty', 'label': _('Available Stock Qty')},
				{'fieldname': 'available_stock_value', 'fieldtype': 'Currency', 'label': _('Available Stock Value')}
			],
			"method": "erpnext.startup.leaderboard.get_all_items",
		},
		"Supplier": {
			"fields": [
				{'fieldname': 'total_purchase_amount', 'fieldtype': 'Currency', 'label': _('Total Purchase Amount')},
				{'fieldname':'total_qty_purchased', 'label': _('Total Qty Purchased')},
				{'fieldname': 'outstanding_amount', 'fieldtype': 'Currency', 'label': _('Outstanding Amount')}
			],
			"method": "erpnext.startup.leaderboard.get_all_suppliers",
		},
		"Sales Partner": {
			"fields": [
				{'fieldname': 'total_sales_amount', 'fieldtype': 'Currency', 'label': _('Total Sales Amount')},
				{'fieldname': 'total_commission', 'fieldtype': 'Currency', 'label': _('Total Commission')}
			],
			"method": "erpnext.startup.leaderboard.get_all_sales_partner",
		},
		"Sales Person": {
			"fields": [
				{'fieldname': 'total_sales_amount', 'fieldtype': 'Currency', 'label': _('Total Sales Amount')}
			],
			"method": "erpnext.startup.leaderboard.get_all_sales_person",
		}
	}

	leaderboard_file = frappe.get_pymodule_path('erpnext.startup', 'leaderboard.py')
	send_translations(get_dict("pyfile", leaderboard_file))

	return leaderboards

@frappe.whitelist()
def get_all_customers(date_range, company, field, limit = None):
	if field == "outstanding_amount":
		filters = [['docstatus', '=', '1'], ['company', '=', company]]
		if date_range:
			date_range = frappe.parse_json(date_range)
			filters.append(['posting_date', 'between', [date_range[0], date_range[1]]])
		return frappe.get_all('Sales Invoice',
			fields = ['customer as name', 'sum(outstanding_amount) as value'],
			filters = filters,
			group_by = 'customer',
			order_by = 'value desc',
			limit = limit
		)
	else:
		if field == "total_sales_amount":
			select_field = "sum(so_item.base_net_amount)"
		elif field == "total_qty_sold":
			select_field = "sum(so_item.stock_qty)"

		date_condition = get_date_condition(date_range, 'so.posting_date')

		return frappe.db.sql("""
			select so.customer as name, {0} as value
			FROM `tabSales Invoice` as so JOIN `tabSales Invoice Item` as so_item
				ON so.name = so_item.parent
			where so.docstatus = 1 {1} and so.company = %s
			group by so.customer
			order by value DESC
			limit %s
		""".format(select_field, date_condition), (company, cint(limit)), as_dict=1)

@frappe.whitelist()
def get_all_items(date_range, company, field, limit = None):
	if field in ("available_stock_qty", "available_stock_value"):
		select_field = "sum(actual_qty)" if field=="available_stock_qty" else "sum(stock_value)"
		return frappe.db.get_all('Bin',
			fields = ['item_code as name', '{0} as value'.format(select_field)],
			group_by = 'item_code',
			order_by = 'value desc',
			limit = limit
		)
	else:
		if field == "total_sales_amount":
			select_field = "sum(order_item.base_net_amount)"
			select_doctype = "Sales Invoice"
		elif field == "total_purchase_amount":
			select_field = "sum(order_item.base_net_amount)"
			select_doctype = "Purchase Invoice"
		elif field == "total_qty_sold":
			select_field = "sum(order_item.stock_qty)"
			select_doctype = "Sales Invoice"
		elif field == "total_qty_purchased":
			select_field = "sum(order_item.stock_qty)"
			select_doctype = "Purchase Invoice"

		date_condition = get_date_condition(date_range, 'sales_order.posting_date')

		return frappe.db.sql("""
			select order_item.item_code as name, {0} as value
			from `tab{1}` sales_order join `tab{1} Item` as order_item
				on sales_order.name = order_item.parent
			where sales_order.docstatus = 1
				and sales_order.company = %s {2}
			group by order_item.item_code
			order by value desc
			limit %s
		""".format(select_field, select_doctype, date_condition), (company, cint(limit)), as_dict=1) #nosec

@frappe.whitelist()
def get_all_suppliers(date_range, company, field, limit = None):
	if field == "outstanding_amount":
		filters = [['docstatus', '=', '1'], ['company', '=', company]]
		if date_range:
			date_range = frappe.parse_json(date_range)
			filters.append(['posting_date', 'between', [date_range[0], date_range[1]]])
		return frappe.db.get_all('Purchase Invoice',
			fields = ['supplier as name', 'sum(outstanding_amount) as value'],
			filters = filters,
			group_by = 'supplier',
			order_by = 'value desc',
			limit = limit
		)
	else:
		if field == "total_purchase_amount":
			select_field = "sum(purchase_order_item.base_net_amount)"
		elif field == "total_qty_purchased":
			select_field = "sum(purchase_order_item.stock_qty)"

		date_condition = get_date_condition(date_range, 'purchase_order.modified')

		return frappe.db.sql("""
			select purchase_order.supplier as name, {0} as value
			FROM `tabPurchase Invoice` as purchase_order LEFT JOIN `tabPurchase Invoice Item`
				as purchase_order_item ON purchase_order.name = purchase_order_item.parent
			where
				purchase_order.docstatus = 1
				{1}
				and  purchase_order.company = %s
			group by purchase_order.supplier
			order by value DESC
			limit %s""".format(select_field, date_condition), (company, cint(limit)), as_dict=1) #nosec

@frappe.whitelist()
def get_all_sales_partner(date_range, company, field, limit = None):
	if field == "total_sales_amount":
		select_field = "sum(`base_net_total`)"
	elif field == "total_commission":
		select_field = "sum(`total_commission`)"

	filters = {
		'sales_partner': ['!=', ''],
		'docstatus': 1,
		'company': company
	}
	if date_range:
		date_range = frappe.parse_json(date_range)
		filters['posting_date'] = ['between', [date_range[0], date_range[1]]]

	return frappe.get_list('Sales Invoice', fields=[
		'`sales_partner` as name',
		'{} as value'.format(select_field),
	], filters=filters, group_by='sales_partner', order_by='value DESC', limit=limit)

@frappe.whitelist()
def get_all_sales_person(date_range, company, field = None, limit = 0):
	date_condition = get_date_condition(date_range, 'sales_order.posting_date')

	return frappe.db.sql("""
		select sales_team.sales_person as name, sum(sales_order.base_net_total) as value
		from `tabSales Invoice` as sales_order join `tabSales Team` as sales_team
			on sales_order.name = sales_team.parent and sales_team.parenttype = 'Sales Invoice'
		where sales_order.docstatus = 1
			and sales_order.company = %s
			{date_condition}
		group by sales_team.sales_person
		order by value DESC
		limit %s
	""".format(date_condition=date_condition), (company, cint(limit)), as_dict=1)

def get_date_condition(date_range, field):
	date_condition = ''
	if date_range:
		date_range = frappe.parse_json(date_range)
		from_date, to_date = date_range
		date_condition = "and {0} between {1} and {2}".format(
			field, frappe.db.escape(from_date), frappe.db.escape(to_date)
		)
	return date_condition