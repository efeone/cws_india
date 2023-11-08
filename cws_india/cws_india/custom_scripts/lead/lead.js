frappe.ui.form.on("Lead", {
    refresh: function(frm) {
        if(!frm.is_new() && frm.doc.status == 'Converted'){
            frappe.call('cws_india.cws_india.custom_scripts.lead.lead.check_donor_exists', {
                lead: frm.doc.name
            }).then(r => {
                let donor = r.message
                console.log('here')
                frm.add_custom_button(__('Donation'), function(){
                    frappe.new_doc('Donation', {
                        'donor': donor
                    })
                }, __('Create'));
            })
        }
    }
});
