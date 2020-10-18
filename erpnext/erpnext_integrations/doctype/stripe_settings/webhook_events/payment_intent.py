# -*- coding: utf-8 -*-
# Copyright (c) 2020, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
from frappe.utils import flt

from erpnext.erpnext_integrations.doctype.stripe_settings.webhook_events.stripe import StripeWebhooksController
from erpnext.erpnext_integrations.doctype.stripe_settings.api import StripeInvoice, StripeSubscription

EVENT_MAP = {
	'payment_intent.created': 'update_payment_request_status',
	'payment_intent.canceled': 'update_payment_request_status',
	'payment_intent.payment_failed': 'update_payment_request_status',
	'payment_intent.processing': 'update_payment_request_status',
	'payment_intent.succeeded': 'create_submit_payment'
}

STATUS_MAP = {
	'payment_intent.created': 'Pending',
	'payment_intent.canceled': 'Failed',
	'payment_intent.payment_failed': 'Failed',
	'payment_intent.processing': 'Pending',
	'payment_intent.succeeded': 'Paid'
}

class StripePaymentIntentWebhookHandler(StripeWebhooksController):
	def __init__(self, **kwargs):
		super(StripePaymentIntentWebhookHandler, self).__init__(**kwargs)

		self.charges = []
		self.event_map = EVENT_MAP
		self.status_map = STATUS_MAP

		self.init_handler()
		self.handle_webhook()

	def get_metadata(self):
		super().get_metadata()
		if not self.metadata:
			invoice_id = self.data.get("data", {}).get("object", {}).get("invoice")
			invoice = StripeInvoice(self.stripe_settings).retrieve(invoice_id) or {}
			metadata = invoice.get("metadata")

			if not metadata and invoice.get("subscription"):
				subscription = StripeSubscription(self.stripe_settings).retrieve(invoice.get("subscription")) or {}
				metadata = subscription.get("metadata")

			self.metadata = metadata

	def update_payment_request_status(self):
		if self.payment_request:
			self.set_references(self.payment_request.doctype, self.payment_request.name)
		self.set_as_completed()

	def get_charges(self):
		self.charges = [x.get("id") for x in self.data.get("data", {}).get("object", {}).get("charges", {}).get("data", [])]