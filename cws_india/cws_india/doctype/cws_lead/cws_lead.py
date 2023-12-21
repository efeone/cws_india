# Copyright (c) 2023, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.contacts.address_and_contact import (
    delete_contact_and_address,
    load_address_and_contact,
)
from frappe.utils import has_gravatar, validate_email_address
from frappe.utils.data import comma_and, get_link_to_form
from frappe import _
from frappe.model.mapper import get_mapped_doc


class CWSLead(Document):
    def onload(self):
        customer = frappe.db.get_value("Customer", {"lead_name": self.name})
        self.get("__onload").is_customer = customer
        load_address_and_contact(self)

    def validate(self):
        self.set_full_name()
        self.set_lead_name()
        self.set_title()
        # self.set_status()
        self.check_email_id_is_unique()
        self.validate_email_id()
        
    def before_save(self):
        if not self.is_new():
            sync_donations(self.name)

    def before_insert(self):
        self.contact_doc = None
        if frappe.db.get_single_value("CRM Settings", "auto_creation_of_contact"):
            self.contact_doc = self.create_contact()

    def after_insert(self):
        self.link_to_contact()

    def on_trash(self):
        frappe.db.set_value("Issue", {"lead": self.name}, "lead", None)
        delete_contact_and_address(self.doctype, self.name)

    def set_full_name(self):
        if self.first_name:
            self.lead_name = " ".join(
                filter(
                    None,
                    [
                        self.salutation,
                        self.first_name,
                        self.middle_name,
                        self.last_name,
                    ],
                )
            )

    def set_lead_name(self):
        if not self.lead_name:
            # Check for leads being created through data import
            if (
                not self.organization_name
                and not self.email_id
                and not self.flags.ignore_mandatory
            ):
                frappe.throw(
                    _(
                        "A Lead requires either a person's name or an organization's name"
                    )
                )
            elif self.organization_name:
                self.lead_name = self.organization_name
            else:
                self.lead_name = self.email_id.split("@")[0]

    def set_title(self):
        self.title = (
            self.organization_name
            if self.contact_type == "Organization"
            else self.lead_name
        )

    def check_email_id_is_unique(self):
        if self.email_id:
            # validate email is unique
            if not frappe.db.get_single_value(
                "CRM Settings", "allow_lead_duplication_based_on_emails"
            ):
                duplicate_leads = frappe.get_all(
                    "Lead",
                    filters={"email_id": self.email_id, "name": ["!=", self.name]},
                )
                duplicate_leads = [
                    frappe.bold(get_link_to_form("Lead", lead.name))
                    for lead in duplicate_leads
                ]

                if duplicate_leads:
                    frappe.throw(
                        frappe._(
                            "Email Address must be unique, it is already used in {0}"
                        ).format(comma_and(duplicate_leads)),
                        frappe.DuplicateEntryError,
                    )

    def validate_email_id(self):
        if self.email_id:
            if not self.flags.ignore_email_validation:
                validate_email_address(self.email_id, throw=True)

            if self.email_id == self.lead_owner:
                frappe.throw(_("Lead Owner cannot be same as the Lead Email Address"))

            if self.is_new() or not self.image:
                self.image = has_gravatar(self.email_id)

    def link_to_contact(self):
        # update contact links
        if self.contact_doc:
            self.contact_doc.append(
                "links",
                {
                    "link_doctype": "CWS Lead",
                    "link_name": self.name,
                    "link_title": self.lead_name,
                },
            )
            self.contact_doc.save()

    def create_contact(self):
        if not self.lead_name:
            self.set_full_name()
            self.set_lead_name()

        contact = frappe.new_doc("Contact")
        contact.update(
            {
                "first_name": self.first_name or self.lead_name,
                "last_name": self.last_name,
                "salutation": self.salutation,
                "gender": self.gender,
                "designation": self.job_title,
                "company_name": self.organization_name,
            }
        )

        if self.email_id:
            contact.append("email_ids", {"email_id": self.email_id, "is_primary": 1})

        if self.phone:
            contact.append("phone_nos", {"phone": self.phone, "is_primary_phone": 1})

        if self.mobile_no:
            contact.append(
                "phone_nos", {"phone": self.mobile_no, "is_primary_mobile_no": 1}
            )

        contact.insert(ignore_permissions=True)
        contact.reload()  # load changes by hooks on contact

        return contact

    def sync_donations(self):
        donations = frappe.db.get_list("Donation", {"donor": self.name, 'docstatus':1}, pluck="name")
        donations_in_table = frappe.db.get_list('Donations Details', {"parent":self.name}, pluck="donation")
        for donation in donations:
            if donation not in donations_in_table:
                amount, date, donor_type = frappe.db.get_value("Donation", donation, ["amount", "date", "custom_donation_from"])
                is_soft_credit = 1 if donor_type == "Organization" else 0
                self.append("donations", {
					"donation":donation,
					"amount":amount,
					"date":date,
					"is_soft_credit": is_soft_credit
				})
        frappe.db.delete("Donations Details", {"donation":["not in", donations]})
        frappe.db.commit()


@frappe.whitelist()
def make_customer(source_name, target_doc=None):
    return _make_customer(source_name, target_doc)


def _make_customer(source_name, target_doc=None, ignore_permissions=False):
    def set_missing_values(source, target):
        if source.company_name:
            target.customer_type = "Company"
            target.customer_name = source.company_name
        else:
            target.customer_type = "Individual"
            target.customer_name = source.lead_name

        target.customer_group = frappe.db.get_default("Customer Group")

    doclist = get_mapped_doc(
        "Lead",
        source_name,
        {
            "Lead": {
                "doctype": "Customer",
                "field_map": {
                    "name": "lead_name",
                    "company_name": "customer_name",
                    "contact_no": "phone_1",
                    "fax": "fax_1",
                },
                "field_no_map": ["disabled"],
            }
        },
        target_doc,
        set_missing_values,
        ignore_permissions=ignore_permissions,
    )

    return doclist

@frappe.whitelist()
def sync_donations(name):
    self = frappe.get_doc('CWS Lead', name)
    donations = frappe.db.get_list("Donation", {"donor": self.name, 'docstatus':1}, pluck="name")
    donations_in_table = frappe.db.get_list('Donations Details', {"parent":self.name}, pluck="donation")
    for donation in donations:
        print(donation)
        if donation not in donations_in_table:
            print('not in')
            amount, date, donor_type, donor_name = frappe.db.get_value("Donation", donation, ["amount", "date", "custom_donation_from", "donor_name"])
            is_soft_credit = 1 if donor_type == "Organization" else 0
            self.append("donations", {
                "donation":donation,
                "amount":amount,
                "date":date,
                "is_soft_credit": is_soft_credit,
                "donor_name":donor_name
            })
    frappe.db.delete("Donations Details", {"donation":["not in", donations]})
    frappe.db.commit()
