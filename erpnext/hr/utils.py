# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
from frappe.utils import formatdate, format_datetime, getdate, get_datetime, nowdate, flt, cstr, add_days, today
from frappe.model.document import Document
from frappe.desk.form import assign_to
from erpnext.hr.doctype.employee.employee import get_holiday_list_for_employee

class DuplicateDeclarationError(frappe.ValidationError): pass

class EmployeeBoardingController(Document):
	'''
		Create the project and the task for the boarding process
		Assign to the concerned person and roles as per the onboarding/separation template
	'''
	def validate(self):
		# remove the task if linked before submitting the form
		if self.amended_from:
			for activity in self.activities:
				activity.task = ''

	def on_submit(self):
		# create the project for the given employee onboarding
		project_name = _(self.doctype) + " : "
		if self.doctype == "Employee Onboarding":
			project_name += self.job_applicant
		else:
			project_name += self.employee
		project = frappe.get_doc({
				"doctype": "Project",
				"project_name": project_name,
				"expected_start_date": self.date_of_joining if self.doctype == "Employee Onboarding" else self.resignation_letter_date,
				"department": self.department,
				"company": self.company
			}).insert(ignore_permissions=True)
		self.db_set("project", project.name)
		self.db_set("boarding_status", "Pending")
		self.reload()
		self.create_task_and_notify_user()

	def create_task_and_notify_user(self):
		# create the task for the given project and assign to the concerned person
		for activity in self.activities:
			if activity.task:
				continue

			task = frappe.get_doc({
					"doctype": "Task",
					"project": self.project,
					"subject": activity.activity_name + " : " + self.employee_name,
					"description": activity.description,
					"department": self.department,
					"company": self.company,
					"task_weight": activity.task_weight
				}).insert(ignore_permissions=True)
			activity.db_set("task", task.name)
			users = [activity.user] if activity.user else []
			if activity.role:
				user_list = frappe.db.sql_list('''select distinct(parent) from `tabHas Role`
					where parenttype='User' and role=%s''', activity.role)
				users = users + user_list

				if "Administrator" in users:
					users.remove("Administrator")

			# assign the task the users
			if users:
				self.assign_task_to_users(task, set(users))

	def assign_task_to_users(self, task, users):
		for user in users:
			args = {
				'assign_to': [user],
				'doctype': task.doctype,
				'name': task.name,
				'description': task.description or task.subject,
				'notify': self.notify_users_by_email
			}
			assign_to.add(args)

	def on_cancel(self):
		# delete task project
		for task in frappe.get_all("Task", filters={"project": self.project}):
			frappe.delete_doc("Task", task.name, force=1)
		frappe.delete_doc("Project", self.project, force=1)
		self.db_set('project', '')
		for activity in self.activities:
			activity.db_set("task", "")


@frappe.whitelist()
def get_onboarding_details(parent, parenttype):
	return frappe.get_all("Employee Boarding Activity",
		fields=["activity_name", "role", "user", "required_for_employee_creation", "description", "task_weight"],
		filters={"parent": parent, "parenttype": parenttype},
		order_by= "idx")

@frappe.whitelist()
def get_boarding_status(project):
	status = 'Pending'
	if project:
		doc = frappe.get_doc('Project', project)
		if flt(doc.percent_complete) > 0.0 and flt(doc.percent_complete) < 100.0:
			status = 'In Process'
		elif flt(doc.percent_complete) == 100.0:
			status = 'Completed'
		return status

def set_employee_name(doc):
	if doc.employee and not doc.employee_name:
		doc.employee_name = frappe.db.get_value("Employee", doc.employee, "employee_name")

def update_employee(employee, details, date=None, cancel=False):
	internal_work_history = {}
	for item in details:
		fieldtype = frappe.get_meta("Employee").get_field(item.fieldname).fieldtype
		new_data = item.new if not cancel else item.current
		if fieldtype == "Date" and new_data:
			new_data = getdate(new_data)
		elif fieldtype =="Datetime" and new_data:
			new_data = get_datetime(new_data)
		setattr(employee, item.fieldname, new_data)
		if item.fieldname in ["department", "designation", "branch"]:
			internal_work_history[item.fieldname] = item.new
	if internal_work_history and not cancel:
		internal_work_history["from_date"] = date
		employee.append("internal_work_history", internal_work_history)
	return employee

@frappe.whitelist()
def get_employee_fields_label():
	fields = []
	for df in frappe.get_meta("Employee").get("fields"):
		if df.fieldname in ["salutation", "user_id", "employee_number", "employment_type",
			"holiday_list", "branch", "department", "designation", "grade",
			"notice_number_of_days", "reports_to", "leave_policy", "company_email"]:
				fields.append({"value": df.fieldname, "label": df.label})
	return fields

@frappe.whitelist()
def get_employee_field_property(employee, fieldname):
	if employee and fieldname:
		field = frappe.get_meta("Employee").get_field(fieldname)
		value = frappe.db.get_value("Employee", employee, fieldname)
		options = field.options
		if field.fieldtype == "Date":
			value = formatdate(value)
		elif field.fieldtype == "Datetime":
			value = format_datetime(value)
		return {
			"value" : value,
			"datatype" : field.fieldtype,
			"label" : field.label,
			"options" : options
		}
	else:
		return False

def validate_dates(doc, from_date, to_date):
	date_of_joining, relieving_date = frappe.db.get_value("Employee", doc.employee, ["date_of_joining", "relieving_date"])
	if getdate(from_date) > getdate(to_date):
		frappe.throw(_("To date can not be less than from date"))
	elif getdate(from_date) > getdate(nowdate()):
		frappe.throw(_("Future dates not allowed"))
	elif date_of_joining and getdate(from_date) < getdate(date_of_joining):
		frappe.throw(_("From date can not be less than employee's joining date"))
	elif relieving_date and getdate(to_date) > getdate(relieving_date):
		frappe.throw(_("To date can not greater than employee's relieving date"))

def validate_overlap(doc, from_date, to_date, company = None):
	query = """
		select name
		from `tab{0}`
		where name != %(name)s
		"""
	query += get_doc_condition(doc.doctype)

	if not doc.name:
		# hack! if name is null, it could cause problems with !=
		doc.name = "New "+doc.doctype

	overlap_doc = frappe.db.sql(query.format(doc.doctype),{
			"employee": doc.get("employee"),
			"from_date": from_date,
			"to_date": to_date,
			"name": doc.name,
			"company": company
		}, as_dict = 1)

	if overlap_doc:
		if doc.get("employee"):
			exists_for = doc.employee
		if company:
			exists_for = company
		throw_overlap_error(doc, exists_for, overlap_doc[0].name, from_date, to_date)

def get_doc_condition(doctype):
	if doctype == "Compensatory Leave Request":
		return "and employee = %(employee)s and docstatus < 2 \
		and (work_from_date between %(from_date)s and %(to_date)s \
		or work_end_date between %(from_date)s and %(to_date)s \
		or (work_from_date < %(from_date)s and work_end_date > %(to_date)s))"
	elif doctype == "Leave Period":
		return "and company = %(company)s and (from_date between %(from_date)s and %(to_date)s \
			or to_date between %(from_date)s and %(to_date)s \
			or (from_date < %(from_date)s and to_date > %(to_date)s))"

def throw_overlap_error(doc, exists_for, overlap_doc, from_date, to_date):
	msg = _("A {0} exists between {1} and {2} (").format(_(doc.doctype),
		formatdate(from_date), formatdate(to_date)) \
		+ """ <b><a href="#Form/{0}/{1}">{1}</a></b>""".format(doc.doctype, overlap_doc) \
		+ _(") for {0}").format(exists_for)
	frappe.throw(msg)

def get_employee_leave_policy(employee):
	leave_policy = frappe.db.get_value("Employee", employee, "leave_policy")
	if not leave_policy:
		employee_grade = frappe.db.get_value("Employee", employee, "grade")
		if employee_grade:
			leave_policy = frappe.db.get_value("Employee Grade", employee_grade, "default_leave_policy")
			if not leave_policy:
				frappe.throw(_("Employee {0} of grade {1} have no default leave policy").format(employee, employee_grade))
	if leave_policy:
		return frappe.get_doc("Leave Policy", leave_policy)
	else:
		frappe.throw(_("Please set leave policy for employee {0} in Employee / Grade record").format(employee))

def validate_duplicate_exemption_for_payroll_period(doctype, docname, payroll_period, employee):
	existing_record = frappe.db.exists(doctype, {
		"payroll_period": payroll_period,
		"employee": employee,
		'docstatus': ['<', 2],
		'name': ['!=', docname]
	})
	if existing_record:
		frappe.throw(_("{0} already exists for employee {1} and period {2}")
			.format(doctype, employee, payroll_period), DuplicateDeclarationError)

def validate_tax_declaration(declarations):
	subcategories = []
	for d in declarations:
		if d.exemption_sub_category in subcategories:
			frappe.throw(_("More than one selection for {0} not allowed").format(d.exemption_sub_category))
		subcategories.append(d.exemption_sub_category)

def get_total_exemption_amount(declarations):
	exemptions = frappe._dict()
	for d in declarations:
		exemptions.setdefault(d.exemption_category, frappe._dict())
		category_max_amount = exemptions.get(d.exemption_category).max_amount
		if not category_max_amount:
			category_max_amount = frappe.db.get_value("Employee Tax Exemption Category", d.exemption_category, "max_amount")
			exemptions.get(d.exemption_category).max_amount = category_max_amount
		sub_category_exemption_amount = d.max_amount \
			if (d.max_amount and flt(d.amount) > flt(d.max_amount)) else d.amount

		exemptions.get(d.exemption_category).setdefault("total_exemption_amount", 0.0)
		exemptions.get(d.exemption_category).total_exemption_amount += flt(sub_category_exemption_amount)

		if category_max_amount and exemptions.get(d.exemption_category).total_exemption_amount > category_max_amount:
			exemptions.get(d.exemption_category).total_exemption_amount = category_max_amount

	total_exemption_amount = sum([flt(d.total_exemption_amount) for d in exemptions.values()])
	return total_exemption_amount

def get_leave_period(from_date, to_date, company):
	leave_period = frappe.db.sql("""
		select name, from_date, to_date
		from `tabLeave Period`
		where company=%(company)s and is_active=1
			and (from_date between %(from_date)s and %(to_date)s
				or to_date between %(from_date)s and %(to_date)s
				or (from_date < %(from_date)s and to_date > %(to_date)s))
	""", {
		"from_date": from_date,
		"to_date": to_date,
		"company": company
	}, as_dict=1)

	if leave_period:
		return leave_period

def generate_leave_encashment():
	''' Generates a draft leave encashment on allocation expiry '''
	from erpnext.hr.doctype.leave_encashment.leave_encashment import create_leave_encashment

	if frappe.db.get_single_value('HR Settings', 'auto_leave_encashment'):
		leave_type = frappe.get_all('Leave Type', filters={'allow_encashment': 1}, fields=['name'])
		leave_type=[l['name'] for l in leave_type]

		leave_allocation = frappe.get_all("Leave Allocation", filters={
			'to_date': add_days(today(), -1),
			'leave_type': ('in', leave_type)
		}, fields=['employee', 'leave_period', 'leave_type', 'to_date', 'total_leaves_allocated', 'new_leaves_allocated'])

		create_leave_encashment(leave_allocation=leave_allocation)

@erpnext.allow_regional
def allocate_earned_leaves():
	'''Allocate earned leaves to Employees'''
	EarnedLeaveAllocator(EarnedLeaveCalculator).allocate()

def create_additional_leave_ledger_entry(allocation, leaves, date):
	''' Create leave ledger entry for leave types '''
	allocation.new_leaves_allocated = leaves
	allocation.from_date = date
	allocation.unused_leaves = 0
	allocation.create_leave_ledger_entry()

def get_salary_assignment(employee, date):
	assignment = frappe.db.sql("""
		select * from `tabSalary Structure Assignment`
		where employee=%(employee)s
		and docstatus = 1
		and %(on_date)s >= from_date order by from_date desc limit 1""", {
			'employee': employee,
			'on_date': date,
		}, as_dict=1)
	return assignment[0] if assignment else None

def get_sal_slip_total_benefit_given(employee, payroll_period, component=False):
	total_given_benefit_amount = 0
	query = """
	select sum(sd.amount) as 'total_amount'
	from `tabSalary Slip` ss, `tabSalary Detail` sd
	where ss.employee=%(employee)s
	and ss.docstatus = 1 and ss.name = sd.parent
	and sd.is_flexible_benefit = 1 and sd.parentfield = "earnings"
	and sd.parenttype = "Salary Slip"
	and (ss.start_date between %(start_date)s and %(end_date)s
		or ss.end_date between %(start_date)s and %(end_date)s
		or (ss.start_date < %(start_date)s and ss.end_date > %(end_date)s))
	"""

	if component:
		query += "and sd.salary_component = %(component)s"

	sum_of_given_benefit = frappe.db.sql(query, {
		'employee': employee,
		'start_date': payroll_period.start_date,
		'end_date': payroll_period.end_date,
		'component': component
	}, as_dict=True)

	if sum_of_given_benefit and flt(sum_of_given_benefit[0].total_amount) > 0:
		total_given_benefit_amount = sum_of_given_benefit[0].total_amount
	return total_given_benefit_amount

def get_holidays_for_employee(employee, start_date, end_date):
	holiday_list = get_holiday_list_for_employee(employee)

	def linked_holiday_lists(hl):
		former_hl = hl
		while former_hl is not None:
			former_hl = frappe.db.get_value("Holiday List", hl, "replaces_holiday_list")
			if former_hl:
				hl = former_hl
				yield former_hl

	linked_holiday_lists = list(linked_holiday_lists(holiday_list))
	total_holidays = [holiday_list] + linked_holiday_lists

	holidays = frappe.db.sql_list('''select holiday_date from `tabHoliday`
		where
			parent in %(holiday_list)s
			and holiday_date >= %(start_date)s
			and holiday_date <= %(end_date)s''', {
				"holiday_list": tuple(total_holidays),
				"start_date": start_date,
				"end_date": end_date
			})

	holidays = [cstr(i) for i in holidays]

	return holidays

@erpnext.allow_regional
def calculate_annual_eligible_hra_exemption(doc):
	# Don't delete this method, used for localization
	# Indian HRA Exemption Calculation
	return {}

@erpnext.allow_regional
def calculate_hra_exemption_for_period(doc):
	# Don't delete this method, used for localization
	# Indian HRA Exemption Calculation
	return {}

def get_previous_claimed_amount(employee, payroll_period, non_pro_rata=False, component=False):
	total_claimed_amount = 0
	query = """
	select sum(claimed_amount) as 'total_amount'
	from `tabEmployee Benefit Claim`
	where employee=%(employee)s
	and docstatus = 1
	and (claim_date between %(start_date)s and %(end_date)s)
	"""
	if non_pro_rata:
		query += "and pay_against_benefit_claim = 1"
	if component:
		query += "and earning_component = %(component)s"

	sum_of_claimed_amount = frappe.db.sql(query, {
		'employee': employee,
		'start_date': payroll_period.start_date,
		'end_date': payroll_period.end_date,
		'component': component
	}, as_dict=True)
	if sum_of_claimed_amount and flt(sum_of_claimed_amount[0].total_amount) > 0:
		total_claimed_amount = sum_of_claimed_amount[0].total_amount
	return total_claimed_amount

def check_frequency_hit(from_date, to_date, frequency):
	'''Return True if current date matches frequency'''
	from_dt = get_datetime(from_date)
	to_dt = get_datetime(to_date)
	from dateutil import relativedelta
	rd = relativedelta.relativedelta(to_dt, from_dt)
	months = rd.months
	if frequency == "Quarterly":
		return math.floor(months / 4)
	elif frequency == "Half-Yearly":
		return math.floor(months / 6)
	elif frequency == "Yearly":
		return math.floor(months / 12)
	return False

class EarnedLeaveAllocator():
	def __init__(self, calculator):
		self.calculator = calculator
		self.e_leave_types = frappe.get_all("Leave Type",
			fields=["name", "max_leaves_allowed", "earned_leave_frequency", "rounding", "earned_leave_frequency_formula"],
			filters={'is_earned_leave' : 1})
		self.today = getdate()
		self.divide_by_frequency = {"Yearly": 1, "Half-Yearly": 6, "Quarterly": 4, "Monthly": 12}

	def allocate(self):
		for e_leave_type in self.e_leave_types:
			leave_allocations = frappe.db.sql(f"""select name, employee, leave_type, from_date, to_date from `tabLeave Allocation` where {self.today}
				between from_date and to_date and docstatus=1 and leave_type={frappe.db.escape(e_leave_type.name)}""", as_dict=1)
			for allocation in leave_allocations:
				self.calculator(self, e_leave_type, allocation).calculate_allocation()

class EarnedLeaveCalculator():
	def __init__(self, parent, leave_type, allocation):
		super(EarnedLeaveCalculator, self).__init__()
		self.parent = parent
		self.leave_type = leave_type
		self.allocation = allocation
		self.leave_policy = get_employee_leave_policy(self.allocation.employee)
		self.annual_allocation = []
		self.attendance = {}
		self.earneable_leaves = 0
		self.earned_leaves = 0

		self.formula_map = {}

	def calculate_allocation(self):
		if not self.leave_policy:
			return

		if self.leave_type.earned_leave_frequency != "Custom Formula":
			frequency = check_frequency_hit(self.allocation.from_date, self.parent.today, self.leave_type.earned_leave_frequency)
			if not frequency:
				return

		self.annual_allocation = frappe.db.get_value("Leave Policy Detail", filters={
			'parent': self.leave_policy.name,
			'leave_type': self.leave_type.name
		}, fieldname=['annual_allocation'])

		if self.annual_allocation:
			self.earneable_leaves = flt(self.annual_allocation) / 12
			self.attendance = get_attendance(self.allocation.employee, self.allocation.from_date, min(self.parent.today, self.allocation.to_date))
			if self.leave_type.earned_leave_frequency == "Custom Formula" and self.formula_map.get(self.leave_type.earned_leave_frequency_formula):
				self.formula_map.get(self.leave_type.earned_leave_frequency_formula)()
			else:
				self.earned_leaves = flt(self.annual_allocation) / self.parent.divide_by_frequency[self.leave_type.earned_leave_frequency] * frequency
				if self.leave_type.rounding == "None":
					pass
				elif self.leave_type.rounding == "0.5":
					self.earned_leaves = round(self.earned_leaves * 2) / 2
				else:
					self.earned_leaves = round(self.earned_leaves)

				self.allocate_earned_leaves()

	def allocate_earned_leaves(self):
		allocation = frappe.get_doc('Leave Allocation', self.allocation.name)
		new_allocation = flt(allocation.new_leaves_allocated) + flt(self.earned_leaves)

		if new_allocation > self.leave_type.max_leaves_allowed and self.leave_type.max_leaves_allowed > 0:
			new_allocation = self.leave_type.max_leaves_allowed

		if new_allocation == allocation.total_leaves_allocated:
			return

		allocation_difference = flt(new_allocation) - flt(allocation.total_leaves_allocated)

		allocation.db_set("total_leaves_allocated", new_allocation, update_modified=False)
		create_additional_leave_ledger_entry(allocation, allocation_difference, self.parent.today)

def get_attendance(employee, start_date, end_date):
	holidays = get_holidays_for_employee(employee, start_date, end_date)
	excluded_leave_types = [x.name for x in frappe.get_all("Leave Type", filters={"exclude_from_leave_acquisition": 1})]

	attendance = frappe.get_all("Attendance",
		filters={"docstatus": 1, "employee": employee, "attendance_date": ("between", [start_date, end_date]), "status": ("!=", "Absent")},
		fields=["name", "attendance_date", "status", "leave_type"])
	attendance = [x for x in attendance if not(x.status=="On Leave" and x.leave_type in excluded_leave_types)]

	return {
		"dates": [x.attendance_date for x in attendance if x.attendance_date not in holidays],
		"weeks": len([x.attendance_date for x in attendance]) / 7
	}