from __future__ import unicode_literals
import frappe
from frappe import _

def execute():
	# Delete assigned roles
	roles = ["Student", "Instructor", "Academics User", "Education Manager", "Guardian"]
	doctypes = [x["name"] for x in frappe.get_all("DocType", filters={"module": "Education"})]

	frappe.db.sql("""
	DELETE
	FROM 
		`tabHas Role`
	WHERE 
		role in ({0})
	""".format(','.join(['%s']*len(roles))), tuple(roles))

	frappe.db.sql("""
	DELETE
	FROM 
		`tabDocPerm`
	WHERE 
		role in ({0})
	""".format(','.join(['%s']*len(roles))), tuple(roles))

	# Standard portal items
	if doctypes:
		frappe.db.sql("""
		DELETE
		FROM 
			`tabPortal Menu Item`
		WHERE 
			reference_doctype in ({0})
		""".format(','.join(['%s']*len(doctypes))), tuple(doctypes))

	# Delete DocTypes, Pages, Reports, Roles, Domain and Custom Fields

	elements = [
		{"document": "Web Form", "items": [x["name"] for x in frappe.get_all("Web Form", filters={"module": "Education"})]},
		{"document": "Report", "items": [x["name"] for x in frappe.get_all("Report", filters={"ref_doctype": ["in", doctypes]})]},
		{"document": "DocType", "items": doctypes},
		{"document": "Page", "items": [x["name"] for x in frappe.get_all("Page", filters={"module": "Education"})]},
		{"document": "Role", "items": roles},
		{"document": "Module Def", "items": ["Education"]},
		{"document": "Domain", "items": ["Education"]}
	]

	for element in elements:
		for item in element["items"]:
			try:
				frappe.delete_doc(element["document"], item)
			except Exception as e:
				print(e)

	# Delete Desktop Icons
	desktop_icons = ["Student", "Program", "Course", "Student Group", "Instructor", "Fees"]

	frappe.db.sql("""
	DELETE
	FROM 
		`tabDesktop Icon`
	WHERE 
		module_name in ({0})
	""".format(','.join(['%s']*len(desktop_icons))), tuple(desktop_icons))