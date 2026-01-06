from importlib.metadata import metadata, PackageNotFoundError


def build_user_agent(package_name: str) -> str:
    try:
        meta = metadata(package_name)

        name = meta.get("Name", package_name)
        version = meta.get("Version", "unknown")
        project_url = meta.get("Project-URL")

        info = None
        if project_url:
            info = f"+{project_url.split(", ")[-1]}"

        if info:
            return f"{name}/{version} ({info})"
        return f"{name}/{version}"

    except PackageNotFoundError:
        return f"{package_name}/dev"
