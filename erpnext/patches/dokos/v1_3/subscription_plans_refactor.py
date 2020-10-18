import frappe

def execute():
    frappe.reload_doctype("Subscription")
    frappe.reload_doctype("Subscription Plan")
    frappe.reload_doctype("Subscription Plan Detail")
    frappe.reload_doc("accounts", "doctype", "subscription_event")

    subscriptions = frappe.get_all("Subscription")
    for subscription in subscriptions:
        doc = frappe.get_doc("Subscription", subscription)
        price_determination = None
        for plan in doc.plans:
            sub_plan = frappe.get_doc("Subscription Plan", plan.plan)
            doc.billing_interval = sub_plan.billing_interval
            doc.billing_interval_count = sub_plan.billing_interval_count
            doc.currency = sub_plan.currency
            plan.item = sub_plan.item
            plan.uom = sub_plan.uom
            if not price_determination:
                price_determination = sub_plan.price_determination

            plan.price_determination = price_determination
            plan.fixed_rate = sub_plan.cost

            for pay_plan in frappe.get_all("Subscription Gateway Plans", dict(parent=sub_plan.name)):
                gateway = frappe.db.get_value("Subscription Gateway Plans", pay_plan.name, "payment_gateway")
                if frappe.db.get_value("Payment Gateway", gateway, "gateway_settings") == "Stripe Settings":
                    plan.stripe_plan = frappe.db.get_value("Subscription Gateway Plans", pay_plan.name, "payment_plan")

            if not sub_plan.subscription_plans_template:
                new_doc = frappe.copy_doc(plan)
                new_doc.parenttype = "Subscription Plan"
                new_doc.parent = sub_plan.name
                new_doc.parentfield = "subscription_plans_template"
                new_doc.insert()

        doc.save()
        
    frappe.delete_doc_if_exists("DocType", "Subscription Gateway Plans")