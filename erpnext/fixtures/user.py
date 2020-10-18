from frappe import _

def get_dashboard_data(data):
	data['non_standard_fieldnames'].update({ 'Employee': 'user_id' })
	data['transactions'].extend(
		[
			{
				'label': _('Employees'),
				'items': ['Employee']
			}
		]
	)

	return data