from __future__ import unicode_literals
import frappe
from frappe import _

def execute():
	# Delete assigned roles
	roles = ["Healthcare Administrator", "LabTest Approver", "Laboratory User", "Nursing User", "Physician", "Patient"]
	doctypes = [x["name"] for x in frappe.get_all("DocType", filters={"module": "Healthcare"})]

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
		{"document": "Item Group", "items": [_('Laboratory'), _('Drug')]},
		{"document": "Custom Field", "items": [x["name"] for x in frappe.get_all("Custom Field", filters={"dt": ["in", doctypes]})]},
		{"document": "Web Form", "items": [x["name"] for x in frappe.get_all("Web Form", filters={"module": "Healthcare"})]},
		{"document": "Print Format", "items": [x["name"] for x in frappe.get_all("Print Format", filters={"doc_type": ["in", doctypes]})]},
		{"document": "Report", "items": [x["name"] for x in frappe.get_all("Report", filters={"ref_doctype": ["in", doctypes]})]},
		{"document": "DocType", "items": doctypes},
		{"document": "Page", "items": [x["name"] for x in frappe.get_all("Page", filters={"module": "Healthcare"})]},
		{"document": "Role", "items": roles},
		{"document": "Module Def", "items": ["Healthcare"]},
		{"document": "Domain", "items": ["Healthcare"]}
	]

	for element in elements:
		for item in element["items"]:
			try:
				frappe.delete_doc(element["document"], item)
			except Exception as e:
				print(e)

	# Delete Desktop Icons
	desktop_icons = ["Patient", "Patient Appointment", "Patient Encounter", "Lab Test", "Healthcare", "Vital Signs", "Clinical Procedure", "Inpatient Record"]

	frappe.db.sql("""
	DELETE
	FROM 
		`tabDesktop Icon`
	WHERE 
		module_name in ({0})
	""".format(','.join(['%s']*len(desktop_icons))), tuple(desktop_icons))