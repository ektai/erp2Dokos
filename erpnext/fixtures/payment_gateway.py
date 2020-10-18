from frappe import _

def get_dashboard_data(data):
	data['transactions'].extend(
		[
			{
				'label': _('Accounts'),
				'items': ['Payment Gateway Account']
			}
		]
	)

	return data