from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'graph': True,
		'graph_method': "erpnext.accounts.doctype.subscription.subscription.get_chart_data",
		'graph_method_args': {
			'title': _('Last subscription invoices')
		},
		'fieldname': 'subscription',
		'non_standard_fieldnames': {
			'Payment Request': 'reference_name'
		},
		'transactions': [
			{
				'label': _('Sales'),
				'items': ['Sales Order', 'Sales Invoice']
			},
			{
				'label': _('Payments'),
				'items': ['Payment Request', 'Payment Entry']
			},
			{
				'label': _('Events'),
				'items': ['Subscription Event']
			}
		]
	}