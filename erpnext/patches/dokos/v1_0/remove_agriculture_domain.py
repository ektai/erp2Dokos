from __future__ import unicode_literals
import frappe

def execute():
	frappe.reload_doc("Assets", "DocType", "Location")
	# Delete assigned roles
	roles = ["Agriculture Manager", "Agriculture User"]
	doctypes = [x["name"] for x in frappe.get_all("DocType", filters={"module": "Agriculture"})]

	frappe.db.sql("""
	DELETE
	FROM 
		`tabHas Role`
	WHERE 
		role in ({0})
	""".format(','.join(['%s']*len(roles))), tuple(roles))

	if doctypes:
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
		{"document": "Item Group", "items": ["Fertilizer", "Seed", "By-product", "Produce"]},
		{"document": "Report", "items": [x["name"] for x in frappe.get_all("Report", filters={"ref_doctype": ["in", doctypes]})]},
		{"document": "DocType", "items": doctypes},
		{"document": "Role", "items": roles},
		{"document": "Module Def", "items": ["Agriculture"]},
		{"document": "Domain", "items": ["Agriculture"]}
	]

	for element in elements:
		for item in element["items"]:
			try:
				frappe.delete_doc(element["document"], item)
			except Exception as e:
				print(e)

	# Delete Desktop Icons
	desktop_icons = [
		'Agriculture Task',
		'Crop',
		'Crop Cycle',
		'Fertilizer',
		'Item',
		'Location',
		'Disease',
		'Plant Analysis',
		'Soil Analysis',
		'Soil Texture',
		'Task',
		'Water Analysis',
		'Weather'
	]

	frappe.db.sql("""
	DELETE
	FROM 
		`tabDesktop Icon`
	WHERE 
		module_name in ({0})
	""".format(','.join(['%s']*len(desktop_icons))), tuple(desktop_icons))
