import frappe

class GoCardlessCustomers:
	def __init__(self, gateway):
		self.gateway = gateway
		self.client = self.gateway.client

	# Restricted to GoCardless Pro
	def create(self, **kwargs):
		return self.client.customers.create(
			params=kwargs
		)

	def get(self, id):
		return self.client.customers.get(
			id
		)

	def update(self, id, **kwargs):
		return self.client.customers.update(
			id,
			params=kwargs
		)

	def remove(self, id):
		return self.client.customers.remove(
			id,
		)

	def get_list(self, **kwargs):
		return self.client.customers.list(
			params=kwargs
		)

	def register(self, gocardless_id, customer):
		try:
			if frappe.db.exists("Integration References", dict(customer=customer)):
				doc = frappe.get_doc("Integration References", dict(customer=customer))
				doc.gocardless_customer_id = gocardless_id
				doc.gocardless_settings = self.gateway.name
				doc.save(ignore_permissions=True)

			else:
				frappe.get_doc({
					"doctype": "Integration References",
					"customer": customer,
					"gocardless_customer_id": gocardless_id,
					"gocardless_settings": self.gateway.name
				}).insert(ignore_permissions=True)
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(e, "GoCardless Customer ID Registration Error")