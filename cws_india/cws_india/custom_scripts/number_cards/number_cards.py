import frappe


@frappe.whitelist()
def last_year_this_month_lead_count():
    """
        Gets the count of leads converted on last year in the current month and returns it
        Output:
            Object for number card to display the count and route to the list view of Lead with the filters applied
    """
    today = frappe.utils.getdate()
    last_year_this_month_datetime = frappe.utils.add_years(today, -1)
    creation_start = frappe.utils.get_first_day(last_year_this_month_datetime)
    creation_end = frappe.utils.get_last_day(last_year_this_month_datetime)
    count = frappe.db.count(
        "Lead",
        {
            "modified": ["between", [creation_start, creation_end]],
            "status": "Converted",
        },
    )

    return_obj = {
        "value": count,
        "fieldtype": "Int",
        "route_options": {
            "modified": ["between", [creation_start, creation_end]],
            "status": "Converted",
        },
        "route": ["list", "Lead"],
    }

    return return_obj
