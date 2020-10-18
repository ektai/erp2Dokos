from __future__ import unicode_literals
import frappe
from frappe import _

def execute():
	frappe.reload_doc('website', 'doctype', 'portal_settings')
	# Delete assigned roles
	roles = ["Non Profit Manager", "Non Profit Member", "Non Profit Portal User"]
	doctypes = [x["name"] for x in frappe.get_all("DocType", filters={"module": "Non Profit"})]

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
		{"document": "Web Form", "items": [x["name"] for x in frappe.get_all("Web Form", filters={"module": "Non Profit"})]},
		{"document": "Report", "items": [x["name"] for x in frappe.get_all("Report", filters={"ref_doctype": ["in", doctypes]})]},
		{"document": "DocType", "items": doctypes},
		{"document": "Role", "items": roles},
		{"document": "Module Def", "items": ["Non Profit"]},
		{"document": "Domain", "items": ["Non Profit"]}
	]

	for element in elements:
		for item in element["items"]:
			try:
				frappe.delete_doc(element["document"], item)
			except Exception as e:
				print(e)

	# Delete Desktop Icons
	desktop_icons = ["Non Profit", "Member", "Donor", "Volunteer", "Grant Application"]

	frappe.db.sql("""
	DELETE
	FROM 
		`tabDesktop Icon`
	WHERE 
		module_name in ({0})
	""".format(','.join(['%s']*len(desktop_icons))), tuple(desktop_icons))