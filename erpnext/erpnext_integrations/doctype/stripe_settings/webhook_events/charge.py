# -*- coding: utf-8 -*-
# Copyright (c) 2020, Dokos SAS and contributors
# For license information, please see license.txt

from frappe import _

from .stripe import StripeWebhooksController

class StripeChargeWebhookHandler(StripeWebhooksController):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.set_as_failed(_("The Charge Webhook is no longer supported. Please add Payment Intent to your webhooks instead."))
