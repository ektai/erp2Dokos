import frappe

def execute():
	if frappe.db.exists("DocType", "Sepa Mandate"):
		return

	frappe.rename_doc("DocType", "GoCardless Mandate", "Sepa Mandate", force=True)
	frappe.reload_doc("accounts", "doctype", "sepa_mandate")

	mandates = frappe.get_all("Sepa Mandate")
	for mandate in mandates:
		frappe.db.set_value("Sepa Mandate", mandate.name, "registered_on_gocardless", 1)
