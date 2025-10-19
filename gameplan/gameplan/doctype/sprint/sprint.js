frappe.ui.form.on('Sprint', {

    project: async function(frm) {
        if (!frm.doc.project_name) return;
        const project_code = frm.doc.project_name.toLowerCase().replace(/\s+/g, '-');
        console.log(project_code)
        const existing_sprints = await frappe.db.get_list('Sprint', {
            filters: { project: frm.doc.project },
            fields: ['name'],
            limit: 1000
        });
        const sprint_count = existing_sprints.length + 1;
        const sprint_number = String(sprint_count).padStart(3, '0');
        const sprint_name = `${project_code}-sprint-${sprint_number}`;
        frm.set_value('sprint_name', sprint_name);
    }
});

