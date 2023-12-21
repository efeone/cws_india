frappe.ui.form.on('Donation', {
    refresh: function(frm) {
        console.log('here');
        set_donor_query(frm)
    }
});

function set_donor_query(frm) {
    frm.set_query('donor', () => {
        return{
            filters: {
                status:'Donor'
            }
        }
    })
}