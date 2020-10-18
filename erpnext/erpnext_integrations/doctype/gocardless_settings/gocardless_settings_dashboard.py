from frappe import _

def get_data():
	return {
		'fieldname': 'gateway_controller',
		'transactions': [
			{
				'label': _('Payment Gateways'),
				'items': ['Payment Gateway']
			}
		]
	}
