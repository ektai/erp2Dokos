frappe.listview_settings['Company'] = {
	onload: () => {
		frappe.breadcrumbs.add({
			type: 'Custom',
			module: 'Accounts',
			label: __('Accounting'),
			route: '#workspace/Accounting'
		});
	}
}