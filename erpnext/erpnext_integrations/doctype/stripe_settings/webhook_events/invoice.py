# -*- coding: utf-8 -*-
# Copyright (c) 2020, Dokos SAS and contributors
# For license information, please see license.txt

import datetime
import json
import frappe
from frappe import _
from frappe.utils import flt, getdate

from erpnext.erpnext_integrations.doctype.stripe_settings.webhook_events.stripe import StripeWebhooksController
from erpnext.erpnext_integrations.doctype.stripe_settings.api import StripeSubscription

EVENT_MAP = {
	'invoice.created': 'get_or_create_invoice',
	'invoice.deleted': 'cancel_invoice',
	'invoice.finalized': 'finalize_invoice',
	'invoice.voided': 'cancel_invoice'
}

class StripeInvoiceWebhookHandler(StripeWebhooksController):
	def __init__(self, **kwargs):
		super(StripeInvoiceWebhookHandler, self).__init__(**kwargs)
		self.event_map = EVENT_MAP

		self.init_handler()
		self.action_type = self.data.get("type")
		self.handle_webhook()

	def get_metadata(self):
		super().get_metadata()
		if not self.metadata:
			subscription_id = self.data.get("data", {}).get("object", {}).get("subscription")
			if subscription_id:
				subscription = StripeSubscription(self.stripe_settings).retrieve(subscription_id)
				self.metadata = subscription.get("metadata")
			else:
				self.metadata = self.data.get("data", {}).get("object", {}).get("lines", {}).get("data")[0].get("metadata")

	def get_or_create_invoice(self):
		reference = self.data.get("data", {}).get("object", {}).get("id")

		if not self.payment_request:
			return self.set_as_queued(_("The corresponding payment request could not be found"))

		period_start = self.period.get("period_start") or self.period_start
		period_end = self.period.get("period_end") or self.period_end

		invoice = self.get_sales_invoice(reference, period_start, period_end)

		if not invoice:
			invoice = self.create_sales_invoice(period_start, period_end, reference)
		else:
			invoice = frappe.get_doc("Sales Invoice", invoice)

		if invoice:
			self.set_references(invoice.doctype, invoice.name)
			self.set_as_completed()
		else:
			self.set_as_failed(_("The corresponding sales invoice could not be found or created."))

	def cancel_invoice(self):
		try:
			invoice = self.cancel_sales_invoice()
			if invoice:
				self.set_references(invoice.doctype, invoice.name)
			self.set_as_completed()
		except Exception as e:
			self.set_as_failed(e)

	def finalize_invoice(self):
		submit_invoice = self.subscription.submit_invoice if self.subscription else True
		if submit_invoice:
			try:
				invoice = self.submit_sales_invoice()
				if invoice:
					self.set_references(invoice.doctype, invoice.name)
			except Exception as e:
				self.set_as_failed(e)

		self.set_as_completed()