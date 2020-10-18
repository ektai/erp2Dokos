// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ready(function(){

	const loyalty_points_input = document.getElementById("loyalty-point-to-redeem");
	const loyalty_points_status = document.getElementById("loyalty-points-status");
	const currency = "{{ doc.currency }}"
	const available_loyalty_points = "{{ available_loyalty_points }}"
	if (loyalty_points_input) {
		loyalty_points_input.onblur = apply_loyalty_points;
	}

	function apply_loyalty_points() {

		if (!doc_info.grand_total) {
			frappe.msgprint(__("Loyalty points cannot be redeemed on this document."))
			return;
		}

		const loyalty_points = parseInt(loyalty_points_input.value);

		if (loyalty_points > available_loyalty_points) {
			frappe.msgprint(__(`You cannot redeem more than ${available_loyalty_points} points.`))
			return;
		}

		if (loyalty_points) {
			frappe.call({
				method: "erpnext.accounts.doctype.loyalty_program.loyalty_program.get_redeemed_amount",
				args: {
					customer: doc_info.customer,
					points_redeemed: parseInt(loyalty_points_input.value),
					grand_total: doc_info.grand_total,
					currency: currency
				},
				callback: function(r) {
					if (r) {
						let message = ""
						if (!r.message.redeem_accepted) {
							frappe.msgprint(__(`You can only redeem a maximum of ${r.message.redeemable_points} points in this order.`));
						} else {
							loyalty_points_status.innerHTML = __(`${loyalty_points} loyalty points applied for an amount of ${r.message.loyalty_amount}.`)
							const payment_button = document.getElementById("pay-for-order");
							payment_button.innerHTML = __(`Pay ${r.message.remaining_amount}`);
							payment_button.href = "/api/method/erpnext.accounts.doctype.payment_request.payment_request.make_payment_request?dn="+doc_info.doctype_name+"&dt="+doc_info.doctype+"&loyalty_points="+loyalty_points+"&submit_doc=1&order_type=Shopping Cart";
						}
					}
				}
			});
		}
	}
})