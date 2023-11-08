import frappe
from frappe.model.mapper import get_mapped_doc
from frappe import _

@frappe.whitelist()
def check_donor_exists(lead):
	return frappe.db.exists('Donor', {'custom_from_lead':lead})

@frappe.whitelist()
def create_donor(doc, method=None):
	'''
		Method to create a donor when a lead is converted
		args:
			doc: document object of lead
			method: NA
	'''
	if doc.status == 'Converted':
		if not frappe.db.exists('Donor', {'custom_from_lead':doc.name} and not doc.custom_has_donated_in_the_past):

			if doc.custom_lead_type == 'Organization':
				if not doc.custom_organization:
					frappe.throw('Create Organization before proceeding')

			#creating a new donor
			new_donor = frappe.new_doc('Donor')
			# lead_full_name = f'{doc.first_name} {doc.last_name}'
			new_donor.donor_name = f'{doc.first_name} {doc.last_name}' if doc.custom_lead_type == 'Individual' else doc.custom_organization
			new_donor.donor_type = 'Organization' if doc.custom_lead_type == 'Organization' else 'Individual'
			new_donor.email = doc.email_id
			new_donor.custom_from_lead = doc.name
			new_donor.save()

			#linking contact and address with donor
			lead_contact = frappe.get_value('Dynamic Link', {'link_doctype':doc.doctype, 'link_name':doc.name, 'parenttype':'Contact'}, 'parent')
			lead_address = frappe.get_value('Dynamic Link', {'link_doctype':doc.doctype, 'link_name':doc.name, 'parenttype':'Address'}, 'parent')
			if lead_contact:
				lead_contact_doc = frappe.get_doc('Contact', lead_contact)
				lead_contact_doc.append('links', {
					'link_doctype':new_donor.doctype,
					'link_name':new_donor.name
				})
				lead_contact_doc.save()
			if lead_address:
				lead_address_doc = frappe.get_doc('Address', lead_address)
				lead_address_doc.append('links', {
					'link_doctype':new_donor.doctype,
					'link_name':new_donor.name
				})
				lead_address_doc.save()

			frappe.msgprint(_(f'Created Donor {new_donor.name} for lead {doc.title}'))
