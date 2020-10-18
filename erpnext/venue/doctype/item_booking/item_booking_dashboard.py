from frappe import _

def get_data():
	return {
		'fieldname': 'item_booking',
		'transactions': [
			{
				'label': _('Quotations'),
				'items': ['Quotation']
			},
			{
				'label': _('Sales Orders'),
				'items': ['Sales Order']
			}
		]
	}