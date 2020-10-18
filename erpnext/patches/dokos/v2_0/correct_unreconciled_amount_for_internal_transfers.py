import frappe
from frappe.utils import flt

def execute():
	for payment in frappe.get_all("Payment Entry",
		filters={"payment_type": "Internal Transfer"},
		fields=["unreconciled_from_amount", "unreconciled_to_amount", "name"]):
		frappe.db.set_value("Payment Entry", payment.name, "unreconciled_amount", (flt(payment.unreconciled_from_amount) + flt(payment.unreconciled_to_amount)))
		frappe.get_doc("Payment Entry", payment.name).set_status(update=True)