import frappe
from frappe.utils import nowdate

class GoCardlessMandates:
	def __init__(self, gateway):
		self.gateway = gateway
		self.client = self.gateway.client

	# Restricted to GoCardless Pro
	def create(self, **kwargs):
		return self.client.mandates.create(
			params=kwargs
		)

	def get(self, id):
		return self.client.mandates.get(
			id
		)

	def update(self, id, **kwargs):
		return self.client.mandates.update(
			id,
			params=kwargs
		)

	def remove(self, id):
		return self.client.mandates.remove(
			id,
		)

	def get_list(self, **kwargs):
		return self.client.mandates.list(
			params=kwargs
		)

	def register(self, id, customer):
		if not frappe.db.exists("Sepa Mandate", id):
			frappe.get_doc({
				"doctype": "Sepa Mandate",
				"mandate": id,
				"customer": customer,
				"registered_on_gocardless": 1,
				"creation_date": nowdate()
			}).insert(ignore_permissions=True)
			frappe.db.commit()
