from frappe import _

def get_data():
	return {
		'fieldname': 'goal',
		'transactions': [
			{
				'label': _('Review'),
				'items': ['Quality Review']
			}
		]
	}