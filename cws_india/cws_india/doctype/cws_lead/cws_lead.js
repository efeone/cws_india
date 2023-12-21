// Copyright (c) 2023, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('CWS Lead', {
	refresh: function(frm) {
		let doc = frm.doc;
		erpnext.toggle_naming_series();
		frappe.dynamic_link = {
			doc: doc,
			fieldname: 'name',
			doctype: 'CWS Lead'
		};

		if (!frm.is_new() && doc.__onload) {
			if (!frm.doc.organization)
				frm.add_custom_button(__("Organization"), make_organization, __("Create"));
			if (frm.doc.status == 'Donor'){
				frm.add_custom_button(__("Donation"), function() {
					console.log('here');
					console.log(frm);
					make_donation(frm)
				}, __("Create"));
			}
		}

		if (!frm.is_new()) {
			frappe.contacts.render_address_and_contact(frm);
		} else {
			frappe.contacts.clear_address_and_contact(frm);
		}

		show_notes(frm);
		show_activities(frm);
	}
});

function show_notes(frm) {
	if (frm.doc.docstatus == 1) return;

	const crm_notes = new erpnext.utils.CRMNotes({
		frm: frm,
		notes_wrapper: $(frm.fields_dict.notes_html.wrapper),
	});
	crm_notes.refresh();
}

function show_activities(frm) {
	if (frm.doc.docstatus == 1) return;

	const crm_activities = new erpnext.utils.CRMActivities({
		frm: frm,
		open_activities_wrapper: $(frm.fields_dict.open_activities_html.wrapper),
		all_activities_wrapper: $(frm.fields_dict.all_activities_html.wrapper),
		form_wrapper: $(frm.wrapper),
	});
	crm_activities.refresh();
}

function make_organization() {
	// code to create an organization here
	console.log('create organization code');
}

function make_donation(frm) {
	let d = new frappe.ui.Dialog({
		title: 'Enter Donation details',
		fields: [
			{
				label: 'Date',
				fieldname: 'date',
				fieldtype: 'Date',
				reqd:1
			},
			{
				label: 'Amount',
				fieldname: 'amount',
				fieldtype: 'Currency',
				reqd:1
			},
			{
				label: 'Mode of Payment',
				fieldname: 'mode_of_payment',
				fieldtype: 'Link',
				options: 'Mode of Payment'
			},
			{
				label: 'Donation Type',
				fieldname: 'donation_type',
				fieldtype: 'Select',
				options: 'Organization\nIndividual',
				rqed: 1
			}
		],
		size: 'small',
		primary_action_label: 'Submit',
		primary_action(values) {
			frappe.db.insert({
				doctype: 'Donation',
				donor: frm.doc.name,
				date: values.date,
				amount: values.amount,
				mode_of_payment: values.mode_of_payment,
				custom_donation_from: values.donation_type
			}).then(doc => {
				d.hide()
				frappe.msgprint(`Donation ${doc.name} been created for ${frm.doc.title}, Submit the Donation form to confirm`)
			})
		}
	});
	
	d.show();
	
}
