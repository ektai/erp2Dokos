import frappe

class GoCardlessPayoutItems:
	def __init__(self, gateway):
		self.gateway = gateway
		self.client = self.gateway.client

	def get_list(self, payout, **kwargs):
		return self.client.payout_items.list(
			params=dict({
				"payout": payout
			}, **kwargs)
		)