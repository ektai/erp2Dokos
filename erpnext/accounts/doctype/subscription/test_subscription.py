# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import unittest

import frappe
from frappe.utils import add_days, nowdate, getdate, date_diff, add_months, today

PLANS = [
	{
		"item": "_Test Non Stock Item",
		"qty": 1,
		"uom": "Unit",
		"fixed_rate": 150,
		"description": "Test Item"
	}
]

class TestSubscription(unittest.TestCase):
	def test_period_update_with_trial(self):
		current_date = today()
		subscription = frappe.new_doc('Subscription')
		subscription.customer = '_Test Customer'
		subscription.company = '_Test Company'
		subscription.start = nowdate()
		subscription.billing_interval = "Day"
		subscription.trial_period_start = nowdate()
		subscription.trial_period_end = add_days(current_date, 5)
		subscription.append('plans', PLANS[0])
		subscription.save()

		for i in range(1, 10):
			frappe.flags.current_date = add_days(nowdate(), 1)
			subscription.save()
			self.assertEqual(subscription.trial_period_start, getdate(current_date))
			self.assertEqual(subscription.trial_period_end, getdate(add_days(current_date, 5)))
			if i in range(1, 6):
				self.assertEqual(subscription.current_invoice_start, None)
				self.assertEqual(subscription.current_invoice_end, None)
				self.assertEqual(subscription.status, 'Trial')
			else:
				self.assertEqual(subscription.current_invoice_start, getdate(add_days(current_date, i)))
				self.assertEqual(subscription.current_invoice_end, getdate(add_days(current_date, i)))
				self.assertEqual(subscription.status, 'Billable')

		subscription.billing_interval = "Month"
		frappe.flags.current_date = current_date
		two_months = date_diff(add_months(getdate(current_date), 2), current_date)
		one_month = date_diff(add_months(getdate(current_date), 1), current_date)

		for i in range(1, two_months):
			frappe.flags.current_date = add_days(nowdate(), 1)
			subscription.save()
			self.assertEqual(subscription.trial_period_start, getdate(current_date))
			self.assertEqual(subscription.trial_period_end, getdate(add_days(current_date, 5)))
			if i in range(1, 6):
				self.assertEqual(subscription.current_invoice_start, None)
				self.assertEqual(subscription.current_invoice_end, None)
				self.assertEqual(subscription.status, 'Trial')
			elif i in range(6, one_month + 6):
				self.assertEqual(subscription.current_invoice_start, getdate(add_days(current_date, 6)))
				self.assertEqual(subscription.current_invoice_end, getdate(add_days(current_date, one_month + 5)))
				self.assertEqual(subscription.status, 'Billable')
			else:
				self.assertEqual(subscription.current_invoice_start, getdate(add_days(current_date, one_month + 6)))
				self.assertEqual(subscription.current_invoice_end, getdate(add_days(current_date, two_months + 5)))
				self.assertEqual(subscription.status, 'Billable')

		subscription.delete()

	def test_period_update_without_trial(self):
		current_date = today()
		subscription = frappe.new_doc('Subscription')
		subscription.customer = '_Test Customer'
		subscription.company = '_Test Company'
		subscription.start = today()
		subscription.billing_interval = "Day"
		subscription.append('plans', PLANS[0])
		subscription.save()

		for i in range(1, 10):
			frappe.flags.current_date = add_days(nowdate(), 1)
			subscription.save()
			self.assertEqual(subscription.current_invoice_start, getdate(add_days(current_date, i)))
			self.assertEqual(subscription.current_invoice_end, getdate(add_days(current_date, i)))
			self.assertEqual(subscription.status, 'Billable')

		subscription.billing_interval = "Month"
		two_months = date_diff(add_months(getdate(current_date), 2), current_date)
		one_month = date_diff(add_months(getdate(current_date), 1), current_date)

		for i in range(1, two_months):
			frappe.flags.current_date = add_days(nowdate(), 1)
			subscription.save()
			if i in range(1, one_month + 1):
				self.assertEqual(subscription.current_invoice_start, add_days(getdate(current_date), 10))
				self.assertEqual(subscription.current_invoice_end, getdate(add_days(current_date, one_month + 9)))
				self.assertEqual(subscription.status, 'Billable')
			else:
				self.assertEqual(subscription.current_invoice_start, getdate(add_days(current_date, one_month + 10)))
				self.assertEqual(subscription.current_invoice_end, getdate(add_days(current_date, two_months + 9)))
				self.assertEqual(subscription.status, 'Billable')

		subscription.delete()

	def test_invoice_generation(self):
		current_date = today()
		subscription = frappe.new_doc('Subscription')
		subscription.customer = '_Test Customer'
		subscription.company = '_Test Company'
		subscription.start = today()
		subscription.billing_interval = "Day"
		subscription.append('plans', PLANS[0])
		subscription.save()

		for i in range(1, 5):
			frappe.flags.current_date = add_days(nowdate(), 1)
			subscription.save()

			invoices = frappe.get_all("Sales Invoice", filters={
				"subscription": subscription.name,
				"from_date": subscription.current_invoice_start,
				"to_date": subscription.current_invoice_end
			})
			events = frappe.get_all("Subscription Event", filters={
				"period_start": subscription.current_invoice_start,
				"period_end": subscription.current_invoice_end,
				"event_type": "Sales invoice created"
			})
			self.assertEqual(len(invoices), 1)
			self.assertEqual(len(events), 1)


		subscription.delete()