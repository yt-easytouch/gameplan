# Copyright (c) 2022, Frappe Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from gameplan.extends.client import check_permissions
from gameplan.gameplan.doctype.gp_notification.gp_notification import GPNotification
from gameplan.mixins.activity import HasActivity
from gameplan.mixins.mentions import HasMentions
from gameplan.search_sqlite import GameplanSearch, GameplanSearchIndexMissingError
import re

def simple_slugify(text):
    """Convert text to a URL-friendly slug (lowercase, hyphens)."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)  # Replace non-alphanumeric with hyphen
    text = re.sub(r"-+", "-", text)           # Remove multiple hyphens
    return text.strip("-")

class GPTask(HasMentions, HasActivity, Document):
	on_delete_cascade = ["GP Comment", "GP Activity"]
	on_delete_set_null = ["GP Notification"]
	activities = ["Task Value Changed"]
	mentions_field = "description"

	def before_insert(self):
		if not self.status:
			self.status = "Backlog"
		if self.project:
			# Get project code
			project_code = frappe.db.get_value("GP Project", self.project, "code")
			if project_code:
				clean_project = simple_slugify(project_code)
				clean_title = simple_slugify(self.title)

				# Get highest number for that project
				last_number = frappe.db.sql("""
					SELECT CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(taskid, '_', -2), '_', -1) AS UNSIGNED)
					FROM `tabGP Task`
					WHERE taskid LIKE %s
					ORDER BY CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(taskid, '_', -2), '_', -1) AS UNSIGNED) DESC
					LIMIT 1
				""", (f"{clean_project}_%_{clean_title}",))

				next_number = (last_number[0][0] + 1) if last_number else 1
				padded_number = str(next_number).zfill(3)

				self.taskid = f"{clean_project}_{padded_number}_{clean_title}"

	def after_insert(self):
		self.update_tasks_count()


	
	def on_update(self):
		self.notify_mentions()
		self.log_value_updates()
		self.update_search_index()

	def log_value_updates(self):
		fields = ["title", "description", "status", "priority", "assigned_to", "due_date", "project"]
		for field in fields:
			prev_doc = self.get_doc_before_save()
			if prev_doc and str(self.get(field)) != str(prev_doc.get(field)):
				self.log_activity(
					"Task Value Changed",
					data={
						"field": field,
						"field_label": self.meta.get_label(field),
						"old_value": prev_doc.get(field),
						"new_value": self.get(field),
					},
				)

	def update_search_index(self):
		if self.has_value_changed("title") or self.has_value_changed("description"):
			try:
				search = GameplanSearch()
				search.index_doc(self)
			except GameplanSearchIndexMissingError:
				pass

	def update_comments_count(self):
		comments_count = frappe.db.count(
			"GP Comment", {"reference_doctype": "GP Task", "reference_name": self.name}
		)
		self.db_set("comments_count", comments_count)

	def on_trash(self):
		self.update_tasks_count()
		try:
			search = GameplanSearch()
			search.remove_doc(self)
		except GameplanSearchIndexMissingError:
			pass

	def update_tasks_count(self):
		if not self.project:
			return
		frappe.get_doc("GP Project", self.project).update_tasks_count()

	@frappe.whitelist()
	def track_visit(self):
		GPNotification.clear_notifications(task=self.name)


@frappe.whitelist(allow_guest = True)
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
	doctype = "GP Task"
	check_permissions(doctype, parent)

	fields = frappe.parse_json(fields) if fields else None
	filters = frappe.parse_json(filters) if filters else {}
	assigned_or_owner = filters.pop("assigned_or_owner", None)
	limit = int(limit)
	query_filters = filters.copy()
	if assigned_or_owner:
		query_filters["assigned_to"] = assigned_or_owner

	tasks = frappe.get_all(
		doctype,
		fields=fields or ["name", "subject", "status", "owner"],
		filters=query_filters,
		order_by=order_by,
		limit_start=start,
		limit_page_length=limit + 1,
	)

	task_names = [t["name"] for t in tasks]

	if task_names:
		total_sub_tasks = frappe.get_all(
			"GP Sub Task",
			fields=["parent", "COUNT(*) as total"],
			filters={"parent": ["in", task_names]},
			group_by="parent"
		)

		done_sub_tasks = frappe.get_all(
			"GP Sub Task",
			fields=["parent", "COUNT(*) as done"],
			filters={
				"parent": ["in", task_names],
				"status": "Done"
			},
			group_by="parent"
		)

		# Convert to dict for lookup
		total_map = {t["parent"]: t["total"] for t in total_sub_tasks}
		done_map = {t["parent"]: t["done"] for t in done_sub_tasks}

		# Merge stats into tasks
		for t in tasks:
			name = t["name"]
			total = total_map.get(str(name), 0)
			done = done_map.get(str(name), 0)
			t["total_sub_tasks"] = total
			t["done_sub_tasks"] = done

	frappe.response["has_next_page"] = len(tasks) > limit
	return tasks[:limit]

def update_task_status_if_subtasks_done(doc, method=None):
    if not doc.get("sub_tasks"):
        return
    all_done = all(sub.status == "Done" for sub in doc.sub_tasks)
    current_status = frappe.db.get_value("GP Task", doc.name, "status")
    status = "Done" if all_done and current_status != "Done" else "In Progress"
    frappe.db.set_value("GP Task", doc.name, "status", status)
    frappe.db.commit()
        
