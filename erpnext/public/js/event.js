// Copyright (c) 2020, Dokos and Contributors
// License: See license.txt

frappe.ui.form.on('Event', {
	setup(frm) {
		frm.custom_make_buttons = {
			'Item Booking': 'Book an item'
		}
	},
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Book an item'), function () {
				itemBookingDialog(frm)
			});
		}
	}
});

const itemBookingDialog = frm => {
	const d = new frappe.ui.form.MultiSelectDialog({
		doctype: "Item",
		target: "Item Booking",
		setters: [
			{
				"fieldname": "item_name",
				"fieldtype": "Data",
				"hidden": 1
			},
			{
				"fieldname": "enable_item_booking",
				"fieldtype": "Check",
				"value": 1,
				"hidden": 1
			}
		],
		primary_action_label: __("Book Item·s"),
		action: function(selections) {
			const values = selections;
			if(values.length === 0){
				frappe.msgprint(__("Please select at least one item"))
				return;
			}
			book_items(frm, values)
			d.dialog.hide();
		},
	});
}

const book_items = (frm, values) => {
	const promises = []
	values.forEach(value => {
		promises.push(new_booking(frm, value))
	})

	Promise.all(promises).then(r => {
		frm.refresh();
	})
}

const new_booking = (frm, value) => {
	return frappe.xcall('erpnext.venue.doctype.item_booking.item_booking.book_new_slot', {
		item: value,
		start: frm.doc.starts_on,
		end: frm.doc.ends_on,
		status: "Not confirmed",
		event: frm.doc.name,
		all_day: frm.doc.all_day
	})
}