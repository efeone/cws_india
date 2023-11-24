import frappe
from frappe.utils.user import get_users_with_role

def send_absentee_this_week():
    '''
        method to send a mail to hr managers and director of the company the report of staff on leave in the week
    '''
    if frappe.utils.getdate().weekday() != 0:
        return
    recipients = [recipient for recipient in get_users_with_role('HR Manager') + get_users_with_role('Director') if recipient not in ['admin@cwsindia.org']]
    subject = 'Report of Staff on Leave this Week'
    url = 'https://cwsindia.frappe.cloud/app/query-report/Absentee%20This%20Week'
    content = 'Please follow the below link to view the report of Staff on Leave this week:\n{url}'.format(url=url)
    frappe.sendmail(recipients, subject=subject, content=content)
