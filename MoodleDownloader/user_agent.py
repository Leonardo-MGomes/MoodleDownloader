from importlib.metadata import metadata, PackageNotFoundError


def build_user_agent(package_name: str) -> str:
    try:
        meta = metadata(package_name)

        name = meta.get("Name", package_name)
        version = meta.get("Version", "unknown")

        author = meta.get("Author")
        email = meta.get("Author-email")
        homepage = meta.get("Home-page")

        contact = None
        if email:
            contact = f"contact: {email}"
        elif homepage:
            contact = f"+{homepage}"

        if author and contact:
            info = f"{author}; {contact}"
        elif contact:
            info = contact
        elif author:
            info = author
        else:
            info = None

        if info:
            return f"{name}/{version} ({info})"
        return f"{name}/{version}"

    except PackageNotFoundError:
        return f"{package_name}/dev"
