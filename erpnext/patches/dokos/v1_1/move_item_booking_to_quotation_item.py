import frappe

def execute():
	frappe.reload_doc("stock", "doctype", "item_booking")
	frappe.reload_doc("selling", "doctype", "quotation")
	frappe.reload_doc("selling", "doctype", "quotation_item")
	frappe.reload_doc("selling", "doctype", "sales_order")
	frappe.reload_doc("selling", "doctype", "sales_order_item")

	if frappe.db.field_exists("Item Booking", "reference_doctype") and \
		frappe.db.field_exists("Item Booking", "reference_name"):
		item_bookings = frappe.get_all("Item Booking", \
			fields=["name", "item", "reference_doctype", "reference_name"])

		for booking in item_bookings:
			if booking.get("reference_doctype") and booking.get("reference_name"):
				doc = frappe.get_doc(booking.get("reference_doctype"), booking.get("reference_name"))

				for item in doc.items:
					if item.item_code == booking.get("item"):
						if booking.get("reference_doctype") == "Quotation":
							frappe.db.set_value("Quotation Item", item.name, "item_booking", booking.get("name"))
						elif booking.get("reference_doctype") == "Sales Order":
							frappe.db.set_value("Sales Order Item", item.name, "item_booking", booking.get("name"))
						else:
							print("Not linked to a quotation or sales order {0}: {1}".format(\
								booking.get("name"), doc.name))
							b = frappe.get_doc("Item Booking", booking.get("name"))
							b.add_comment('Comment', "Linked to {0}: {1}".format(booking.get("reference_doctype"), \
								booking.get("reference_name")))
