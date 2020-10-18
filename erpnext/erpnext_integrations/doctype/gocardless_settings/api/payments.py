import frappe
from erpnext.erpnext_integrations.idempotency import IdempotencyKey, handle_idempotency

class GoCardlessPayments:
	def __init__(self, gateway, payment_request=None):
		self.gateway = gateway
		self.client = self.gateway.client
		self.payment_request = payment_request

	@handle_idempotency
	def create(self, **kwargs):
		return self.client.payments.create(
			params=kwargs,
			headers={
				'Idempotency-Key' : IdempotencyKey("payments", "create", self.payment_request.name).get(),
			}
		)

	def get(self, id):
		return self.client.payments.get(
			id
		)

	def get_list(self, params):
		return self.client.payments.list(
			params=params
		)

	def update(self, id, **kwargs):
		return self.client.payments.update(
			id,
			params=kwargs
		)

	def cancel(self, id, **kwargs):
		return self.client.payments.cancel(
			id,
			params=kwargs
		)

	def retry(self, id, **kwargs):
		return self.client.payments.retry(
			id,
			params=kwargs
		)