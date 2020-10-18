import frappe

def execute():
	for dt in ["Bank Transaction", "Payment Entry"]:
		for doc in frappe.get_all(dt, filters={"docstatus": 2}):
			frappe.get_doc(dt, doc.name).set_status(update=True)
