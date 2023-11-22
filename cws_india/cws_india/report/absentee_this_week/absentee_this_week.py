# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

def get_columns():
    return [
        _("Employee") + ":Data:100",
        _("Leave Application") + ":Data:150",
		_("Employee Name") + ":Data:300",
		_("Total Leave Days") + ":Float:150",
		_("From Date") + ":Date:150",
		_("To Date") + ":Date:150",
	]
    
def get_data(filters):
	data = []
	today = frappe.utils.today()
	first_day_of_this_week = frappe.utils.get_first_day_of_week(today)
	last_day_of_this_week = frappe.utils.get_last_day_of_week(today)
	data = frappe.db.sql("""
						SELECT
							employee,
							name as leave_application,
							employee_name,
							total_leave_days,
							from_date,
							to_date
						FROM
							`tabLeave Application`
						WHERE
							status = "Approved"
						AND
							(
								WEEK(from_date) = WEEK(NOW())
							OR
								WEEK(to_date) = WEEK(NOW())
							OR
								(from_date < NOW() AND to_date > NOW())
							)
						ORDER BY
							from_date asc
						""".format(first_day_of_this_week=first_day_of_this_week, last_day_of_this_week=last_day_of_this_week),
						as_dict=True, debug = True
					)
	return data
