import frappe

class GoCardlessEvents:
	def __init__(self, gateway):
		self.gateway = gateway
		self.client = self.gateway.client

	def get(self, id):
		return self.client.events.get(
			id
		)

	def get_list(self, **kwargs):
		return self.client.events.list(
			params=kwargs
		)