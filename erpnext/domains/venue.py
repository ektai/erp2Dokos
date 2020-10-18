from __future__ import unicode_literals

data = {
	'default_portal_role': 'Customer',
	'hidden_modules': [
		'Assets',
		'Payroll',
		'Projects',
		'Loan Management',
		'Quality Management',
		'HR',
		'Stock',
		'CRM',
		'Support',
		'Accounting'
	],
	'restricted_roles': [
		'Volunteer'
	],
	'modules': [
		'Venue'
	],
	'on_setup': 'erpnext.venue.setup.setup_venue'
}