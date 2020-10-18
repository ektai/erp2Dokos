from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'sales_invoice',
		'non_standard_fieldnames': {
			'Delivery Note': 'against_sales_invoice',
			'Journal Entry': 'reference_name',
			'Payment Entry': 'reference_name',
			'Payment Request': 'reference_name',
			'Sales Invoice': 'return_against',
			'Auto Repeat': 'reference_document',
			'Bank Transaction': 'payment_entry'
		},
		'internal_links': {
			'Sales Order': ['items', 'sales_order']
		},
		'transactions': [
			{
				'label': _('Payment'),
				'items': ['Payment Entry', 'Payment Request', 'Journal Entry', 'Invoice Discounting', 'Dunning', 'Bank Transaction']
			},
			{
				'label': _('Reference'),
				'items': ['Timesheet', 'Delivery Note', 'Sales Order']
			},
			{
				'label': _('Returns'),
				'items': ['Sales Invoice']
			},
			{
				'label': _('Repeat'),
				'items': ['Auto Repeat']
			},
		]
	}