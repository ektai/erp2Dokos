frappe.ui.form.on("Leave Type", {
	refresh: function(frm) {
		frm.set_df_property("earned_leave_frequency", "options", ["Monthly", "Quarterly", "Half-Yearly", "Yearly"]);
	}
});


frappe.tour['Leave Type'] = [
	{
		fieldname: "max_leaves_allowed",
		title: __("Max Leaves Allowed"),
		description: __("Maximum number of leaves allowed for this type of leaves.")
	},
	{
		fieldname: "applicable_after",
		title: __("Applicable After (Working Days)"),
		description: __("This type of leaves is applicable only after x working days from the date of joining the company.")
	},
	{
		fieldname: "max_continuous_days_allowed",
		title: __("Maximum Continuous Days Applicable"),
		description: __("Maximum number of consecutive leave days an employee can apply for.")
	},
	{
		fieldname: "is_carry_forward",
		title: __("Is Carry Forward"),
		description: __("If checked, the balance leaves of this Leave Type will be carried forward to the next allocation period.")
	},
	{
		fieldname: "is_lwp",
		title: __("Is Leave Without Pay"),
		description: __("The salary will be deducted for this leave type.")
	},
	{
		fieldname: "is_optional_leave",
		title: __("Is Optional Leave"),
		description: __("Optional Leaves are holidays that Employees can choose to avail from a list of holidays published by the company. The Holiday List for Optional Leaves can have any number of holidays, but you can restrict the number of such leaves by setting the Max Days Leave Allowed field.")
	},
	{
		fieldname: "allow_negative",
		title: __("Allow Negative Balance"),
		description: __("If checked, employees will be allowed to apply for this leave type even if they don't have a sufficient balance. This will result in a negative balance for this type of leaves.")
	},
	{
		fieldname: "include_holiday",
		title: __("Include holidays within leaves as leaves"),
		description: __("Check this option if you wish to count holidays within leaves as a ‘leave’. For example, if an Employee has applied for leave on Friday and Monday, and Saturday and Sunday are weekly offs, if this option is checked, the system will consider Saturday as Sunday as leaves too. Such holidays will be deducted from the total number of leaves.")
	},
	{
		fieldname: "exclude_from_leave_acquisition",
		title: __("Exclude from leave acquisition"),
		description: __("If checked, all leave days taken with this leave type will be considered as absent when calculating the attendance for acquired leaves calculation.")
	},
	{
		fieldname: "is_compensatory",
		title: __("Compensatory leave"),
		description: __("Compensatory leaves are leaves granted for working overtime or on holidays, normally compensated as an encashable leave. You can check this option to mark the Leave Type as compensatory. An Employee can request for compensatory leaves using Compensatory Leave Request.")
	},
	{
		fieldname: "maximum_carry_forwarded_leaves",
		title: __("Maximum Carry Forwarded Leaves"),
		description: __("Maximum number of carry forwarded leaves allowed.")
	},
	{
		fieldname: "expire_carry_forwarded_leaves_after_days",
		title: __("Expire Carry Forwarded Leaves (Days)"),
		description: __("Number of days after which a carry forwarded leave is condidered as expired.")
	},
	{
		fieldname: "is_earned_leave",
		title: __("Earned Leave"),
		description: __("Check this option if this type of leaves is earned based on a working period.")
	},
	{
		fieldname: "earned_leave_frequency",
		title: __("Earned Leave Frequency"),
		description: __("Frequency of leave earnings.")
	},
	{
		fieldname: "earned_leave_frequency_formula",
		title: __("Earned Leave Frequency Formula"),
		description: __("Pre-configured formula for certain types of leaves. Usually country dependent.")
	},
	{
		fieldname: "rounding",
		title: __("Rounding"),
		description: __("Calculated earned leaves will be rounded to the nearest value based on this option if the result is a fraction.")
	},
	{
		fieldname: "allow_encashment",
		title: __("Encashment"),
		description: __("Check this option to allow encashment for this type of leaves.")
	},
	{
		fieldname: "encashment_threshold_days",
		title: __("Encashment Threshold Days"),
		description: __("Number of days that cannot be encashed for this leave type. Every leaves above this threshold will be available for encashment.")
	},
	{
		fieldname: "earning_component",
		title: __("Earning Component"),
		description: __("Salary component to use for encashment.")
	}
]