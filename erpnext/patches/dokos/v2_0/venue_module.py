import frappe


def execute():
	frappe.reload_doc("venue", "doctype", "Venue Settings")

	stock_settings = frappe.get_single("Stock Settings")
	venue_settings = frappe.get_single("Venue Settings")
	for field in ["minute_uom", "clear_item_booking_draft_duration", "enable_simultaneous_booking", "sync_with_google_calendar"]:
		if hasattr(stock_settings, field):
			setattr(venue_settings, field, getattr(stock_settings, field, None))

	doc = frappe.db.get_value("Scheduled Job Type", dict(method="erpnext.stock.doctype.item_booking.item_booking.clear_draft_bookings"))
	if doc:
		frappe.db.set_value("Scheduled Job Type",
			doc,
			"method",
			"erpnext.venue.doctype.item_booking.item_booking.clear_draft_bookings"
		)