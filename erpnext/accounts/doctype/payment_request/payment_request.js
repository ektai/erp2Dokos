frappe.ui.form.on("Payment Request", {
	setup(frm) {
		frm.set_query("reference_doctype", function() {
			return {
				filters: {
					"name": ["in", ["Sales Order", "Sales Invoice", "Subscription"]]
				}
			};
		});

		frm.set_query("party_type", function() {
			return {
				query: "erpnext.setup.doctype.party_type.party_type.get_party_type",
			};
		});
	},
	onload(frm) {
		if (frm.doc.reference_doctype) {
			frappe.call({
				method:"erpnext.accounts.doctype.payment_request.payment_request.get_print_format_list",
				args: {"ref_doctype": frm.doc.reference_doctype},
				callback:function(r){
					set_field_options("print_format", r.message["print_format"])
				}
			})
		}
	},
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.payment_key) {
			frm.web_link && frm.web_link.remove();
			frm.add_web_link(`/payments?link=${frm.doc.payment_key}`, __("See payment link"));
		}

		if(frm.doc.status !== "Paid" && frm.doc.docstatus==1 && frm.doc.message && !frm.doc.mute_email && frm.doc.email_to){
			frm.add_custom_button(__('Resend Payment Email'), function(){
				frappe.call({
					method: "erpnext.accounts.doctype.payment_request.payment_request.resend_payment_email",
					args: {"docname": frm.doc.name},
					freeze: true,
					freeze_message: __("Sending"),
					callback: function(r){
						if(!r.exc) {
							frappe.msgprint(__("Message Sent"));
						}
					}
				});
			}, __("Actions"));
		}

		if(frm.doc.status == "Initiated") {
			if (!frm.doc.payment_gateway_account) {
				frm.add_custom_button(__('Create Payment Entry'), function(){
					frappe.call({
						method: "erpnext.accounts.doctype.payment_request.payment_request.make_payment_entry",
						args: {"docname": frm.doc.name},
						freeze: true,
						callback: function(r){
							if(!r.exc) {
								const doc = frappe.model.sync(r.message);
								frappe.set_route("Form", doc[0].doctype, doc[0].name);
							}
						}
					});
				});
			}

			if (!frm.doc.transaction_reference && (frm.doc.payment_gateway || frm.doc.payment_gateways.length === 1)) {
				frappe.xcall("erpnext.accounts.doctype.payment_request.payment_request.check_if_immediate_payment_is_autorized",
					{
						payment_request: frm.doc.name,
					}
				).then(r => {
					if (r) {
						frm.trigger("process_payment_immediately");
					}
				})
			}
		}

		if (frm.doc.docstatus === 1 && ["Initiated", "Pending"].includes(frm.doc.status)) {
			frm.add_custom_button(__('Set as completed'), function(){
				frappe.xcall("erpnext.accounts.doctype.payment_request.payment_request.make_status_as_completed", {name: frm.doc.name})
				.then(r => {
					frm.reload_doc()
				})
			})
		}
	},
	process_payment_immediately(frm) {
		frm.add_custom_button(__('Process payment immediately'), function(){
			frappe.call({
				method: "process_payment_immediately",
				doc: frm.doc,
			}).then(r => {
					frm.reload_doc()
					frappe.show_alert({message:__("Payment successfully initialized"), indicator:'green'});
			})
		}, __("Actions"))
	},
	reference_doctype(frm) {
		frm.trigger('get_reference_amount');
	},
	reference_name(frm) {
		frm.trigger('get_reference_amount');
	},
	email_template(frm) {
		if (frm.doc.email_template) {
			frappe.xcall('erpnext.accounts.doctype.payment_request.payment_request.get_message', {
				doc: frm.doc,
				template: frm.doc.email_template
			}).then(r => {
				let signature = frappe.boot.user.email_signature || "";

				if(!frappe.utils.is_html(signature)) {
					signature = signature.replace(/\n/g, "<br>");
				}

				if(r.message && signature && r.message.includes(signature)) {
					signature = "";
				}
		
				const content = (r.message || "") + (signature ? ("<br>" + signature) : "");

				frm.set_value("subject", r.subject);
				frm.set_value("message", content);
			})
		}
	},
	payment_gateways_template(frm) {
		if(frm.doc.payment_gateways_template) {
			frappe.model.with_doc("Portal Payment Gateways Template", frm.doc.payment_gateways_template, function() {
				const template = frappe.get_doc("Portal Payment Gateways Template", frm.doc.payment_gateways_template)
				frm.set_value('payment_gateways', template.payment_gateways.slice());
			});
		}
	},
	get_reference_amount(frm) {
		if (frm.doc.reference_doctype && frm.doc.reference_name) {
			frappe.xcall('erpnext.accounts.doctype.payment_request.payment_request.get_reference_amount', {
				doctype: frm.doc.reference_doctype,
				docname: frm.doc.reference_name
			}).then(r => {
				r&&frm.set_value("grand_total", r);
				frm.refresh_fields("grand_total");
			})
		}
	}

})
