from __future__ import unicode_literals
import frappe

def execute():
	# Delete assigned roles
	roles = ["Hotel Manager", "Hotel Reservation User", "Restaurant Manager"]
	doctypes = [x["name"] for x in frappe.get_all("DocType", filters={"module": ["in", ["Restaurant", "Hotels"]]})]

	frappe.db.sql("""
	DELETE
	FROM 
		`tabHas Role`
	WHERE 
		role in ({0})
	""".format(','.join(['%s']*len(roles))), tuple(roles))

	# Standard portal items
	frappe.db.sql("""
	DELETE
	FROM 
		`tabPortal Menu Item`
	WHERE 
		reference_doctype in ({0})
	""".format(','.join(['%s']*len(doctypes))), tuple(doctypes))

	# Delete DocTypes, Pages, Reports, Roles, Domain and Custom Fields
	elements = [
		{"document": "Custom Field", "items": ["Sales Invoice-restaurant", "Sales Invoice-restaurant_table", "Price List-restaurant_menu"]},
		{"document": "Report", "items": [x["name"] for x in frappe.get_all("Report", filters={"ref_doctype": ["in", doctypes]})]},
		{"document": "DocType", "items": doctypes},
		{"document": "Page", "items": [x["name"] for x in frappe.get_all("Page", filters={"module": ["in", ["Restaurant", "Hotels"]]})]},
		{"document": "Role", "items": roles},
		{"document": "Module Def", "items": ["Restaurant", "Hotels"]},
		{"document": "Domain", "items": ["Hospitality"]}
	]

	for element in elements:
		for item in element["items"]:
			try:
				frappe.delete_doc(element["document"], item)
			except Exception as e:
				print(e)

	# Delete Desktop Icons
	desktop_icons = ["Hotels", "Restaurant"]

	frappe.db.sql("""
	DELETE
	FROM 
		`tabDesktop Icon`
	WHERE 
		module_name in ({0})
	""".format(','.join(['%s']*len(desktop_icons))), tuple(desktop_icons))