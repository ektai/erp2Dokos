from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'payment_request',
        'non_standard_fieldnames': {
			'Integration Request': 'reference_docname',
		},
		'transactions': [
			{
                'label': _("Payment Logs"),
				'items': ['Integration Request', 'Payment Entry']
			}
		]
	}