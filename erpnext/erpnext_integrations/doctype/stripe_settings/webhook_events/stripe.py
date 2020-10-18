# Copyright (c) 2020, Dokos SAS and contributors
# For license information, please see license.txt

import datetime
import frappe
from frappe import _
import json
from frappe.utils import flt, getdate, add_days

from erpnext.erpnext_integrations.webhooks_controller import WebhooksController
from erpnext.erpnext_integrations.doctype.stripe_settings.api import StripeCharge, StripeInvoice

class StripeWebhooksController(WebhooksController):
	def __init__(self, **kwargs):
		super(StripeWebhooksController, self).__init__(**kwargs)
		self.period_start = None
		self.period_end = None
		self.stripe_invoice = {}

	def init_handler(self):
		self.stripe_settings = frappe.get_doc("Stripe Settings", self.integration_request.get("payment_gateway_controller"))
		self.payment_gateway = frappe.get_doc("Payment Gateway", dict(
			gateway_settings="Stripe Settings",
			gateway_controller=self.integration_request.get("payment_gateway_controller")
			)
		)

		self.get_metadata()
		self.get_invoice()
		self.get_payment_request()

	def handle_webhook(self):
		self.action_type = self.data.get("type")

		if self.metadata:
			self.handle_update()
		else:
			self.set_as_failed(_("No metadata found in this webhook"))

	def get_metadata(self):
		self.metadata = self.data.get("data", {}).get("object", {}).get("metadata")

	def get_invoice(self):
		object_type = self.data.get("data", {}).get("object", {}).get("object")
		if object_type == "invoice":
			invoice = self.data.get("data", {}).get("object", {}).get("id")
		else:
			invoice = self.data.get("data", {}).get("object", {}).get("invoice")

		if invoice:
			self.stripe_invoice = StripeInvoice(self.stripe_settings).retrieve(invoice)

	def get_payment_request(self):
		payment_request_id = None

		if self.metadata.get("reference_doctype") == "Subscription":
			self.subscription = frappe.get_doc("Subscription", self.metadata.get("reference_name"))
			if self.stripe_invoice:
				period = self.stripe_invoice.get("lines", {}).get("data", [])[0].get("period", {})
				self.period_start = getdate(datetime.datetime.utcfromtimestamp(period.get("start")))
				self.period_end = getdate(datetime.datetime.utcfromtimestamp(period.get("end")))
			if self.period_start and self.period_end:
				payment_request_id = self.subscription.get_payment_request_for_period(self.period_start, add_days(self.period_end, -1))

		elif self.metadata.get("payment_request"):
			payment_request_id = self.metadata.get("payment_request")
		elif self.metadata.get("reference_doctype") == "Payment Request":
			payment_request_id = self.metadata.get("reference_name")

		if payment_request_id:
			self.payment_request = frappe.get_doc("Payment Request", payment_request_id)

	def add_fees_before_submission(self, payment_entry):
		output = []
		base_amount = exchange_rate = fee_amount = 0.0
		for charge in self.charges:
			stripe_charge = StripeCharge(self.stripe_settings).retrieve(charge)
			output.append(stripe_charge)

			if stripe_charge.balance_transaction.currency != payment_entry.paid_to_account_currency:
				currency_account = frappe.db.get_value("Payment Gateway Account", {
					"payment_gateway": self.payment_gateway.name,
					"currency": stripe_charge.balance_transaction.currency
				}, "payment_account")
				if not currency_account:
					frappe.throw(_("Please create a payment gateway account for currency {0}").format(stripe_charge.balance_transaction.currency))

				payment_entry.update({
					"paid_to": currency_account,
					"paid_to_account_currency": stripe_charge.balance_transaction.currency
				})

			# We suppose all charges within the same payment intent have the same exchange rate
			exchange_rate = (1 / flt(stripe_charge.balance_transaction.get("exchange_rate") or 1))

			base_amount += flt(stripe_charge.balance_transaction.get("amount")) / 100
			fee_amount += flt(stripe_charge.balance_transaction.get("fee")) / 100 * exchange_rate

			payment_entry.mode_of_payment = self.payment_gateway.mode_of_payment

			if exchange_rate:
				payment_entry.update({
					"target_exchange_rate": exchange_rate,
				})

			if fee_amount and self.payment_gateway.fee_account and self.payment_gateway.cost_center:
				payment_entry.update({
					"paid_amount": flt(base_amount or payment_entry.paid_amount) - fee_amount,
					"received_amount": flt(base_amount or payment_entry.received_amount) - fee_amount
				})

				payment_entry.append("deductions", {
					"account": self.payment_gateway.fee_account,
					"cost_center": self.payment_gateway.cost_center,
					"amount": fee_amount
				})

				payment_entry.set_amounts()

		self.integration_request.db_set("output", json.dumps(output, indent=4))

	def create_submit_payment(self):
		self.get_charges()
		if self.charges:
			for charge in self.charges:
				self.create_payment(charge)
				self.submit_payment(charge)