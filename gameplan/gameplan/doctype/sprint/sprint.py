# Copyright (c) 2025, Frappe Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from gameplan.extends.client import check_permissions


class Sprint(Document):
	pass


@frappe.whitelist()
def get_list(
    fields: str = None,
    filters: str = None,
    order_by: str = None,
    start: int = 0,
    limit: int = 20,
    group_by: str = None,
    parent: str = None,
    debug=False,
):
	doctype = "Sprint"
	check_permissions(doctype, parent)

	fields = frappe.parse_json(fields) if fields else None
	filters = frappe.parse_json(filters) if filters else {}
	
	assigned_or_owner = filters.pop("assigned_or_owner", None)
	limit = int(limit)
	query_filters = filters.copy()
	# if assigned_or_owner:
	# 	query_filters["owner"] = assigned_or_owner

	sprint = frappe.get_all(
		doctype,
		fields=fields or ["name", "title", "status", "owner"],
		filters=query_filters,
		order_by=order_by,
		limit_start=start,
		limit_page_length=limit + 1,
	)
	return sprint
