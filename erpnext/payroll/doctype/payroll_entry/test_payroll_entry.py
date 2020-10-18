# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import unittest
import erpnext
import frappe
from dateutil.relativedelta import relativedelta
from erpnext.accounts.utils import get_fiscal_year, getdate, nowdate
from frappe.utils import add_months
from erpnext.payroll.doctype.payroll_entry.payroll_entry import get_start_end_dates, get_end_date
from erpnext.hr.doctype.employee.test_employee import make_employee
from erpnext.payroll.doctype.salary_slip.test_salary_slip import get_salary_component_account, \
		make_earning_salary_component, make_deduction_salary_component, create_account
from erpnext.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from erpnext.loan_management.doctype.loan.test_loan import create_loan, make_loan_disbursement_entry
from erpnext.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual import process_loan_interest_accrual_for_term_loans

class TestPayrollEntry(unittest.TestCase):
	def setUp(self):
		for dt in ["Salary Slip", "Salary Component", "Salary Component Account",
			"Payroll Entry", "Salary Structure", "Salary Structure Assignment", "Payroll Employee Detail", "Additional Salary"]:
				frappe.db.sql("delete from `tab%s`" % dt)

		make_earning_salary_component(setup=True, company_list=["_Test Company"])
		make_deduction_salary_component(setup=True, company_list=["_Test Company"])

		frappe.db.set_value("Payroll Settings", None, "email_salary_slip_to_employee", 0)

	def test_payroll_entry(self): # pylint: disable=no-self-use
		company = erpnext.get_default_company()
		for data in frappe.get_all('Salary Component', fields = ["name"]):
			if not frappe.db.get_value('Salary Component Account',
				{'parent': data.name, 'company': company}, 'name'):
				get_salary_component_account(data.name)

		employee = frappe.db.get_value("Employee", {'company': company})
		make_salary_structure("_Test Salary Structure", "Monthly", employee, company=company)
		dates = get_start_end_dates('Monthly', nowdate())
		if not frappe.db.get_value("Salary Slip", {"start_date": dates.start_date, "end_date": dates.end_date}):
			make_payroll_entry(start_date=dates.start_date, end_date=dates.end_date)

	def test_payroll_entry_with_employee_cost_center(self): # pylint: disable=no-self-use
		for data in frappe.get_all('Salary Component', fields = ["name"]):
			if not frappe.db.get_value('Salary Component Account',
				{'parent': data.name, 'company': "_Test Company"}, 'name'):
				get_salary_component_account(data.name)

		if not frappe.db.exists('Department', "cc - _TC"):
			frappe.get_doc({
				'doctype': 'Department',
				'department_name': "cc",
				"company": "_Test Company"
			}).insert()

		employee1 = make_employee("test_employee1@example.com", payroll_cost_center="_Test Cost Center - _TC",
			department="cc - _TC", company="_Test Company")
		employee2 = make_employee("test_employee2@example.com", payroll_cost_center="_Test Cost Center 2 - _TC",
			department="cc - _TC", company="_Test Company")

		make_salary_structure("_Test Salary Structure 1", "Monthly", employee1, company="_Test Company")
		make_salary_structure("_Test Salary Structure 2", "Monthly", employee2, company="_Test Company")

		if not frappe.db.exists("Account", "_Test Payroll Payable - _TC"):
			create_account(account_name="_Test Payroll Payable",
				company="_Test Company", parent_account="Current Liabilities - _TC")
			frappe.db.set_value("Company", "_Test Company", "default_payroll_payable_account",
				"_Test Payroll Payable - _TC")

		dates = get_start_end_dates('Monthly', nowdate())
		if not frappe.db.get_value("Salary Slip", {"start_date": dates.start_date, "end_date": dates.end_date}):
			pe = make_payroll_entry(start_date=dates.start_date, end_date=dates.end_date,
				department="cc - _TC", company="_Test Company", payment_account="Cash - _TC", cost_center="Main - _TC")
			je = frappe.db.get_value("Salary Slip", {"payroll_entry": pe.name}, "journal_entry")
			je_entries = frappe.db.sql("""
				select account, cost_center, debit, credit
				from `tabJournal Entry Account`
				where parent=%s
				order by account, cost_center
			""", je)
			expected_je = (
				('_Test Payroll Payable - _TC', 'Main - _TC', 0.0, 155600.0),
				('Salary - _TC', '_Test Cost Center - _TC', 78000.0, 0.0),
				('Salary - _TC', '_Test Cost Center 2 - _TC', 78000.0, 0.0),
				('Salary Deductions - _TC', '_Test Cost Center - _TC', 0.0, 200.0),
				('Salary Deductions - _TC', '_Test Cost Center 2 - _TC', 0.0, 200.0)
			)

			self.assertEqual(je_entries, expected_je)

	def test_get_end_date(self):
		self.assertEqual(get_end_date('2017-01-01', 'monthly'), {'end_date': '2017-01-31'})
		self.assertEqual(get_end_date('2017-02-01', 'monthly'), {'end_date': '2017-02-28'})
		self.assertEqual(get_end_date('2017-02-01', 'fortnightly'), {'end_date': '2017-02-14'})
		self.assertEqual(get_end_date('2017-02-01', 'bimonthly'), {'end_date': ''})
		self.assertEqual(get_end_date('2017-01-01', 'bimonthly'), {'end_date': ''})
		self.assertEqual(get_end_date('2020-02-15', 'bimonthly'), {'end_date': ''})
		self.assertEqual(get_end_date('2017-02-15', 'monthly'), {'end_date': '2017-03-14'})
		self.assertEqual(get_end_date('2017-02-15', 'daily'), {'end_date': '2017-02-15'})

	def test_loan(self):
		branch = "Test Employee Branch"
		applicant = make_employee("test_employee@loan.com", company="_Test Company")
		company = "_Test Company"
		holiday_list = make_holiday("test holiday for loan")

		company_doc = frappe.get_doc('Company', company)
		if not company_doc.default_payroll_payable_account:
			company_doc.default_payroll_payable_account = frappe.db.get_value('Account',
				{'company': company, 'root_type': 'Liability', 'account_type': ''}, 'name')
			company_doc.save()

		if not frappe.db.exists('Branch', branch):
			frappe.get_doc({
				'doctype': 'Branch',
				'branch': branch
			}).insert()

		employee_doc = frappe.get_doc('Employee', applicant)
		employee_doc.branch = branch
		employee_doc.holiday_list = holiday_list
		employee_doc.save()

		salary_structure = "Test Salary Structure for Loan"
		make_salary_structure(salary_structure, "Monthly", employee=employee_doc.name, company="_Test Company")

		loan = create_loan(applicant, "Car Loan", 280000, "Repay Over Number of Periods", 20, posting_date=add_months(nowdate(), -1))
		loan.repay_from_salary = 1
		loan.submit()

		make_loan_disbursement_entry(loan.name, loan.loan_amount, disbursement_date=add_months(nowdate(), -1))

		process_loan_interest_accrual_for_term_loans(posting_date=nowdate())


		dates = get_start_end_dates('Monthly', nowdate())
		make_payroll_entry(company="_Test Company", start_date=dates.start_date,
			end_date=dates.end_date, branch=branch, cost_center="Main - _TC", payment_account="Cash - _TC")

		name = frappe.db.get_value('Salary Slip',
			{'posting_date': nowdate(), 'employee': applicant}, 'name')

		salary_slip = frappe.get_doc('Salary Slip', name)
		for row in salary_slip.loans:
			if row.loan == loan.name:
				interest_amount = (280000 * 8.4)/(12*100)
				principal_amount = loan.monthly_repayment_amount - interest_amount
				self.assertEqual(row.interest_amount, interest_amount)
				self.assertEqual(row.principal_amount, principal_amount)
				self.assertEqual(row.total_payment,
					interest_amount + principal_amount)

		if salary_slip.docstatus == 0:
			frappe.delete_doc('Salary Slip', name)


def make_payroll_entry(**args):
	args = frappe._dict(args)

	payroll_entry = frappe.new_doc("Payroll Entry")
	payroll_entry.company = args.company or erpnext.get_default_company()
	payroll_entry.start_date = args.start_date or "2016-11-01"
	payroll_entry.end_date = args.end_date or "2016-11-30"
	payroll_entry.payment_account = get_payment_account()
	payroll_entry.posting_date = nowdate()
	payroll_entry.payroll_frequency = "Monthly"
	payroll_entry.branch = args.branch or None
	payroll_entry.department = args.department or None

	if args.cost_center:
		payroll_entry.cost_center = args.cost_center

	if args.payment_account:
		payroll_entry.payment_account = args.payment_account

	payroll_entry.fill_employee_details()
	payroll_entry.save()
	payroll_entry.create_salary_slips()
	payroll_entry.submit_salary_slips()
	if payroll_entry.get_sal_slip_list(ss_status = 1):
		payroll_entry.make_payment_entry()

	return payroll_entry

def get_payment_account():
	return frappe.get_value('Account',
		{'account_type': 'Cash', 'company': erpnext.get_default_company(),'is_group':0}, "name")

def make_holiday(holiday_list_name):
	if not frappe.db.exists('Holiday List', holiday_list_name):
		current_fiscal_year = get_fiscal_year(nowdate(), as_dict=True)
		dt = getdate(nowdate())

		new_year = dt + relativedelta(month=1, day=1, year=dt.year)
		republic_day = dt + relativedelta(month=1, day=26, year=dt.year)
		test_holiday = dt + relativedelta(month=2, day=2, year=dt.year)

		frappe.get_doc({
			'doctype': 'Holiday List',
			'from_date': current_fiscal_year.year_start_date,
			'to_date': current_fiscal_year.year_end_date,
			'holiday_list_name': holiday_list_name,
			'holidays': [{
				'holiday_date': new_year,
				'description': 'New Year'
			}, {
				'holiday_date': republic_day,
				'description': 'Republic Day'
			}, {
				'holiday_date': test_holiday,
				'description': 'Test Holiday'
			}]
		}).insert()

	return holiday_list_name
