from frappe import _

def get_data():
	return {
		'fieldname': 'payment_entry',
		'transactions': [
			{
				'label': _('Bank Statement'),
				'items': ['Bank Transaction']
			}
		]
	}