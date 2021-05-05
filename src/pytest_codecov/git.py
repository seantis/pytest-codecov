slug = None
branch = None
commit = None

try:
    import git
    import os

    repo = git.Repo(os.getcwd())
    commit = repo.head.commit.hexsha

    if not repo.head.is_detached:
        branch = repo.active_branch.name

    _origin = repo.remotes.origin
    if _origin:
        _url = _origin.url
        if _url.endswith('.git'):
            _url = _url[:-4]
        _parts = _url.split(':')[-1].split('/')
        if len(_parts) >= 2:
            slug = '/'.join(_parts[-2:])

except Exception:
    # For now we just ignore every error, so we don't have to
    # double wrap the try block with GitPython specific exceptions
    pass
