import os
import pathlib
import re


slug = None
branch = None
commit = None

_exclude_pattern = re.compile(
    r'/(\.?virtualenvs?|'
    r'\.?v?envs?|'
    r'\.git|'
    r'\.tox|'
    r'\.pytest_cache|'
    r'\.coverage|'
    r'coverage\.xml|'
    r'[^/]*\.egg-info|'
    r'vendor|'
    r'__pycache__|'
    r'node_modules)(/|$)'
)
_exlude_extension = (
    '.png',
    '.gif',
    '.jpg',
    '.jpeg',
    '.md',
)


def os_ls_files():
    basedir = os.getcwd()
    paths = []
    for path in pathlib.Path(basedir).glob('**/*'):
        if path.is_dir():
            continue
        if path.suffix in _exlude_extension:
            continue

        _path = str(path)
        if _exclude_pattern.search(_path):
            continue
        paths.append(os.path.relpath(_path, basedir))
    return paths


try:
    import git

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

    def _git_ls_files():
        repo = git.Repo(os.getcwd())
        return [
            e.path for e in repo.head.commit.tree.traverse()
            if not hasattr(e, 'blobs')
        ]

    ls_files = _git_ls_files

except Exception:
    # For now we just ignore every error, so we don't have to
    # double wrap the try block with GitPython specific exceptions
    ls_files = os_ls_files
