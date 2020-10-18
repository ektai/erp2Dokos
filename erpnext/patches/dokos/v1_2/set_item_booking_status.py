import frappe

def execute():
	frappe.reload_doc("stock", "doctype", "item_booking")
	bookings = frappe.get_all("Item Booking", fields=["name", "docstatus"])

	for booking in bookings:
		if booking.get("docstatus") == 1:
			frappe.db.set_value("Item Booking", booking.get("name"), "status", "Confirmed")
		elif booking.get("docstatus") == 2:
			frappe.db.set_value("Item Booking", booking.get("name"), "status", "Cancelled")

