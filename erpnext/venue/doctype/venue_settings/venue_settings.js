// Copyright (c) 2020, Dokos SAS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Venue Settings', {
	// refresh: function(frm) {

	// }
});

frappe.tour['Venue Settings'] = [
	{
		fieldname: "minute_uom",
		title: __("Minute UOM"),
		description: __("Unit of measure corresponding to one minute"),
	},
	{
		fieldname: "clear_item_booking_draft_duration",
		title: __("Clear bookings in shopping cart after x minutes"),
		description: __("Time interval between the last modification of an item booking with status 'In Cart' and its automatic deletion."),
	},
	{
		fieldname: "enable_simultaneous_booking",
		title: __("Enable simultaneous booking"),
		description: __("Activates the possibility to set a number of allowed simultaneous bookings for each item in the item master data."),
	},
	{
		fieldname: "sync_with_google_calendar",
		title: __("Automatically synchronize with Google Calendar"),
		description: __("If checked, items booked on the portal will be automatically synchronized with Google Calendar."),
	},
]