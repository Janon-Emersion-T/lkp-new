from .models import CareerApplication, Employee


def resource(
    model,
    title,
    singular,
    description,
    columns,
    search=None,
    fields="__all__",
    form=None,
):
    config = {
        "model": model,
        "title": title,
        "singular": singular,
        "description": description,
        "columns": columns,
        "search": search or [],
        "fields": fields,
    }

    if form:
        config["form"] = form

    return config


HR_RESOURCES = {
    "career-applications": resource(
        CareerApplication,
        "Career Applications",
        "Application",
        "Recruitment pipeline and career submissions.",
        [
            ("name", "Name"),
            ("position", "Position"),
            ("email", "Email"),
            ("status", "Status"),
            ("created_at", "Received"),
        ],
        ["name", "email", "phone", "position", "message"],
    ),
    "employees": resource(
        Employee,
        "Employees",
        "Employee",
        "Team members, roles, status, and internal assignment references.",
        [
            ("name", "Name"),
            ("email", "Email"),
            ("role", "Role"),
            ("status", "Status"),
            ("start_date", "Start"),
        ],
        ["name", "email", "role", "notes"],
    ),
}


HR_NAV = {
    "label": "HR & Team",
    "icon": "ti-users-group",
    "children": [
        {"label": "Employees", "resource": "employees"},
        {"label": "Applications", "resource": "career-applications"},
        {"label": "Tasks", "resource": "project-tasks"},
    ],
}
