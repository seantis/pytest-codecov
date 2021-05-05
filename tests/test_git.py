import git
import os


def test_no_repository(pytester):

    pytester.makepyfile(
        """
        import pytest_codecov.git as git
        from importlib import reload

        reload(git)

        def test_no_repository():
            assert git.slug is None
            assert git.branch is None
            assert git.commit is None
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_slug(pytester):
    repo = git.Repo.init(pytester.path)
    repo.create_remote('origin', 'git@example.com:foo/bar.git')

    pytester.makepyfile(
        """
        import pytest_codecov.git as git
        from importlib import reload

        reload(git)

        def test_slug():
            assert git.slug == 'foo/bar'
        """
    )

    repo.index.add(os.path.join(pytester.path, 'test_slug.py'))
    repo.index.commit('Initial commit')

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_slug_https(pytester):
    repo = git.Repo.init(pytester.path)
    repo.create_remote('origin', 'https://example.com/foo/bar')

    pytester.makepyfile(
        """
        import pytest_codecov.git as git
        from importlib import reload

        reload(git)

        def test_slug():
            assert git.slug == 'foo/bar'
        """
    )

    repo.index.add(os.path.join(pytester.path, 'test_slug_https.py'))
    repo.index.commit('Initial commit')

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_branch(pytester):
    repo = git.Repo.init(pytester.path)
    repo.create_remote('origin', 'git@example.com:foo/bar.git')

    pytester.makepyfile(
        """
        import pytest_codecov.git as git
        from importlib import reload

        reload(git)

        def test_branch():
            assert git.branch == 'foo'
        """
    )

    repo.index.add(os.path.join(pytester.path, 'test_branch.py'))
    repo.index.commit('Initial commit')
    new_branch = repo.create_head('foo', 'HEAD')
    repo.head.reference = new_branch

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_branch_detached(pytester):
    repo = git.Repo.init(pytester.path)
    repo.create_remote('origin', 'git@example.com:foo/bar.git')

    pytester.makepyfile(
        """
        import pytest_codecov.git as git
        from importlib import reload

        reload(git)

        def test_branch_detached():
            assert git.branch is None
        """
    )

    repo.index.add(os.path.join(pytester.path, 'test_branch_detached.py'))
    repo.index.commit('Initial commit')
    repo.head.reference = repo.commit('HEAD')

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_commit(pytester):
    repo = git.Repo.init(pytester.path)
    repo.create_remote('origin', 'git@example.com:foo/bar.git')

    # create dummy file for initial commit
    pytester.makefile('.txt', foo='bar')
    repo.index.add(os.path.join(pytester.path, 'foo.txt'))
    repo.index.commit('Initial commit')

    pytester.makepyfile(
        f"""
        import pytest_codecov.git as git
        from importlib import reload

        reload(git)

        def test_commit():
            assert git.commit == '{repo.head.commit.hexsha}'
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
