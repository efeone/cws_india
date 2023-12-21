# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _
from frappe.email import sendmail_to_system_managers
from frappe.model.document import Document
from frappe.utils import flt, get_link_to_form, getdate

from non_profit.non_profit.doctype.membership.membership import verify_signature
from cws_india.cws_india.doctype.cws_lead.cws_lead import  sync_donations


class CustomDonation(Document):
    def validate(self):
        if not self.donor or not frappe.db.exists('CWS Lead', self.donor):
            frappe.throw(_('Please select a Lead'))
            
    def before_save(self):
        self.set_donor_name()
    
    def on_Submit(self):
        sync_donations(self.donor)

    def create_donor_for_website_user(self):
        donor_name = frappe.get_value('Donor', dict(email=frappe.session.user))

        if not donor_name:
            user = frappe.get_doc('User', frappe.session.user)
            donor = frappe.get_doc(dict(
                doctype='Donor',
                donor_type=self.get('donor_type'),
                email=frappe.session.user,
                member_name=user.get_fullname()
            )).insert(ignore_permissions=True)
            donor_name = donor.name

        if self.get('__islocal'):
            self.donor = donor_name

    def on_payment_authorized(self, *args, **kwargs):
        self.db_set("paid", 1)
        self.load_from_db()
        self.create_payment_entry()

    def create_payment_entry(self, date=None):
        settings = frappe.get_doc('Non Profit Settings')
        if not settings.automate_donation_payment_entries:
            return

        if not settings.donation_payment_account:
            frappe.throw(_('You need to set <b>Payment Account</b> for Donation in {0}').format(
                get_link_to_form('Non Profit Settings', 'Non Profit Settings')))

        from non_profit.non_profit.custom_doctype.payment_entry import get_donation_payment_entry

        frappe.flags.ignore_account_permission = True
        pe = get_donation_payment_entry(dt=self.doctype, dn=self.name)
        frappe.flags.ignore_account_permission = False
        pe.paid_from = settings.donation_debit_account
        pe.paid_to = settings.donation_payment_account
        pe.posting_date = date or getdate()
        pe.reference_no = self.name
        pe.reference_date = date or getdate()
        pe.flags.ignore_mandatory = True
        pe.insert()
        pe.submit()
        
    def set_donor_name(self):
        if self.custom_donation_from == 'Organization':
            donor_name = frappe.db.get_value('CWS Lead', self.donor, 'organization_name')
        else:
            donor_name = frappe.db.get_value('CWS Lead', self.donor, 'lead_name')
        self.donor_name = donor_name