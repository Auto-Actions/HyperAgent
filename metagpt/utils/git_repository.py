#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/20
@Author  : mashenquan
@File    : git_repository.py
@Desc: Git repository management. RFC 135 2.2.3.3.
"""
from __future__ import annotations

import shutil
from enum import Enum
from pathlib import Path
from typing import Dict

from git.repo import Repo
from git.repo.fun import is_git_dir

from metagpt.const import WORKSPACE_ROOT
from metagpt.utils.dependency_file import DependencyFile
from metagpt.utils.file_repository import FileRepository


class ChangeType(Enum):
    ADDED = "A"  # File was added
    COPIED = "C"  # File was copied
    DELETED = "D"  # File was deleted
    RENAMED = "R"  # File was renamed
    MODIFIED = "M"  # File was modified
    TYPE_CHANGED = "T"  # Type of the file was changed
    UNTRACTED = "U"  # File is untracked (not added to version control)


class GitRepository:
    """A class representing a Git repository.

    :param local_path: The local path to the Git repository.
    :param auto_init: If True, automatically initializes a new Git repository if the provided path is not a Git repository.

    Attributes:
        _repository (Repo): The GitPython `Repo` object representing the Git repository.
    """

    def __init__(self, local_path=None, auto_init=True):
        """Initialize a GitRepository instance.

        :param local_path: The local path to the Git repository.
        :param auto_init: If True, automatically initializes a new Git repository if the provided path is not a Git repository.
        """
        self._repository = None
        self._dependency = None
        if local_path:
            self.open(local_path=local_path, auto_init=auto_init)

    def open(self, local_path: Path, auto_init=False):
        """Open an existing Git repository or initialize a new one if auto_init is True.

        :param local_path: The local path to the Git repository.
        :param auto_init: If True, automatically initializes a new Git repository if the provided path is not a Git repository.
        """
        if self.is_git_dir(local_path):
            self._repository = Repo(local_path)
            return
        if not auto_init:
            return
        local_path.mkdir(parents=True, exist_ok=True)
        return self._init(local_path)

    def _init(self, local_path: Path):
        """Initialize a new Git repository at the specified path.

        :param local_path: The local path where the new Git repository will be initialized.
        """
        self._repository = Repo.init(path=local_path)

    def add_change(self, files: Dict):
        """Add or remove files from the staging area based on the provided changes.

        :param files: A dictionary where keys are file paths and values are instances of ChangeType.
        """
        if not self.is_valid or not files:
            return

        for k, v in files.items():
            self._repository.index.remove(k) if v is ChangeType.DELETED else self._repository.index.add([k])

    def commit(self, comments):
        """Commit the staged changes with the given comments.

        :param comments: Comments for the commit.
        """
        if self.is_valid:
            self._repository.index.commit(comments)

    def delete_repository(self):
        """Delete the entire repository directory."""
        if self.is_valid:
            shutil.rmtree(self._repository.working_dir)

    @property
    def changed_files(self) -> Dict[str, str]:
        """Return a dictionary of changed files and their change types.

        :return: A dictionary where keys are file paths and values are change types.
        """
        files = {i: ChangeType.UNTRACTED for i in self._repository.untracked_files}
        changed_files = {f.a_path: ChangeType(f.change_type) for f in self._repository.index.diff(None)}
        files.update(changed_files)
        return files

    @staticmethod
    def is_git_dir(local_path):
        """Check if the specified directory is a Git repository.

        :param local_path: The local path to check.
        :return: True if the directory is a Git repository, False otherwise.
        """
        git_dir = Path(local_path) / ".git"
        if git_dir.exists() and is_git_dir(git_dir):
            return True
        return False

    @property
    def is_valid(self):
        """Check if the Git repository is valid (exists and is initialized).

        :return: True if the repository is valid, False otherwise.
        """
        return bool(self._repository)

    @property
    def status(self) -> str:
        """Return the Git repository's status as a string."""
        if not self.is_valid:
            return ""
        return self._repository.git.status()

    @property
    def workdir(self) -> Path | None:
        """Return the path to the working directory of the Git repository.

        :return: The path to the working directory or None if the repository is not valid.
        """
        if not self.is_valid:
            return None
        return Path(self._repository.working_dir)

    def archive(self, comments="Archive"):
        """Archive the current state of the Git repository.

        :param comments: Comments for the archive commit.
        """
        self.add_change(self.changed_files)
        self.commit(comments)

    def new_file_repository(self, relative_path: Path | str = ".") -> FileRepository:
        """Create a new instance of FileRepository associated with this Git repository.

        :param relative_path: The relative path to the file repository within the Git repository.
        :return: A new instance of FileRepository.
        """
        return FileRepository(git_repo=self, relative_path=Path(relative_path))

    async def get_dependency(self) -> DependencyFile:
        """Get the dependency file associated with the Git repository.

        :return: An instance of DependencyFile.
        """
        if not self._dependency:
            self._dependency = DependencyFile(workdir=self.workdir)
        return self._dependency


if __name__ == "__main__":
    path = WORKSPACE_ROOT / "git"
    path.mkdir(exist_ok=True, parents=True)

    repo = GitRepository()
    repo.open(path, auto_init=True)

    changes = repo.changed_files
    print(changes)
    repo.add_change(changes)
    print(repo.status)
    repo.commit("test")
    print(repo.status)
    repo.delete_repository()
