// Copyright (c) 2019, Dokos SAS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Contract", {
	contract_template: function (frm) {
		if (frm.doc.contract_template) {
			frappe.xcall("erpnext.crm.doctype.contract.contract.get_contract_template", {
				template_name: frm.doc.contract_template,
				doc: frm.doc
			})
			.then((r) => {
				if (r) {
					frm.set_value("contract_terms", r.contract_terms)
					frm.set_value("requires_fulfilment", r.requires_fulfilment)
					$.each(r.fulfilment_terms, function (index, row) {
						var d = frm.add_child("fulfilment_terms");
						d.requirement = row.requirement;
						frm.refresh_field("fulfilment_terms");
					});
				}
			})
		}
	}
});
