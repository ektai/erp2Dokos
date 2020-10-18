import frappe
from frappe.utils.data import nowdate, getdate, add_days, get_last_day, add_to_date, flt

class SubscriptionPeriod:
	def __init__(self, subscription, start=None, end=None):
		self.subscription = subscription
		self.start = start or self.subscription.current_invoice_start or self.subscription.start
		self.end = end or self.subscription.current_invoice_end

	def validate(self):
		current_invoice_start = self.get_current_invoice_start()
		if self.subscription.current_invoice_start != current_invoice_start:
			self.subscription.current_invoice_start = current_invoice_start
			self.subscription.db_set("current_invoice_start", current_invoice_start, update_modified=False)

		current_invoice_end = self.get_current_invoice_end()
		if self.subscription.current_invoice_end != current_invoice_end:
			self.subscription.current_invoice_end = current_invoice_end
			self.subscription.db_set("current_invoice_end", current_invoice_end, update_modified=False)

			if not self.subscription.is_new():
				self.subscription.add_subscription_event("New period")

	def get_current_invoice_start(self):
		if SubscriptionStateManager(self.subscription).is_trial() \
			or (self.subscription.cancellation_date and getdate(self.subscription.cancellation_date) < getdate(nowdate())):
			return None
		elif self.subscription.is_new() or self.start is None:
			return max(getdate(self.subscription.start), add_days(getdate(self.subscription.trial_period_end), 1)) if self.subscription.trial_period_end else self.subscription.start 
		elif self.subscription.get_doc_before_save() \
			and self.subscription.get_doc_before_save().billing_interval != self.subscription.billing_interval:
			return add_days(getdate(self.end), 1) if getdate(nowdate()) > getdate(self.end) else getdate(self.start)
		elif self.subscription.get_doc_before_save() \
			and getdate(self.subscription.get_doc_before_save().trial_period_end) != getdate(self.subscription.trial_period_end):
			return max(getdate(self.subscription.start), add_days(getdate(self.subscription.trial_period_end), 1)) if self.subscription.trial_period_end else self.subscription.start
		elif getdate(self.subscription.current_invoice_end) < getdate(nowdate()):
			return self.get_next_period_start()
		else:
			return max(getdate(self.subscription.current_invoice_start), add_days(getdate(self.subscription.trial_period_end), 1)) if self.subscription.trial_period_end else self.subscription.current_invoice_start

	def get_current_invoice_end(self):
		if SubscriptionStateManager(self.subscription).is_trial():
			return None
		elif self.subscription.cancellation_date:
			return self.subscription.cancellation_date
		elif self.subscription.is_new():
			return self.get_next_period_end()
		elif self.subscription.get_doc_before_save() \
			and self.subscription.get_doc_before_save().current_invoice_start != self.subscription.current_invoice_start:
			return self.get_next_period_end()
		elif getdate(self.subscription.current_invoice_end) < getdate(self.subscription.current_invoice_start):
			return self.get_next_period_end()
		else:
			return self.subscription.current_invoice_end

	def get_next_period_start(self):
		if not self.subscription.current_invoice_start:
			return max(getdate(self.subscription.start), add_days(getdate(self.subscription.trial_period_end), 1))

		if getdate(self.subscription.current_invoice_end) < getdate(nowdate()):
			return add_days(self.get_next_period_end(), 1)

	def get_next_period_end(self):
		if self.get_billing_cycle_data():
			return add_to_date(self.subscription.current_invoice_start, **self.get_billing_cycle_data())
		else:
			return get_last_day(self.subscription.current_invoice_start)

	def get_billing_cycle_data(self):
		data = {}
		interval = self.subscription.billing_interval
		interval_count = self.subscription.billing_interval_count
		if interval not in ['Day', 'Week']:
			data['days'] = -1
		if interval == 'Day':
			data['days'] = interval_count - 1
		elif interval == 'Month':
			data['months'] = interval_count
		elif interval == 'Year':
			data['years'] = interval_count
		elif interval == 'Week':
			data['days'] = interval_count * 7 - 1

		return data

	def get_current_documents(self, doctype):
		events = [x.document_name for x in frappe.get_all("Subscription Event",
			filters={"subscription": self.subscription.name, "document_type": doctype,
				"period_start": self.start, "period_end": self.end,
				"event_type": f"{doctype.capitalize()} created"},
			fields=["document_name"])]

		transaction_date = "posting_date" if doctype == "Sales Invoice" else "transaction_date"
		fields = ["name", "docstatus"]
		if doctype == "Sales Invoice":
			fields.append("outstanding_amount")

		documents = frappe.get_all(doctype,
			filters={
				"subscription": self.subscription.name,
				"docstatus": ["!=", 2]
			},
			or_filters={
				transaction_date: ["between", [self.start, self.end]],
				"name": ["in", events]
			},
			fields=fields)

		return documents

	def get_previous_period(self):
		if self.start:
			return frappe.get_all("Subscription Event",
				filters={"subscription": self.subscription.name,
					"period_end": getdate(add_days(self.start, -1)),
					"event_type": "New period"},
				fields=["period_start", "period_end"])
		else:
			return frappe.get_all("Subscription Event",
				filters={"subscription": self.subscription.name,
					"period_end": ["<=", getdate(self.subscription.cancellation_date)],
					"event_type": "New period"},
				fields=["period_start", "period_end"], order_by="period_end DESC")

	def get_next_invoice_date(self):
		if self.subscription.current_invoice_start:
			if self.get_current_documents("Sales Invoice"):
				return add_days(self.subscription.current_invoice_end, 1)
			else:
				return self.subscription.current_invoice_start
		elif self.subscription.generate_invoice_at_period_start and self.subscription.trial_period_end and getdate(self.subscription.trial_period_end) >= getdate(nowdate()):
				return add_days(self.subscription.trial_period_end, 1)
		elif not(self.subscription.generate_invoice_at_period_start) and self.subscription.trial_period_end and getdate(self.subscription.trial_period_end) >= getdate(nowdate()):
			return add_to_date(add_days(self.subscription.trial_period_end, 1), **self.get_billing_cycle_data())
		elif not(self.subscription.generate_invoice_at_period_start):
			previous_period = self.get_previous_period()
			if previous_period:
				self.start = previous_period[0].period_start
				self.end = previous_period[0].period_end
			if self.get_current_documents("Sales Invoice"):
				return add_to_date(add_days(self.subscription.current_invoice_end, 1), **self.get_billing_cycle_data())
			else:
				return add_days(self.subscription.current_invoice_end, 1)

class SubscriptionStateManager:
	def __init__(self, subscription=None):
		self.subscription = subscription

	def set_status(self):
		status = 'Active'
		if self.subscription.status == 'Billing failed' and \
			self.subscription.get_doc_before_save() and self.subscription.get_doc_before_save().status != 'Billing failed':
			status = 'Billing failed'
		elif self.is_cancelled() and self.is_billable():
			status = 'Cancelled and billable'
		elif self.is_cancelled():
			status = 'Cancelled'
		elif not self.is_cancelled() and self.is_trial():
			status = 'Trial'
		elif not self.is_cancelled() and not self.is_trial():
			if self.is_billable():
				status = 'Billable'
			elif self.is_payable():
				status = 'Payable'
			elif self.is_draft():
				status = 'Draft invoices'
			elif flt(self.subscription.outstanding_amount) > 0:
				status = 'Unpaid'
			elif self.is_paid():
				status = 'Paid'

		if status != self.subscription.status:
			previous_status = self.subscription.status
			self.subscription.db_set("status", status)
			self.subscription.reload()
			self.subscription.add_subscription_event("Status updated", **{
				"previous_status": previous_status,
				"new_status": status
			})

	def is_trial(self):
		return getdate(self.subscription.trial_period_end) >= getdate(nowdate()) if self.subscription.trial_period_start else False

	def is_cancelled(self):
		return getdate(self.subscription.cancellation_date) <= getdate(nowdate()) if self.subscription.cancellation_date else False

	def is_billable(self):
		if self.subscription.generate_invoice_at_period_start and getdate(nowdate()) >= getdate(self.subscription.current_invoice_start):
			return not(SubscriptionPeriod(self.subscription).get_current_documents("Sales Invoice"))
		else:
			previous_period = SubscriptionPeriod(self.subscription).get_previous_period()
			return not(SubscriptionPeriod(self.subscription,
				start=previous_period[0].period_start,
				end=previous_period[0].period_end
			).get_current_documents("Sales Invoice")) if previous_period else False

	def is_draft(self):
		current_sales_invoices = []
		if self.subscription.generate_invoice_at_period_start:
			current_sales_invoices = SubscriptionPeriod(self.subscription).get_current_documents("Sales Invoice")
		else:
			previous_period = SubscriptionPeriod(self.subscription).get_previous_period()
			if previous_period:
				current_sales_invoices = SubscriptionPeriod(self.subscription,
					start=previous_period[0].period_start,
					end=previous_period[0].period_end
				).get_current_documents("Sales Invoice")
		return bool([x for x in current_sales_invoices if x.docstatus == 0])

	def is_payable(self):
		if self.is_cancelled():
			return False

		if self.subscription.generate_invoice_at_period_start and getdate(nowdate()) >= getdate(self.subscription.current_invoice_start):
			current_sales_invoices = SubscriptionPeriod(self.subscription).get_current_documents("Sales Invoice")
			current_payment_requests = frappe.get_all("Subscription Event",
				filters={
					"event_type": "Payment request created",
					"period_start": self.subscription.current_invoice_start ,
					"period_end": self.subscription.current_invoice_end,
					"subscription": self.subscription.name
				}
			)
		else:
			previous_period = SubscriptionPeriod(self.subscription).get_previous_period()
			if previous_period:
				current_sales_invoices = SubscriptionPeriod(self.subscription,
					start=previous_period[0].period_start,
					end=previous_period[0].period_end
				).get_current_documents("Sales Invoice")
				current_payment_requests = frappe.get_all("Subscription Event",
					filters={
						"event_type": "Payment request created",
						"period_start": previous_period[0].period_start,
						"period_end": previous_period[0].period_end,
						"subscription": self.subscription.name
					}
				)
			else:
				current_sales_invoices = current_payment_requests = []

		if current_sales_invoices and sum([flt(x.outstanding_amount) for x in current_sales_invoices]) > 0.0 and not current_payment_requests:
			return True

		return False

	def is_paid(self):
		if SubscriptionPeriod(self.subscription).get_current_documents("Sales Invoice"):
			return True