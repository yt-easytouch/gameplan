# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt


import frappe
from frappe.query_builder.functions import Count
from frappe.utils import cstr, split_emails, validate_email_address

import gameplan
from gameplan.utils import validate_type
from frappe.utils.data import now
from urllib.parse import unquote_plus
import json


@frappe.whitelist(allow_guest=True)
def get_user_info(user=None):
	if frappe.session.user == "Guest":
		frappe.throw("Authentication failed", exc=frappe.AuthenticationError)

	filters = {"roles.role": ["like", "Gameplan %"]}
	if user:
		filters["name"] = user

	users = frappe.qb.get_query(
		"User",
		filters=filters,
		fields=["name", "email", "enabled", "user_image", "full_name", "user_type"],
		order_by="full_name asc",
		distinct=True,
	).run(as_dict=1)

	user_names = [u.name for u in users]
	if user_names:
		# Get discussion counts for last 3 months
		Discussion = frappe.qb.DocType("GP Discussion")
		discussion_counts = (
			frappe.qb.from_(Discussion)
			.select(Discussion.owner, Count(Discussion.name).as_("count"))
			.where(Discussion.creation >= frappe.utils.add_months(frappe.utils.now(), -3))
			.where(Discussion.owner.isin(user_names))
			.groupby(Discussion.owner)
		).run(as_dict=1)
	else:
		discussion_counts = []
	discussion_count_map = {d.owner: d.count for d in discussion_counts}
 

	# Get comment counts for last 3 months
	Comment = frappe.qb.DocType("GP Comment")
	if user_names:
		comment_counts = (
			frappe.qb.from_(Comment)
			.select(Comment.owner, Count(Comment.name).as_("count"))
			.where(Comment.creation >= frappe.utils.add_months(frappe.utils.now(), -3))
			.where(Comment.owner.isin([u.name for u in users]))
			.groupby(Comment.owner)
		).run(as_dict=1)
	else:
		comment_counts = []
	comment_count_map = {c.owner: c.count for c in comment_counts}

	roles = frappe.db.get_all("Has Role", filters={"parenttype": "User"}, fields=["role", "parent"])
	user_profiles = frappe.db.get_all(
		"GP User Profile",
		fields=["user", "name", "image", "image_background_color", "is_image_background_removed", "bio"],
		filters={"user": ["in", [u.name for u in users]]},
	)
	user_profile_map = {u.user: u for u in user_profiles}
	for user in users:
		if frappe.session.user == user.name:
			user.session_user = True
		user_profile = user_profile_map.get(user.name)
		if user_profile:
			user.user_profile = user_profile.name
			user.user_image = user_profile.image
			user.image_background_color = user_profile.image_background_color
			user.is_image_background_removed = user_profile.is_image_background_removed
			user.bio = user_profile.bio
		user_roles = [r.role for r in roles if r.parent == user.name]
		user.role = None
		for role in ["Gameplan Guest", "Gameplan Member", "Gameplan Admin"]:
			if role in user_roles:
				user.role = role

		# Add discussion and comment counts
		user.discussions_count_3m = discussion_count_map.get(user.name, 0)
		user.comments_count_3m = comment_count_map.get(user.name, 0)

	return users


@frappe.whitelist()
@validate_type
def change_user_role(user: str, role: str):
	if gameplan.is_guest():
		frappe.throw("Only Admin can change user roles")

	if role not in ["Gameplan Guest", "Gameplan Member", "Gameplan Admin"]:
		return get_user_info(user)[0]

	user_doc = frappe.get_doc("User", user)
	for _role in user_doc.roles:
		if _role.role in ["Gameplan Guest", "Gameplan Member", "Gameplan Admin"]:
			user_doc.remove(_role)
	user_doc.append_roles(role)
	user_doc.save(ignore_permissions=True)

	return get_user_info(user)[0]


@frappe.whitelist()
@validate_type
def remove_user(user: str):
	user_doc = frappe.get_doc("User", user)
	user_doc.enabled = 0
	user_doc.save(ignore_permissions=True)
	return user


@frappe.whitelist()
@validate_type
def invite_by_email(emails: str, role: str, projects: list = None):
	if not emails:
		return
	email_string = validate_email_address(emails, throw=False)
	email_list = split_emails(email_string)
	if not email_list:
		return
	existing_members = frappe.db.get_all("User", filters={"email": ["in", email_list]}, pluck="email")
	existing_invites = frappe.db.get_all(
		"GP Invitation",
		filters={
			"email": ["in", email_list],
			"role": ["in", ["Gameplan Admin", "Gameplan Member"]],
		},
		pluck="email",
	)

	if role == "Gameplan Guest":
		to_invite = list(set(email_list) - set(existing_invites))
	else:
		to_invite = list(set(email_list) - set(existing_members) - set(existing_invites))

	if projects:
		projects = frappe.as_json(projects, indent=None)

	for email in to_invite:
		frappe.get_doc(doctype="GP Invitation", email=email, role=role, projects=projects).insert(
			ignore_permissions=True
		)


@frappe.whitelist()
def unread_notifications():
	res = frappe.db.get_all(
		"GP Notification",
		"count(name) as count",
		{"to_user": frappe.session.user, "read": 0},
	)
	return res[0].count


@frappe.whitelist(allow_guest=True)
@validate_type
def accept_invitation(key: str = None):
	if not key:
		frappe.throw("Invalid or expired key")

	result = frappe.db.get_all("GP Invitation", filters={"key": key}, pluck="name")
	if not result:
		frappe.throw("Invalid or expired key")

	invitation = frappe.get_doc("GP Invitation", result[0])

	invitation.accept()
	invitation.reload()

	user = frappe.get_doc("User", invitation.email)
	needs_password_setup = user and not user.last_password_reset_date

	if invitation.status == "Accepted":
		if needs_password_setup:
			url = invitation.get_password_link()
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = f"{url}"
		else:
			frappe.local.login_manager.login_as(invitation.email)
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = "/g"


@frappe.whitelist()
def get_unsplash_photos(keyword=None):
	from gameplan.unsplash import get_by_keyword, get_list

	if keyword:
		return get_by_keyword(keyword)

	return frappe.cache().get_value("unsplash_photos", generator=get_list)


@frappe.whitelist()
def get_unread_items():
	Discussion = frappe.qb.DocType("GP Discussion")
	Visit = frappe.qb.DocType("GP Discussion Visit")
	query = (
		frappe.qb.from_(Discussion)
		.select(Discussion.team, Count(Discussion.team).as_("count"))
		.left_join(Visit)
		.on((Visit.discussion == Discussion.name) & (Visit.user == frappe.session.user))
		.where((Visit.last_visit.isnull()) | (Visit.last_visit < Discussion.last_post_at))
		.groupby(Discussion.team)
	)

	is_guest = gameplan.is_guest()
	if is_guest:
		GuestAccess = frappe.qb.DocType("GP Guest Access")
		project_list = GuestAccess.select(GuestAccess.project).where(GuestAccess.user == frappe.session.user)
		query = query.where(Discussion.project.isin(project_list))

	# pypika doesn't have any API for "FORCE INDEX FOR JOIN"
	sql = query.get_sql()
	sql = sql.replace(
		"LEFT JOIN `tabGP Discussion Visit`",
		"LEFT JOIN `tabGP Discussion Visit` FORCE INDEX FOR JOIN(discussion_user_index)",
	)
	data = frappe.db.sql(sql, as_dict=1)

	out = {}
	for d in data:
		out[d.team] = d.count
	return out


@frappe.whitelist()
def get_unread_items_by_project(projects):
	from frappe.query_builder.functions import Count

	project_names = frappe.parse_json(projects)
	Discussion = frappe.qb.DocType("GP Discussion")
	Visit = frappe.qb.DocType("GP Discussion Visit")
	query = (
		frappe.qb.from_(Discussion)
		.select(Discussion.project, Count(Discussion.project).as_("count"))
		.left_join(Visit)
		.on((Visit.discussion == Discussion.name) & (Visit.user == frappe.session.user))
		.where((Visit.last_visit.isnull()) | (Visit.last_visit < Discussion.last_post_at))
		.where(Discussion.project.isin(project_names))
		.groupby(Discussion.project)
	)

	data = query.run(as_dict=1)
	out = {}
	for d in data:
		out[d.project] = d.count
	return out


@frappe.whitelist()
def mark_all_notifications_as_read():
	for d in frappe.db.get_all(
		"GP Notification",
		filters={"to_user": frappe.session.user, "read": 0},
		pluck="name",
	):
		doc = frappe.get_doc("GP Notification", d)
		doc.read = 1
		doc.save(ignore_permissions=True)


@frappe.whitelist()
def recent_projects():
	from frappe.query_builder.functions import Max

	ProjectVisit = frappe.qb.DocType("GP Project Visit")
	Team = frappe.qb.DocType("GP Team")
	Project = frappe.qb.DocType("GP Project")
	Pin = frappe.qb.DocType("GP Pinned Project")
	pinned_projects_query = frappe.qb.from_(Pin).select(Pin.project).where(Pin.user == frappe.session.user)
	projects = (
		frappe.qb.from_(ProjectVisit)
		.select(
			ProjectVisit.project.as_("name"),
			Project.team,
			Project.title.as_("project_title"),
			Team.title.as_("team_title"),
			Project.icon,
			Max(ProjectVisit.last_visit).as_("timestamp"),
		)
		.left_join(Project)
		.on(Project.name == ProjectVisit.project)
		.left_join(Team)
		.on(Team.name == Project.team)
		.groupby(ProjectVisit.project)
		.where(ProjectVisit.user == frappe.session.user)
		.where(ProjectVisit.project.notin(pinned_projects_query))
		.orderby(ProjectVisit.last_visit, order=frappe.qb.desc)
		.limit(12)
	)

	return projects.run(as_dict=1)


@frappe.whitelist()
def active_projects():
	from frappe.query_builder.functions import Count

	Comment = frappe.qb.DocType("GP Comment")
	Discussion = frappe.qb.DocType("GP Discussion")
	CommentCount = Count(Comment.name).as_("comments_count")
	active_projects = (
		frappe.qb.from_(Comment)
		.select(CommentCount, Discussion.project)
		.left_join(Discussion)
		.on(Discussion.name == Comment.reference_name)
		.where(Comment.reference_doctype == "GP Discussion")
		.where(Comment.creation > frappe.utils.add_days(frappe.utils.now(), -70))
		.groupby(Discussion.project)
		.orderby(CommentCount, order=frappe.qb.desc)
		.limit(12)
	).run(as_dict=1)

	projects = frappe.qb.get_query(
		"GP Project",
		fields=[
			"name",
			"title as project_title",
			"team",
			"team.title as team_title",
			"icon",
			"modified as timestamp",
		],
		filters={"name": ("in", [d.project for d in active_projects])},
	).run(as_dict=1)

	active_projects_comment_count = {d.project: d.comments_count for d in active_projects}
	for d in projects:
		d.comments_count = active_projects_comment_count.get(str(d.name), 0)

	projects.sort(key=lambda d: d.comments_count, reverse=True)

	return projects


@frappe.whitelist()
def onboarding(space, icon, emails):
	emails = frappe.parse_json(emails)
	project = frappe.get_doc(doctype="GP Project", title=space, icon=icon).insert()
	invite_by_email(", ".join(emails), role="Gameplan Member")
	return project.name


@frappe.whitelist(allow_guest=True)
def oauth_providers():
	from frappe.utils.html_utils import get_icon_html
	from frappe.utils.oauth import get_oauth2_authorize_url, get_oauth_keys
	from frappe.utils.password import get_decrypted_password

	out = []
	providers = frappe.get_all(
		"Social Login Key",
		filters={"enable_social_login": 1},
		fields=["name", "client_id", "base_url", "provider_name", "icon"],
		order_by="name",
	)

	for provider in providers:
		client_secret = get_decrypted_password("Social Login Key", provider.name, "client_secret")
		if not client_secret:
			continue

		icon = None
		if provider.icon:
			if provider.provider_name == "Custom":
				icon = get_icon_html(provider.icon, small=True)
			else:
				icon = f"<img src='{provider.icon}' alt={provider.provider_name}>"

		if provider.client_id and provider.base_url and get_oauth_keys(provider.name):
			out.append(
				{
					"name": provider.name,
					"provider_name": provider.provider_name,
					"auth_url": get_oauth2_authorize_url(provider.name, "/g"),
					"icon": icon,
				}
			)
	return out


@frappe.whitelist()
def search(query, start=0):
	from gameplan.search import GameplanSearch

	search = GameplanSearch()
	query = search.clean_query(query)

	query_parts = query.split(" ")
	if len(query_parts) == 1 and not query_parts[0].endswith("*"):
		query = f"{query_parts[0]}*"
	if len(query_parts) > 1:
		query = " ".join([f"%%{q}%%" for q in query_parts])

	result = search.search(
		f"@title|content:({query})",
		start=start,
		sort_by="modified desc",
		highlight=True,
		with_payloads=True,
	)

	comments_by_doctype = {}
	grouped_results = {}
	for d in result.docs:
		doctype, name = d.id.split(":")
		d.doctype = doctype
		d.name = name
		del d.id
		if doctype == "GP Comment":
			comments_by_doctype.setdefault(d.payload["reference_doctype"], []).append(d)
		else:
			d.project = d.payload.get("project")
			d.team = d.payload.get("team")
			del d.payload
			grouped_results.setdefault(doctype, []).append(d)

	discussion_names = [d.payload["reference_name"] for d in comments_by_doctype.get("GP Discussion", [])]
	task_names = [d.payload["reference_name"] for d in comments_by_doctype.get("GP Task", [])]

	if discussion_names:
		for d in frappe.get_all(
			"GP Discussion",
			fields=["name", "title", "last_post_at", "project", "team"],
			filters={"name": ("in", discussion_names)},
		):
			d.doctype = "GP Discussion"
			d.name = cstr(d.name)
			d.content = ""
			d.via_comment = True
			d.modified = d.last_post_at
			for c in comments_by_doctype.get("GP Discussion", []):
				if c.payload["reference_name"] == d.name:
					d.content = c.content
			grouped_results.setdefault("GP Discussion", []).append(d)

	if task_names:
		for d in frappe.get_all(
			"GP Task",
			fields=["name", "title", "modified", "project", "team"],
			filters={"name": ("in", task_names)},
		):
			d.doctype = "GP Task"
			d.name = cstr(d.name)
			d.content = ""
			d.via_comment = True
			for c in comments_by_doctype.get("GP Task", []):
				if c.payload["reference_name"] == d.name:
					d.content = c.content
			grouped_results.setdefault("GP Task", []).append(d)

	return {
		"results": grouped_results,
		"total": result.total,
		"duration": result.duration,
	}


@frappe.whitelist()
def search2(query):
	from gameplan.search2 import GameplanSearch

	search = GameplanSearch()
	result = search.search(query)
	return result


@frappe.whitelist()
def search_sqlite(query, filters=None):
	from gameplan.search_sqlite import GameplanSearch

	search = GameplanSearch()

	# Parse filters if provided as JSON string
	if filters and isinstance(filters, str):
		import json

		filters = json.loads(filters)

	result = search.search(query, filters=filters)
	return result


@frappe.whitelist()
def get_search_filter_options():
	"""Get available filter options for advanced search"""
	from gameplan.search_sqlite import GameplanSearch

	search = GameplanSearch()
	return search.get_filter_options()


def can_access_gameplan():
	"""Check if the app should be shown in /apps"""
	# from frappe.utils.modules import get_modules_from_all_apps_for_user

	if frappe.session.user == "Administrator":
		return True

	# allowed_modules = [x["module_name"] for x in get_modules_from_all_apps_for_user()]
	# if "Gameplan" not in allowed_modules:
	# 	return False

	roles = set(frappe.get_roles())
	allowed_roles = set(["System Manager", "Gameplan Admin", "Gameplan Member", "Gameplan Guest"])
	if roles.intersection(allowed_roles):
		return True

	return False

@frappe.whitelist()
def get_gp_projects_with_members():
    projects = frappe.get_all("GP Project",
        fields=[
            "name",
            "title",
            "icon",
            "team",
            "archived_at",
            "is_private",
            "modified",
            "tasks_count",
            "discussions_count"
        ],
        order_by="title asc",
        limit_page_length=99999
    )

    for project in projects:
        members = frappe.get_all("GP Member",
            filters={"parent": project["name"]},
            fields=["user"]
        )
        project["members"] = members
    
    frappe.response.update({
            "data": projects,
        })


@frappe.whitelist(allow_guest=False)
def proxy_document():
    """
    Proxy API that supports dynamic nested linked child tables.
    Automatically detects child doctype from DocField metadata.
    """

    # Get request params
    doctype = frappe.form_dict.get("parent")
    fields_param = frappe.form_dict.get("fields")
    filters_param = frappe.form_dict.get("filters")
    order_by = frappe.form_dict.get("order_by") or "creation asc"
    start = int(frappe.form_dict.get("start") or 0)
    limit = int(frappe.form_dict.get("limit") or 20)
    

    # Parse filters JSON string to dict
    filters = {}
    if filters_param:
        try:
            filters = json.loads(filters_param)
        except Exception:
            filters = {}

    # Parse fields, separate main fields and child table requests
    fields = []
    child_fields_map = {}  # { child_fieldname: [list_of_fields] }

    if fields_param:
        try:
            fields_list = json.loads(fields_param)
        except Exception:
            fields_list = []

        for f in fields_list:
            if isinstance(f, dict):
                # Nested child fields found, e.g. {"reactions": ["name", "user", "emoji"]}
                for child_fieldname, child_fields in f.items():
                    child_fields_map[child_fieldname] = child_fields
            else:
                fields.append(f)
    else:
        fields = ["name"]

    # Fetch main documents with main fields only
    docs = frappe.get_all(
        doctype,
        fields=fields,
        filters=filters,
        order_by=order_by,
        limit_start=start,
        limit_page_length=limit,
    )

    def get_child_doctype(parent_doctype, child_fieldname):
        """
        Query DocField to find child doctype linked to parent_doctype and child_fieldname
        """
        return frappe.db.get_value(
            "DocField",
            {
                "parent": parent_doctype,
                "fieldname": child_fieldname,
                "fieldtype": "Table"
            },
            "options"
        )

    # For each child field, fetch related child docs and attach
    for child_fieldname, child_fields in child_fields_map.items():
        child_doctype = get_child_doctype(doctype, child_fieldname)
        if not child_doctype:
            # Could not find child doctype for that fieldname, skip
            continue

        for doc in docs:
            child_docs = frappe.get_all(
                child_doctype,
                fields=child_fields,
                filters={
                    "parent": doc["name"],
                    "parentfield": child_fieldname,
                    "parenttype": doctype,
                },
                order_by="creation asc",
            )
            doc[child_fieldname] = child_docs

    frappe.response.update({
            "data": docs,
        })