# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate, get_url
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.party import get_party_account
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry, get_company_defaults
from erpnext.accounts.doctype.subscription_event.subscription_event import delete_linked_subscription_events
from frappe.integrations.utils import get_payment_gateway_controller
from frappe.utils.background_jobs import enqueue
import json

import warnings

from erpnext.accounts.doctype.subscription.subscription_transaction import SubscriptionPaymentEntryGenerator

class PaymentRequest(Document):
	def before_insert(self):
		if not self.no_payment_link:
			self.generate_payment_key()

	def validate(self):
		if self.get("__islocal"):
			self.status = 'Draft'
		self.validate_reference_document()
		self.validate_payment_request_amount()

		if not self.no_payment_link:
			self.validate_payment_gateways()
			self.payment_gateways_validation()
			self.validate_existing_gateway()
			self.validate_currency()

	def validate_reference_document(self):
		if not self.reference_doctype or not self.reference_name:
			frappe.throw(_("To create a Payment Request reference document is required"))

	def validate_payment_request_amount(self):
		existing_payment_request_amount = \
			get_existing_payment_request_amount(self.reference_doctype, self.reference_name)

		if existing_payment_request_amount:
			ref_doc = frappe.get_doc(self.reference_doctype, self.reference_name)
			if (hasattr(ref_doc, "order_type") \
					and getattr(ref_doc, "order_type") != "Shopping Cart"):
				ref_amount = get_amount(ref_doc)

				if existing_payment_request_amount + flt(self.grand_total)> ref_amount:
					frappe.throw(_("Total Payment Request amount cannot be greater than {0} amount")
						.format(self.reference_doctype))

	def validate_currency(self):
		currency = frappe.db.get_value(self.reference_doctype, self.reference_name, "currency")
		for gateway in self.payment_gateways:
			if not frappe.db.exists("Payment Gateway Account", dict(payment_gateway=gateway.get("payment_gateway"), currency=currency)):
				frappe.msgprint(_("No payment gateway account found for payment gateway {0} and currency {1}."\
					.format(gateway.get("payment_gateway"), currency)))

	def validate_payment_gateways(self):
		if self.payment_gateways_template and not self.payment_gateways:
			template = frappe.get_doc("Portal Payment Gateways Template", self.payment_gateways_template)
			self.payment_gateways = template.payment_gateways

	def validate_existing_gateway(self):
		if not self.payment_gateways and not self.payment_gateway:
			frappe.throw(_("Please add at least one payment gateway"))

	def payment_gateways_validation(self):
		selected_gateways = set([x.payment_gateway for x in self.payment_gateways])
		if selected_gateways:
			gateways = frappe.get_all("Payment Gateway", filters={"name": ["in", selected_gateways]}, fields=["name", "gateway_settings", "gateway_controller"])
			for gateway in gateways:
				if gateway.gateway_settings and gateway.gateway_controller:
					gateway_controller = frappe.get_doc(gateway.gateway_settings, gateway.gateway_controller)
					if hasattr(gateway_controller, "validate_payment_request"):
						try:
							gateway_controller.validate_payment_request(self)
						except Exception as e:
							if frappe.flags.mute_gateways_validation:
								self.payment_gateways = [x for x in self.payment_gateways if x.payment_gateway!=gateway.name]
	
	def set_gateway_account(self):
		accounts = frappe.get_all("Payment Gateway Account",\
			filters={"payment_gateway": self.payment_gateway, "currency": self.currency},\
			fields=["name", "is_default"])

		default_accounts = [x["name"] for x in accounts if x["is_default"]]
		if default_accounts:
			self.db_set("payment_gateway_account", default_accounts[0])
		elif accounts:
			self.db_set("payment_gateway_account", accounts[0]["name"])

	def get_payment_account(self):
		if self.payment_gateway_account:
			return frappe.db.get_value("Payment Gateway Account", self.payment_gateway_account, "payment_account")

	def on_submit(self):
		self.db_set('status', 'Initiated')
		if self.is_linked_to_a_subscription():
			self.create_subscription_event()

		send_mail = True
		ref_doc = frappe.get_doc(self.reference_doctype, self.reference_name)

		if (hasattr(ref_doc, "order_type") and getattr(ref_doc, "order_type") == "Shopping Cart") \
			or self.flags.mute_email or self.mute_email:
			send_mail = False

		if not self.message:
			self.mute_email = True
			send_mail = False

		if send_mail:
			communication = self.make_communication_entry()
			self.send_email(communication)

	def on_cancel(self):
		delete_linked_subscription_events(self)
		self.check_if_payment_entry_exists()
		self.set_as_cancelled()

	def on_trash(self):
		delete_linked_subscription_events(self)

	def make_invoice(self):
		if self.reference_doctype == "Sales Order":
			from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

			si = make_sales_invoice(self.reference_name, ignore_permissions=True)
			si.allocate_advances_automatically = True
			si.insert(ignore_permissions=True)
			si.submit()

	@frappe.whitelist()
	def check_if_immediate_payment_is_autorized(self):
		if not self.payment_gateway:
			self.payment_gateway = self.payment_gateways[0].payment_gateway

		return self.check_immediate_payment_for_gateway(self.payment_gateway)

	def check_immediate_payment_for_gateway(self, gateway):
		"""Returns a boolean"""
		controller = get_payment_gateway_controller(gateway)
		if hasattr(controller, 'on_payment_request_submission'):
			return controller.on_payment_request_submission(self)

		return False

	@frappe.whitelist()
	def process_payment_immediately(self):
		if not self.payment_gateway:
			self.payment_gateway = self.payment_gateways[0].payment_gateway

		return self.get_immediate_payment_for_gateway(self.payment_gateway)

	def get_immediate_payment_for_gateway(self, gateway):
		controller = get_payment_gateway_controller(gateway)
		if hasattr(controller, 'immediate_payment_processing'):
			result = controller.immediate_payment_processing(self)
			self.db_set("transaction_reference", result, commit=True)
			self.db_set("status", "Pending", commit=True)
			return result

	def generate_payment_key(self):
		self.db_set('payment_key', frappe.generate_hash(json.dumps(self.as_dict())))

	def get_customer(self):
		return frappe.db.get_value(self.reference_doctype, self.reference_name, "customer")

	def get_payment_url(self, payment_gateway):
		data = frappe.db.get_value(self.reference_doctype, self.reference_name,\
			["company", "customer"], as_dict=1)
		data.update(frappe.db.get_value("Customer", data.customer, "customer_name", as_dict=1))

		controller = get_payment_gateway_controller(\
			payment_gateway)
		controller.validate_transaction_currency(self.currency)

		if hasattr(controller, 'validate_minimum_transaction_amount'):
			controller.validate_minimum_transaction_amount(self.currency, self.grand_total)

		# All keys kept for backward compatibility
		return controller.get_payment_url(**{
			"amount": flt(self.grand_total, self.precision("grand_total")),
			"title": frappe.safe_encode(data.company),
			"description": frappe.safe_encode(self.subject),
			"reference_doctype": "Payment Request",
			"reference_docname": self.name,
			"payer_email": self.email_to or (frappe.session.user if frappe.session.user != "Guest" else ""),
			"payer_name": frappe.safe_encode(data.customer_name),
			"order_id": self.name,
			"currency": self.currency,
			"payment_key": self.payment_key
		})

	def set_as_paid(self, reference_no=None):
		frappe.flags.mute_messages = True
		payment_entry = self.create_payment_entry(reference_no=reference_no)
		if self.reference_doctype != "Subscription":
			self.make_invoice()
		frappe.flags.mute_messages = False

		return payment_entry

	def create_payment_entry(self, submit=True, reference_no=None):
		"""create entry"""
		frappe.flags.ignore_account_permission = True
		frappe.flags.ignore_permissions = True

		ref_doc = frappe.get_doc(self.reference_doctype, self.reference_name)
		gateway_defaults = frappe.db.get_value("Payment Gateway", self.payment_gateway,\
				["fee_account", "cost_center", "mode_of_payment"], as_dict=1) or dict()

		if self.reference_doctype == "Subscription":
			payment_entry = SubscriptionPaymentEntryGenerator(ref_doc).create_payment()
			payment_entry.bank_account = self.get_payment_account()
		else:
			if self.reference_doctype == "Sales Invoice":
				party_account = ref_doc.debit_to
			else:
				party_account = get_party_account("Customer", ref_doc.get("customer"), ref_doc.company)

			party_account_currency = ref_doc.get("party_account_currency") or get_account_currency(party_account)

			bank_amount = self.grand_total
			if party_account_currency == ref_doc.company_currency and party_account_currency != self.currency:
				party_amount = ref_doc.base_grand_total
			else:
				party_amount = self.grand_total

			payment_entry = get_payment_entry(self.reference_doctype, self.reference_name,
				party_amount=party_amount, bank_account=self.get_payment_account(), bank_amount=bank_amount)

		payment_entry.setup_party_account_field()
		payment_entry.set_missing_values()
		payment_entry.set_exchange_rate()

		payment_entry.update({
			"reference_no": reference_no if reference_no else self.name,
			"reference_date": nowdate(),
			"mode_of_payment": gateway_defaults.get("mode_of_payment"),
			"remarks": _("Payment Entry against {0} {1} via Payment Request {2}").format(self.reference_doctype,
				self.reference_name, self.name)
		})

		if self.exchange_rate:
			payment_entry.update({
				"target_exchange_rate": self.exchange_rate,
			})

		if self.fee_amount and gateway_defaults.get("fee_account") and gateway_defaults.get("cost_center"):
			fees = flt(self.fee_amount) * flt(self.get("target_exchange_rate", 1))
			payment_entry.update({
				"paid_amount": flt(self.base_amount or self.grand_total) - fees,
				"received_amount": flt(self.grand_total) - fees
			})

			payment_entry.append("deductions", {
				"account": gateway_defaults.get("fee_account"),
				"cost_center": gateway_defaults.get("cost_center"),
				"amount": self.fee_amount
			})

			payment_entry.set_amounts()

		if payment_entry.difference_amount:
			company_details = get_company_defaults(ref_doc.company)

			payment_entry.append("deductions", {
				"account": company_details.exchange_gain_loss_account,
				"cost_center": company_details.cost_center,
				"amount": payment_entry.difference_amount
			})

		if submit:
			payment_entry.insert(ignore_permissions=True)
			payment_entry.submit()

		return payment_entry

	def send_email(self, communication=None):
		"""send email with payment link"""
		email_args = {
			"recipients": self.email_to,
			"sender": frappe.session.user if frappe.session.user not in ("Administrator", "Guest") else None,
			"subject": self.subject,
			"message": self.message,
			"now": True,
			"communication": communication.name if communication else None,
			"attachments": [frappe.attach_print(self.reference_doctype, self.reference_name,
				file_name=self.reference_name, print_format=self.print_format)] if self.print_format else []}

		enqueue(method=frappe.sendmail, queue='short', timeout=300, is_async=True, **email_args)

	def set_failed(self):
		self.db_set("status", "Failed")

	def set_as_cancelled(self):
		self.db_set("status", "Cancelled")

	def check_if_payment_entry_exists(self):
		if self.status == "Paid":
			if frappe.get_all("Payment Entry Reference",
				filters={"reference_name": self.reference_name, "docstatus": ["<", 2]},
				fields=["parent"],
				limit=1):
				frappe.throw(_("A payment entry for this reference exists already"), title=_('Error'))

	def make_communication_entry(self):
		"""Make communication entry"""
		try:
			comm = frappe.get_doc({
				"doctype":"Communication",
				"communication_medium": "Email",
				"recipients": self.email_to,
				"subject": self.subject,
				"content": self.message,
				"sent_or_received": "Sent",
				"reference_doctype": self.reference_doctype,
				"reference_name": self.reference_name
			})
			comm.insert(ignore_permissions=True)

			return comm
		except Exception:
			frappe.log_error(frappe.get_traceback(), _("Payment request communication creation error"))

	def get_payment_success_url(self):
		return self.payment_success_url

	def on_payment_authorized(self, status=None, reference_no=None):
		if not status:
			return

		if status in ["Authorized", "Completed"]:
			self.run_method("set_as_paid", reference_no)
			self.db_set('status', 'Paid', commit=True)
		elif status in ["Pending"] and self.reference_doctype != "Subscription":
			self.run_method("make_invoice")

		return self.get_redirection()

	def get_redirection(self):
		redirect_to = "no-redirection"

		# if shopping cart enabled and in session
		shopping_cart_settings = frappe.db.get_value("Shopping Cart Settings",\
			None, ["enabled", "payment_success_url"], as_dict=1)

		if (shopping_cart_settings.get("enabled") and hasattr(frappe.local, "session")\
			and frappe.local.session.user != "Guest"):

			success_url = shopping_cart_settings.get("payment_success_url")
			if success_url:
				redirect_to = ({
					"Orders": "/orders",
					"Invoices": "/invoices",
					"My Account": "/me"
				}).get(success_url, "/me")
			else:
				redirect_to = get_url("/orders/{0}".format(self.reference_name))

		return redirect_to

	@frappe.whitelist()
	def is_linked_to_a_subscription(self):
		if self.reference_doctype == "Subscription":
			return self.reference_name

		meta = frappe.get_meta(self.reference_doctype, self.reference_name)
		has_subscription_field = [df for df in meta.fields if df.fieldname == "subscription"]

		if has_subscription_field:
			return frappe.db.get_value(self.reference_doctype, self.reference_name, "subscription")

		return None

	@frappe.whitelist()
	def get_linked_subscription(self):
		subscription = self.is_linked_to_a_subscription()
		if subscription:
			return frappe.get_doc("Subscription", subscription)

	def create_subscription_event(self):
		from erpnext.accounts.doctype.subscription.subscription_state_manager import SubscriptionPeriod
		subscription = frappe.get_doc("Subscription", self.is_linked_to_a_subscription())
		start = subscription.current_invoice_start
		end = subscription.current_invoice_end

		if not subscription.generate_invoice_at_period_start:
			previous_period = SubscriptionPeriod(subscription).get_previous_period()
			if previous_period:
				start = previous_period[0].period_start
				end = previous_period[0].period_end

		subscription.add_subscription_event("Payment request created", **{
			"document_type": "Payment Request",
			"document_name": self.name,
			"period_start": start,
			"period_end": end
		})


@frappe.whitelist(allow_guest=True)
def make_payment_request(**args):
	"""Make payment request"""

	args = frappe._dict(args)

	ref_doc = frappe.get_doc(args.dt, args.dn)
	grand_total = get_amount(ref_doc)

	if args.loyalty_points and args.dt == "Sales Order":
		from erpnext.accounts.doctype.loyalty_program.loyalty_program import validate_loyalty_points
		loyalty_amount = validate_loyalty_points(ref_doc, int(args.loyalty_points))
		frappe.db.set_value("Sales Order", args.dn, "loyalty_points", int(args.loyalty_points), update_modified=False)
		frappe.db.set_value("Sales Order", args.dn, "loyalty_amount", loyalty_amount, update_modified=False)
		grand_total = grand_total - loyalty_amount

	existing_payment_request = None
	if args.order_type == "Shopping Cart":
		existing_payment_request = frappe.db.get_value("Payment Request",
			{"reference_doctype": args.dt, "reference_name": args.dn, "docstatus": ("!=", 2)})

	if existing_payment_request:
		frappe.db.set_value("Payment Request", existing_payment_request, "grand_total", grand_total, update_modified=False)
		pr = frappe.get_doc("Payment Request", existing_payment_request)

	else:
		if args.order_type != "Shopping Cart" and args.dt != "Subscription":
			existing_payment_request_amount = \
				get_existing_payment_request_amount(args.dt, args.dn)

			if existing_payment_request_amount:
				grand_total -= existing_payment_request_amount

		pr = frappe.new_doc("Payment Request")
		pr.update({
			"currency": ref_doc.currency,
			"no_payment_link": args.no_payment_link,
			"grand_total": grand_total,
			"email_to": args.recipient_id or ref_doc.owner,
			"subject": _("Payment Request for {0}").format(args.dn),
			"reference_doctype": args.dt,
			"reference_name": args.dn
		})

		if args.order_type == "Shopping Cart" or args.mute_email:
			pr.flags.mute_email = True

		if args.get("payment_gateway") or args.order_type == "Shopping Cart":
			gateway_account = get_gateway_details(args) or frappe._dict()
			pr.update({
				"payment_gateway_account": gateway_account.get("name"),
				"payment_gateway": gateway_account.get("payment_gateway")
			})

		if args.submit_doc:
			pr.insert(ignore_permissions=True)
			pr.submit()

	if args.order_type == "Shopping Cart":
		frappe.db.commit()
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = pr.get_payment_url(pr.payment_gateway)

	if args.return_doc:
		return pr

	return pr.as_dict()

@frappe.whitelist()
def get_reference_amount(doctype, docname):
	ref_doc = frappe.get_doc(doctype, docname)
	return get_amount(ref_doc)

def get_amount(ref_doc):
	"""get amount based on doctype"""
	dt = ref_doc.doctype
	if dt == "Sales Order":
		grand_total = flt(ref_doc.grand_total) - flt(ref_doc.advance_paid)

	elif dt == "Sales Invoice":
		if ref_doc.party_account_currency == ref_doc.currency:
			grand_total = flt(ref_doc.outstanding_amount)
		else:
			grand_total = flt(ref_doc.outstanding_amount) / ref_doc.conversion_rate

	elif dt == "Subscription":
		grand_total = flt(ref_doc.grand_total)

	if grand_total > 0 :
		return grand_total

	else:
		frappe.throw(_("There is no outstanding amount for this reference"))

def get_existing_payment_request_amount(ref_dt, ref_dn):
	existing_payment_request_amount = frappe.db.sql("""
		select sum(grand_total)
		from `tabPayment Request`
		where
			reference_doctype = %s
			and reference_name = %s
			and docstatus = 1
			and status != 'Paid'
	""", (ref_dt, ref_dn))
	return flt(existing_payment_request_amount[0][0]) if existing_payment_request_amount else 0

def get_gateway_details(args):
	"""return gateway and payment account of default payment gateway"""
	filters = {}
	if args.get("currency"):
		filters.update({"currency": args.get("currency")})

	if args.get("payment_gateway"):
		filters.update({"payment_gateway": args.get("payment_gateway")})
		return get_payment_gateway_account(filters)

	if args.order_type == "Shopping Cart":
		payment_gateway_account = frappe.get_doc("Shopping Cart Settings").payment_gateway_account
		return get_payment_gateway_account(payment_gateway_account)

	filters.update({"is_default": 1})
	gateway_account = get_payment_gateway_account(filters)

	return gateway_account

def get_payment_gateway_account(args):
	return frappe.db.get_value("Payment Gateway Account", args,
		["name", "payment_gateway"], as_dict=1)

@frappe.whitelist()
def get_print_format_list(ref_doctype):
	print_format_list = ["Standard"]

	print_format_list.extend([p.name for p in frappe.get_all("Print Format",
		filters={"doc_type": ref_doctype})])

	return {
		"print_format": print_format_list
	}

@frappe.whitelist(allow_guest=True)
def resend_payment_email(docname):
	doc = frappe.get_doc("Payment Request", docname)
	communication = doc.make_communication_entry()
	return doc.send_email(communication)

@frappe.whitelist()
def make_payment_entry(docname):
	doc = frappe.get_doc("Payment Request", docname)
	return doc.create_payment_entry(submit=False).as_dict()

def make_status_as_paid(doc, method):
	warnings.warn(
		"make_status_as_paid will be deprecated since it is error prone.",
		FutureWarning
	)
	for ref in doc.references:
		payment_request_name = frappe.db.get_value("Payment Request",
			{"reference_doctype": ref.reference_doctype, "reference_name": ref.reference_name,
			"docstatus": 1})

		if payment_request_name:
			doc = frappe.get_doc("Payment Request", payment_request_name)
			if doc.status != "Paid":
				doc.db_set('status', 'Paid')
				frappe.db.commit()

@frappe.whitelist()
def make_status_as_completed(name):
	frappe.db.set_value("Payment Request", name, "status", "Completed")

@frappe.whitelist()
def get_message(doc, template):
	"""return message with payment gateway link"""

	if isinstance(doc, str):
		doc = json.loads(doc)

	context = {
		"doc": doc,
		"reference": frappe.get_doc(doc.get("reference_doctype"), doc.get("reference_name")),
		"payment_link": get_payment_link(doc.get("payment_key"))
	}

	email_template = frappe.get_doc("Email Template", template)

	return {
		"subject" : frappe.render_template(email_template.subject, context),
		"message" : frappe.render_template(email_template.response, context)
	}

def get_payment_link(payment_key):
	return get_url("/payments?link={0}".format(payment_key))

@frappe.whitelist()
def check_if_immediate_payment_is_autorized(payment_request):
	return frappe.get_doc("Payment Request", payment_request).check_if_immediate_payment_is_autorized()