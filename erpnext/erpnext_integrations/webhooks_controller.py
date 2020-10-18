# -*- coding: utf-8 -*-
# Copyright (c) 2020, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
from frappe.utils import nowdate, getdate, flt
from datetime import timedelta
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
from erpnext.accounts.doctype.subscription.subscription_state_manager import SubscriptionPeriod
from erpnext.accounts.doctype.subscription.subscription_transaction import SubscriptionInvoiceGenerator

class WebhooksController():
	def __init__(self, **kwargs):
		self.integration_request = frappe.get_doc(kwargs.get("doctype"), kwargs.get("docname"))
		self.integration_request.db_set("error", None)
		self.data = json.loads(self.integration_request.get("data"))
		self.reference_date = nowdate()
		self.metadata = {}
		self.payment_request = None
		self.subscription = None
		self.sales_invoice = None
		self.sales_order = None
		self.period = {}
		self.event_map = {}
		self.status_map = {}

	def handle_update(self):
		self.process_metadata()
		target = self.event_map.get(self.action_type)
		if not target:
			self.set_as_not_handled()
		else:
			method = getattr(self, target)
			try:
				method()
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), "Webhook processing error")
				self.set_as_failed(e)

	def process_metadata(self):
		reference_doc = {}
		if self.metadata.get("reference_doctype"):
			reference_doc = frappe.get_doc(self.metadata.get("reference_doctype"), self.metadata.get("reference_name"))

		if not reference_doc:
			return

		if reference_doc.doctype == "Subscription" and not self.subscription:
			self.subscription = reference_doc
			if self.payment_request:
				self.period = frappe.db.get_value("Subscription Event", dict(
					event_type="Payment request created",
					subscription=self.subscription.name,
					document_type="Payment Request",
					document_name=self.payment_request.name
				), ["period_start", "period_end"], as_dict=True)

		if reference_doc.doctype == "Sales Invoice" and not self.sales_invoice:
			self.sales_invoice = reference_doc

		if reference_doc.doctype =="Sales Order" and not self.sales_order:
			self.sales_order = reference_doc

	def create_payment(self, reference=None):
		if not reference:
			reference = self.integration_request.get("service_id")

		if not frappe.db.exists("Payment Entry", dict(reference_no=reference, docstatus=("!=", 2))):
			if self.payment_request and not self.subscription:
				payment_entry = self.payment_request.run_method("create_payment_entry", submit=False)
				payment_entry.reference_no = reference
				payment_entry.payment_request = self.payment_request.name
				payment_entry.insert(ignore_permissions=True)
				self.set_references(payment_entry.doctype, payment_entry.name)
				self.set_as_completed()

			# For compatibility
			# All new request should contain a payment_request key in their metadata or provide a way to obtain it in the handler (for subscriptions)
			elif self.metadata.get("reference_doctype") in ("Sales Order", "Sales Invoice"):
				payment_entry = get_payment_entry(self.metadata.get("reference_doctype"), self.metadata.get("reference_name"))
				payment_entry.reference_no = reference
				payment_entry.payment_request = self.payment_request.name if self.payment_request else None
				payment_entry.insert(ignore_permissions=True)
				self.set_references(payment_entry.doctype, payment_entry.name)
				self.set_as_completed()

			elif self.subscription:
				payment_entry = self.subscription.run_method("create_payment")
				payment_entry.reference_no = reference
				payment_entry.subscription = self.subscription.name
				payment_entry.insert(ignore_permissions=True)
				if self.payment_request:
					payment_entry.payment_request = self.payment_request.name
					payment_entry.references = []
					self.add_subscription_references(payment_entry)
				self.set_references(payment_entry.doctype, payment_entry.name)
				self.set_as_completed()

			else:
				self.set_as_failed(_("The reference doctype should be a Payment Request, a Sales Invoice, a Sales Order or a Subscription"))
		else:
			payment_entry = frappe.get_doc("Payment Entry", dict(reference_no=reference))
			self.set_references(payment_entry.doctype, payment_entry.name)
			self.set_as_completed()

	def submit_payment(self, reference=None):
		if not reference:
			reference = self.integration_request.get("service_id")

		if frappe.db.exists("Payment Entry", dict(reference_no=reference, docstatus=0)):
			posting_date = getdate(frappe.parse_json(self.integration_request.data).get("created_at"))
			payment_entry = frappe.get_doc("Payment Entry", dict(reference_no=reference, docstatus=0))
			payment_entry.flags.ignore_permissions = True
			payment_entry.posting_date = posting_date
			payment_entry.reference_date = posting_date

			if hasattr(self, 'add_fees_before_submission'):
				payment_entry.deductions = []
				self.add_fees_before_submission(payment_entry)

			if self.payment_request:
				payment_entry.references = []
				payment_entry.save()
				if self.subscription:
					self.add_subscription_references(payment_entry)
				else:
					self.add_payment_request_references(payment_entry)

			if flt(payment_entry.unallocated_amount) == 0.0:
				payment_entry.submit()
				self.set_as_completed()
			else:
				payment_entry.save()
				self.set_as_completed(_("Please allocate the remaining amount before submitting."))

			self.set_references(payment_entry.doctype, payment_entry.name)
		elif frappe.db.exists("Payment Entry", dict(reference_no=reference, docstatus=1)):
			payment_entry_name = frappe.db.get_value("Payment Entry", dict(reference_no=reference, docstatus=1))
			self.set_references("Payment Entry", payment_entry_name)
			self.set_as_completed()
		else:
			self.set_as_failed(_("Payment entry with reference {0} not found").format(reference))

	def add_subscription_references(self, payment_entry):
		payment_entry.subscription = self.payment_request.is_linked_to_a_subscription()
		references = self.subscription.get_references_for_payment_request(self.payment_request.name)
		allocated = 0.0
		for ref in references:
			allocation = min(flt(payment_entry.unallocated_amount) - flt(allocated), flt(ref.get("outstanding_amount")))
			allocated += allocation
			ref = dict(allocated_amount=allocation, **ref)
			payment_entry.append('references', ref)
		payment_entry.save()

	def add_payment_request_references(self, payment_entry):
		references = self.payment_request.create_payment_entry(submit=False).get("references")
		for ref in references:
			payment_entry.append('references', {
				"reference_doctype": ref.reference_doctype,
				"reference_name": ref.reference_name,
				"outstanding_amount": ref.outstanding_amount,
				"allocated_amount": min(ref.outstanding_amount, payment_entry.get("unallocated_amount"))
			})
			payment_entry.save()

	def cancel_payment(self, reference=None):
		if not reference:
			reference = self.integration_request.get("service_id")

		if frappe.db.exists("Payment Entry", dict(reference_no=reference)):
			payment_entry = frappe.get_doc("Payment Entry", dict(reference_no=reference))
			if payment_entry.docstatus == 1:
				payment_entry.cancel()
			elif payment_entry.docstatus == 0:
				payment_entry.delete()
			self.set_references(payment_entry.doctype, payment_entry.name)
			self.set_as_completed()
		else:
			self.set_as_failed(_("Payment entry with reference {0} not found").format(reference))

	def get_sales_invoice(self, reference=None, start=None, end=None):
		invoice = None
		if reference:
			invoice = frappe.db.get_value("Sales Invoice", {"external_reference": reference, "docstatus": ("!=", 2)})

		if not invoice and self.subscription:
			invoices = SubscriptionPeriod(self.subscription,
				start=start,
				end=end
			).get_current_documents("Sales Invoice")

			if invoices:
				frappe.db.set_value("Sales Invoice", invoices[0].name, "external_reference", reference)
				return invoices[0].name

		return invoice

	def create_sales_invoice(self, period_start, period_end, reference=None):
		invoice = None
		if self.subscription:
			invoice = SubscriptionInvoiceGenerator(
				self.subscription,
				start_date=period_start,
				end_date=period_end,
			).create_invoice()
			invoice.save()

		elif self.sales_invoice:
			invoice = self.sales_invoice

		elif self.sales_order:
			from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
			invoice = make_sales_invoice(self.sales_order.name, ignore_permissions=True)
			invoice.allocate_advances_automatically = True
			invoice.insert(ignore_permissions=True)

		if invoice:
			frappe.db.set_value("Sales Invoice", invoice.name, "external_reference", self.data.get("data", {}).get("object", {}).get("id"))
		return invoice

	def submit_sales_invoice(self, reference=None):
		if not reference:
			reference = self.data.get("data", {}).get("object", {}).get("id")

		invoice = self.get_sales_invoice(reference)
		if invoice:
			si = frappe.get_doc("Sales Invoice", invoice)
			si.submit()
			return si

	def cancel_sales_invoice(self, reference=None):
		if not reference:
			reference = self.data.get("data", {}).get("object", {}).get("id")

		invoice = self.get_sales_invoice(reference)
		if invoice:
			si = frappe.get_doc("Sales Invoice", invoice)
			if si.docstatus == 1:
				si.cancel()
			elif si.docstatus == 0:
				si.delete()
			return si

	def set_references(self, dt, dn):
		self.integration_request.db_set("reference_doctype", dt, update_modified=False)
		self.integration_request.db_set("reference_docname", dn, update_modified=False)
		self.integration_request.load_from_db()

	def set_as_not_handled(self):
		self.integration_request.db_set("error", _("This type of event is not handled"), update_modified=False)
		self.integration_request.load_from_db()
		self.integration_request.update_status({}, "Not Handled")

	def set_as_failed(self, message):
		self.integration_request.db_set("error", str(message), update_modified=False)
		self.integration_request.load_from_db()
		self.integration_request.update_status({}, "Failed")

	def set_as_completed(self, message=None):
		if message:
			self.integration_request.db_set("error", str(message), update_modified=False)
			self.integration_request.load_from_db()
		self.integration_request.update_status({}, "Completed")
		self.update_payment_request()

	def set_as_queued(self, message):
		self.integration_request.db_set("error", str(message), update_modified=False)
		self.integration_request.load_from_db()
		self.integration_request.update_status({}, "Queued")

	def update_payment_request(self):
		if self.payment_request and self.status_map.get(self.action_type) and \
			self.payment_request.status not in (self.status_map.get(self.action_type), 'Paid', 'Completed'):
			frappe.db.set_value(self.payment_request.doctype, self.payment_request.name, 'status', self.status_map.get(self.action_type))


def handle_webhooks(handlers, **kwargs):
	integration_request = frappe.get_doc(kwargs.get("doctype"), kwargs.get("docname"))

	if handlers.get(integration_request.get("service_document")):
		handlers.get(integration_request.get("service_document"))(**kwargs)
	else:
		integration_request.db_set("error", _("This type of event is not handled"))
		integration_request.update_status({}, "Not Handled")