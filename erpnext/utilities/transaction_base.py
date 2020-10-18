# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import frappe.share
from frappe import _
from frappe.utils import cstr, now_datetime, cint, flt, get_time, get_datetime, get_link_to_form, date_diff, nowdate
from erpnext.controllers.status_updater import StatusUpdater
from erpnext.accounts.utils import get_fiscal_year

from six import string_types

class UOMMustBeIntegerError(frappe.ValidationError): pass

class TransactionBase(StatusUpdater):
	def validate_posting_time(self):
		# set Edit Posting Date and Time to 1 while data import
		if frappe.flags.in_import and self.posting_date:
			self.set_posting_time = 1

		if not getattr(self, 'set_posting_time', None):
			now = now_datetime()
			self.posting_date = now.strftime('%Y-%m-%d')
			self.posting_time = now.strftime('%H:%M:%S.%f')
		elif self.posting_time:
			try:
				get_time(self.posting_time)
			except ValueError:
				frappe.throw(_('Invalid Posting Time'))

		self.validate_future_posting()
		self.validate_with_last_transaction_posting_time()

	def is_stock_transaction(self):
		if self.doctype not in ["Sales Invoice", "Purchase Invoice", "Stock Entry", "Stock Reconciliation",
			"Delivery Note", "Purchase Receipt", "Fees"]:
				return False

		if self.doctype in ["Sales Invoice", "Purchase Invoice"]:
			if not (self.get("update_stock") or self.get("is_pos")):
				return False

		return True

	def validate_future_posting(self):
		if not self.is_stock_transaction():
			return

		if getattr(self, 'set_posting_time', None) and date_diff(self.posting_date, nowdate()) > 0:
			msg = _("Posting future transactions are not allowed due to Immutable Ledger")
			frappe.throw(msg, title=_("Future Posting Not Allowed"))

	def add_calendar_event(self, opts, force=False):
		if cstr(self.contact_by) != cstr(self._prev.contact_by) or \
				cstr(self.contact_date) != cstr(self._prev.contact_date) or force or \
				(hasattr(self, "ends_on") and cstr(self.ends_on) != cstr(self._prev.ends_on)):

			self._add_calendar_event(opts)

	def _add_calendar_event(self, opts):
		opts = frappe._dict(opts)

		if self.contact_date:
			event = frappe.get_doc({
				"doctype": "Event",
				"owner": opts.owner or self.owner,
				"subject": opts.subject,
				"description": opts.description,
				"starts_on":  self.contact_date,
				"ends_on": opts.ends_on,
				"event_type": "Private"
			})

			event.insert(ignore_permissions=True)

			if frappe.db.exists("User", self.contact_by):
				frappe.share.add("Event", event.name, self.contact_by,
					flags={"ignore_share_permission": True})

	def validate_uom_is_integer(self, uom_field, qty_fields):
		validate_uom_is_integer(self, uom_field, qty_fields)

	def validate_with_previous_doc(self, ref):
		self.exclude_fields = ["conversion_factor", "uom"] if self.get('is_return') else []

		for key, val in ref.items():
			is_child = val.get("is_child_table")
			ref_doc = {}
			item_ref_dn = []
			for d in self.get_all_children(self.doctype + " Item"):
				ref_dn = d.get(val["ref_dn_field"])
				if ref_dn:
					if is_child:
						self.compare_values({key: [ref_dn]}, val["compare_fields"], d)
						if ref_dn not in item_ref_dn:
							item_ref_dn.append(ref_dn)
						elif not val.get("allow_duplicate_prev_row_id"):
							frappe.throw(_("Duplicate row {0} with same {1}").format(d.idx, key))
					elif ref_dn:
						ref_doc.setdefault(key, [])
						if ref_dn not in ref_doc[key]:
							ref_doc[key].append(ref_dn)
			if ref_doc:
				self.compare_values(ref_doc, val["compare_fields"])

	def compare_values(self, ref_doc, fields, doc=None):
		for reference_doctype, ref_dn_list in ref_doc.items():
			for reference_name in ref_dn_list:
				prevdoc_values = frappe.db.get_value(reference_doctype, reference_name,
					[d[0] for d in fields], as_dict=1)

				if not prevdoc_values:
					frappe.throw(_("Invalid reference {0} {1}").format(reference_doctype, reference_name))

				for field, condition in fields:
					if prevdoc_values[field] is not None and field not in self.exclude_fields:
						self.validate_value(field, condition, prevdoc_values[field], doc)


	def validate_rate_with_reference_doc(self, ref_details):
		buying_doctypes = ["Purchase Order", "Purchase Invoice", "Purchase Receipt"]

		if self.doctype in buying_doctypes:
			to_disable = "Maintain same rate throughout Purchase cycle"
			settings_page = "Buying Settings"
		else:
			to_disable = "Maintain same rate throughout Sales cycle"
			settings_page = "Selling Settings"

		for ref_dt, ref_dn_field, ref_link_field in ref_details:
			for d in self.get("items"):
				if d.get(ref_link_field):
					ref_rate = frappe.db.get_value(ref_dt + " Item", d.get(ref_link_field), "rate")

					if abs(flt(d.rate - ref_rate, d.precision("rate"))) >= .01:
						frappe.msgprint(_("Row #{0}: Rate must be same as {1}: {2} ({3} / {4}) ")
							.format(d.idx, ref_dt, d.get(ref_dn_field), d.rate, ref_rate))
						frappe.throw(_("To allow different rates, disable the {0} checkbox in {1}.")
							.format(frappe.bold(_(to_disable)),
							get_link_to_form(settings_page, settings_page, frappe.bold(settings_page))))

	def get_link_filters(self, for_doctype):
		if hasattr(self, "prev_link_mapper") and self.prev_link_mapper.get(for_doctype):
			fieldname = self.prev_link_mapper[for_doctype]["fieldname"]

			values = filter(None, tuple([item.as_dict()[fieldname] for item in self.items]))

			if values:
				ret = {
					for_doctype : {
						"filters": [[for_doctype, "name", "in", values]]
					}
				}
			else:
				ret = None
		else:
			ret = None

		return ret

	def validate_with_last_transaction_posting_time(self):

		if not self.is_stock_transaction():
			return

		for item in self.get('items'):
			last_transaction_time = frappe.db.sql("""
				select MAX(timestamp(posting_date, posting_time)) as posting_time
				from `tabStock Ledger Entry`
				where docstatus = 1 and item_code = %s """, (item.item_code))[0][0]

			cur_doc_posting_datetime = "%s %s" % (self.posting_date, self.get("posting_time") or "00:00:00")

			if last_transaction_time and get_datetime(cur_doc_posting_datetime) < get_datetime(last_transaction_time):
				msg = _("Last Stock Transaction for item {0} was on {1}.").format(frappe.bold(item.item_code), frappe.bold(last_transaction_time))
				msg += "<br><br>" + _("Stock Transactions for Item {0} cannot be posted before this time.").format(frappe.bold(item.item_code))
				msg += "<br><br>" + _("Please remove this item and try to submit again or update the posting time.")
				frappe.throw(msg, title=_("Backdated Stock Entry"))

	def add_subscription_event(self):
		if getattr(self, "subscription", None) and self.doctype in ("Sales Order", "Sales Invoice", "Payment Entry"):
			from erpnext.accounts.doctype.subscription.subscription_state_manager import SubscriptionPeriod
			subscription = frappe.get_doc("Subscription", self.subscription)
			existing_event = frappe.db.get_value("Subscription Event", {
				"subscription": subscription.name,
				"document_type": self.doctype,
				"document_name": self.name
			})
			start = getattr(self, "from_date", None) or subscription.current_invoice_start or subscription.start
			end = getattr(self, "to_date", None) or subscription.current_invoice_end

			if not subscription.generate_invoice_at_period_start:
				previous_period = SubscriptionPeriod(
					subscription,
					start=start,
					end=end
				).get_previous_period()
				if previous_period:
					start = previous_period[0].period_start
					end = previous_period[0].period_end

			if existing_event:
				for key, value in (("period_start", start), ("period_end", end)):
					frappe.db.set_value("Subscription Event", existing_event, key, value)
			else:
				subscription.add_subscription_event(f"{self.doctype.capitalize()} created", **{
					"document_type": self.doctype,
					"document_name": self.name,
					"period_start": start,
					"period_end": end
				})

def validate_uom_is_integer(doc, uom_field, qty_fields, child_dt=None):
	if isinstance(qty_fields, string_types):
		qty_fields = [qty_fields]

	distinct_uoms = list(set([d.get(uom_field) for d in doc.get_all_children()]))
	integer_uoms = list(filter(lambda uom: frappe.db.get_value("UOM", uom,
		"must_be_whole_number", cache=True) or None, distinct_uoms))

	if not integer_uoms:
		return

	for d in doc.get_all_children(parenttype=child_dt):
		if d.get(uom_field) in integer_uoms:
			for f in qty_fields:
				qty = d.get(f)
				if qty:
					if abs(cint(qty) - flt(qty)) > 0.0000001:
						frappe.throw(_("Row {1}: Quantity ({0}) cannot be a fraction. To allow this, disable '{2}' in UOM {3}.") \
							.format(qty, d.idx, frappe.bold(_("Must be Whole Number")), frappe.bold(d.get(uom_field))), UOMMustBeIntegerError)
