# -*- coding: utf-8 -*-
# Copyright (c) 2020, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
from frappe.utils import flt, getdate

from erpnext.erpnext_integrations.webhooks_controller import WebhooksController
from erpnext.erpnext_integrations.doctype.gocardless_settings.api import GoCardlessPayments, GoCardlessPayouts, GoCardlessPayoutItems

EVENT_MAP = {
	'created': 'create_payment',
	'submitted': 'create_payment',
	'confirmed': 'submit_payment',
	'cancelled': 'cancel_payment',
	'failed': 'cancel_payment',
	'paid_out': 'submit_payment'
}

STATUS_MAP = {
	'created': 'Pending',
	'submitted': 'Pending',
	'confirmed': 'Paid',
	'cancelled': 'Failed',
	'failed': 'Failed',
	'paid_out': 'Paid'
}

class GoCardlessPaymentWebhookHandler(WebhooksController):
	def __init__(self, **kwargs):
		super(GoCardlessPaymentWebhookHandler, self).__init__(**kwargs)
		self.gocardless_settings = None
		self.payment_gateway = None
		self.gocardless_payment = {}

		self.event_map = EVENT_MAP
		self.status_map = STATUS_MAP
		self.init_handler()

		if self.gocardless_payment and self.metadata:
			frappe.db.set_value(self.integration_request.doctype, self.integration_request.name, "service_id",\
				self.gocardless_payment.id, update_modified=False)
			self.integration_request.load_from_db()

			self.action_type = self.data.get("action")
			self.handle_update()
		else:
			self.set_as_completed(_("No payment reference and metadata found in this webhook"))

	def init_handler(self):
		self.gocardless_settings = frappe.get_doc("GoCardless Settings", self.integration_request.get("payment_gateway_controller"))
		self.payment_gateway = frappe.get_doc("Payment Gateway", dict(
			gateway_settings="GoCardless Settings",
			gateway_controller=self.integration_request.get("payment_gateway_controller")
			)
		)

		self.get_payment()
		self.get_reference_date()
		self.get_metadata()
		self.get_payment_request()

	def get_payment(self):
		payment = self.data.get("links", {}).get("payment")
		self.gocardless_payment = GoCardlessPayments(self.gocardless_settings).get(payment)

	def get_reference_date(self):
		self.reference_date = getdate(self.gocardless_payment.charge_date)

	def get_payout(self):
		self.gocardless_payout = self.data.get("links", {}).get("payout") or getattr(self.gocardless_payment.links, "payout", {})

	def get_metadata(self):
		self.metadata = getattr(self.gocardless_payment, "metadata", {})

	def get_payment_request(self):
		if self.metadata.get("payment_request"):
			self.payment_request = frappe.get_doc("Payment Request", self.metadata.get("payment_request"))

	def add_fees_before_submission(self, payment_entry):
		self.get_payout()
		if self.gocardless_payout:
			payout = GoCardlessPayouts(self.gocardless_settings).get(self.gocardless_payout)
			payout_items = GoCardlessPayoutItems(self.gocardless_settings).get_list(self.gocardless_payout)

			output = ""
			for p in payout_items.records:
				output += (str(p.__dict__) + "\n") if getattr(p.links, "payment") == self.gocardless_payment.id else ""
			frappe.db.set_value(self.integration_request.doctype, self.integration_request.name, "output", output)

			base_amount = self.get_base_amount(payout_items.records)
			fee_amount = self.get_fee_amount(payout_items.records)
			exchange_rate = self.get_exchange_rate(payout)

			payment_entry.mode_of_payment = self.payment_gateway.mode_of_payment
			payment_entry.update({
				"target_exchange_rate": exchange_rate,
			})

			if fee_amount and self.payment_gateway.fee_account and self.payment_gateway.cost_center:
				fees = flt(fee_amount) * flt(payment_entry.get("target_exchange_rate", 1))
				payment_entry.update({
					"paid_amount": flt(base_amount or payment_entry.paid_amount) + fees,
					"received_amount": flt(payment_entry.received_amount) + fees
				})

				payment_entry.append("deductions", {
					"account": self.payment_gateway.fee_account,
					"cost_center": self.payment_gateway.cost_center,
					"amount": -1 * fee_amount
				})

				payment_entry.set_amounts()

	def get_base_amount(self, payout_items):
		paid_amount = [x.amount for x in payout_items if (x.type == "payment_paid_out" and getattr(x.links, "payment") == self.gocardless_payment.id)]
		total = 0
		for p in paid_amount:
			total += flt(p)
		return total / 100

	def get_fee_amount(self, payout_items):
		fee_amount = [x.amount for x in payout_items if ((x.type == "gocardless_fee" or x.type == "app_fee") and getattr(x.links, "payment") == self.gocardless_payment.id)]
		total = 0
		for p in fee_amount:
			total += flt(p)
		return total / 100

	@staticmethod
	def get_exchange_rate(payment):
		return flt(getattr(payment.fx, "exchange_rate", 1) or 1)
