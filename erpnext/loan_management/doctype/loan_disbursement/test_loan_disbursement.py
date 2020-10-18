# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals
import frappe
import unittest
from frappe.utils import (nowdate, add_days, get_datetime, get_first_day, get_last_day, date_diff, flt, add_to_date)
from erpnext.loan_management.doctype.loan.test_loan import (create_loan_type, create_loan_security_pledge, create_repayment_entry, create_loan_application,
	make_loan_disbursement_entry, create_loan_accounts, create_loan_security_type, create_loan_security, create_demand_loan, create_loan_security_price)
from erpnext.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual import process_loan_interest_accrual_for_demand_loans
from erpnext.loan_management.doctype.loan_interest_accrual.loan_interest_accrual import days_in_year
from erpnext.selling.doctype.customer.test_customer import get_customer_dict
from erpnext.loan_management.doctype.loan_application.loan_application import create_pledge

class TestLoanDisbursement(unittest.TestCase):

	def setUp(self):
		create_loan_accounts()

		create_loan_type("Demand Loan", 2000000, 13.5, 25, 0, 5, 'Cash', 'Payment Account - _TC', 'Loan Account - _TC',
			'Interest Income Account - _TC', 'Penalty Income Account - _TC')

		create_loan_security_type()
		create_loan_security()

		create_loan_security_price("Test Security 1", 500, "Nos", get_datetime() , get_datetime(add_to_date(nowdate(), hours=24)))
		create_loan_security_price("Test Security 2", 250, "Nos", get_datetime() , get_datetime(add_to_date(nowdate(), hours=24)))

		if not frappe.db.exists("Customer", "_Test Loan Customer"):
			frappe.get_doc(get_customer_dict('_Test Loan Customer')).insert(ignore_permissions=True)

		self.applicant = frappe.db.get_value("Customer", {'name': '_Test Loan Customer'}, 'name')

	def test_loan_topup(self):
		pledge = [{
			"loan_security": "Test Security 1",
			"qty": 4000.00
		}]

		loan_application = create_loan_application('_Test Company', self.applicant, 'Demand Loan', pledge)
		create_pledge(loan_application)

		loan = create_demand_loan(self.applicant, "Demand Loan", loan_application, posting_date=get_first_day(nowdate()))

		loan.submit()

		first_date = get_first_day(nowdate())
		last_date = get_last_day(nowdate())

		no_of_days = date_diff(last_date, first_date) + 1

		accrued_interest_amount = (loan.loan_amount * loan.rate_of_interest * no_of_days) \
			/ (days_in_year(get_datetime().year) * 100)

		make_loan_disbursement_entry(loan.name, loan.loan_amount, disbursement_date=first_date)

		process_loan_interest_accrual_for_demand_loans(posting_date=add_days(last_date, 1))

		# Should not be able to create loan disbursement entry before repayment
		self.assertRaises(frappe.ValidationError, make_loan_disbursement_entry, loan.name,
			500000, first_date)

		repayment_entry = create_repayment_entry(loan.name, self.applicant, add_days(get_last_day(nowdate()), 5),
			"Regular Payment", 611095.89)

		repayment_entry.submit()
		loan.reload()

		# After repayment loan disbursement entry should go through
		make_loan_disbursement_entry(loan.name, 500000, disbursement_date=add_days(last_date, 16))
