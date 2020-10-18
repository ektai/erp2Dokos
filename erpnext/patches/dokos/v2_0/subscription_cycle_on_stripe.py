import frappe

def execute():
	frappe.reload_doc("erpnext_integrations", "doctype", "Stripe Settings")
	for doc in frappe.get_all("Stripe Settings"):
		frappe.db.set_value("Stripe Settings", doc.name, "subscription_cycle_on_stripe", 1)