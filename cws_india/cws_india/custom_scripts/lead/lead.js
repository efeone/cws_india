frappe.ui.form.on("Lead", {
    refresh: function(frm) {
        frm.add_custom_button(__('Donation'), function(){
            frappe.new_doc('Donation')
        }, __('Create'));
        frm.add_custom_button(__('Donor'), function(){
            frappe.new_doc('Donor')
        }, __('Create'));
    }
});
