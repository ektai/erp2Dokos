frappe.ready(() => {
	$(document).on('click', '.address-card', (e) => {
		const $target = $(e.currentTarget);
		const $section = $target.closest('[data-section]');
		$section.find('.address-card').removeClass('active');
		$target.addClass('active');
	});

	$('#input_same_billing').change((e) => {
		const $check = $(e.target);
		toggle_billing_address_section(!$check.is(':checked'));
	});

	$('.btn-new-address').click(() => {
		const d = new frappe.ui.Dialog({
			title: __('New Address'),
			fields: [
				{
					label: __('Address Title'),
					fieldname: 'address_title',
					fieldtype: 'Data',
					reqd: 1
				},
				{
					label: __('Address Line 1'),
					fieldname: 'address_line1',
					fieldtype: 'Data',
					reqd: 1
				},
				{
					label: __('Address Line 2'),
					fieldname: 'address_line2',
					fieldtype: 'Data'
				},
				{
					label: __('City/Town'),
					fieldname: 'city',
					fieldtype: 'Data',
					reqd: 1
				},
				{
					label: __('State'),
					fieldname: 'state',
					fieldtype: 'Data'
				},
				{
					label: __('Country'),
					fieldname: 'country',
					fieldtype: 'Link',
					reqd: 1,
					options: 'Country',
					only_select: 1
				},
				{
					fieldname: "column_break0",
					fieldtype: "Column Break",
					width: "50%"
				},
				{
					label: __('Address Type'),
					fieldname: 'address_type',
					fieldtype: 'Select',
					options: [
						{ "label": __("Billing"), "value": "Billing" },
						{ "label": __("Shipping"), "value": "Shipping" },
					],
					reqd: 1
				},
				{
					label: __('Postal Code'),
					fieldname: 'pincode',
					fieldtype: 'Data'
				},
				{
					fieldname: "phone",
					fieldtype: "Data",
					label: "Phone"
				}
			],
			primary_action_label: __('Save'),
			primary_action: (values) => {
				frappe.call('erpnext.shopping_cart.cart.add_new_address', { doc: values })
					.then(r => {
						frappe.call({
							method: "erpnext.shopping_cart.cart.update_cart_address",
							args: {
								address_type: r.message.address_type,
								address_name: r.message.name
							},
							callback: function (r) {
								d.hide();
								window.location.reload();
							}
						});
					});
			}
		})

		d.show();
	});

	function setup_state() {
		const shipping_address = $('[data-section="shipping-address"]')
			.find('[data-address-name][data-active]').attr('data-address-name');

		const billing_address = $('[data-section="billing-address"]')
			.find('[data-address-name][data-active]').attr('data-address-name');

		$('#input_same_billing').prop('checked', shipping_address === billing_address).trigger('change');

		if (!shipping_address && !billing_address) {
			$('#input_same_billing').prop('checked', true).trigger('change');
		}

		if (shipping_address) {
			$(`[data-section="shipping-address"] [data-address-name="${shipping_address}"] .address-card`).addClass('active');
		}
		if (billing_address) {
			$(`[data-section="billing-address"] [data-address-name="${billing_address}"] .address-card`).addClass('active');
		}
	}

	setup_state();

	function toggle_billing_address_section(flag) {
		$('[data-section="billing-address"]').toggle(flag);
	}
});