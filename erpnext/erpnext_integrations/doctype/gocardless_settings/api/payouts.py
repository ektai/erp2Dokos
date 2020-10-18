import frappe

class GoCardlessPayouts:
	def __init__(self, gateway):
		self.gateway = gateway
		self.client = self.gateway.client

	def get(self, id):
		return self.client.payouts.get(
			id
		)

	def get_list(self, **kwargs):
		return self.client.payouts.list(
			params=kwargs
		)