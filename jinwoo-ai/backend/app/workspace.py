"""Read-only, user-selected workspace boundary for safe Igris diagnostics.

This module intentionally has no write, delete, rename, shell, package, or
process-launch capability. It is a small foundation that proves path confinement
before any impactful developer tool is introduced.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import stat
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from .schemas import WorkspaceAnalysis, WorkspaceEntry, WorkspaceSearch, WorkspaceStatus


class WorkspaceError(ValueError):
    """A user-safe error for an invalid workspace or path boundary."""


_TEXT_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".go", ".h", ".hpp", ".html",
    ".java", ".js", ".json", ".jsx", ".kt", ".kts", ".md", ".mjs",
    ".py", ".rb", ".rs", ".sh", ".sql", ".swift", ".toml", ".ts",
    ".tsx", ".txt", ".xml", ".yaml", ".yml",
}
_LANGUAGE_BY_SUFFIX = {
    ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript React",
    ".js": "JavaScript", ".jsx": "JavaScript React", ".json": "JSON",
    ".md": "Markdown", ".html": "HTML", ".css": "CSS", ".java": "Java",
    ".kt": "Kotlin", ".kts": "Kotlin", ".go": "Go", ".rs": "Rust",
    ".sql": "SQL", ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
}
_MAX_ANALYSIS_BYTES = 512_000
_MAX_LIST_ENTRIES = 200
# NEXA-inspired native filename search limits. They ensure that a convenience
# search never becomes a whole-device crawl or an unbounded content scanner.
_MAX_SEARCH_DIRECTORIES = 120
_MAX_SEARCH_DIRECTORY_ENTRIES = 500
_MAX_SEARCH_RESULTS = 100


@dataclass(frozen=True)
class _Workspace:
    root: Path


class WorkspaceStore:
    """Persists one deliberate local root and resolves every child beneath it."""

    def __init__(self, data_dir: Path) -> None:
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "jinwoo.db"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS workspace_settings (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    root_path TEXT NOT NULL
                )"""
            )

    def select(self, raw_path: str) -> WorkspaceStatus:
        try:
            root = Path(raw_path).expanduser().resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise WorkspaceError("Choose an existing local folder as the workspace.") from error
        if not root.is_dir():
            raise WorkspaceError("Choose a folder, not a file, as the workspace.")
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO workspace_settings (singleton, root_path) VALUES (1, ?)
                   ON CONFLICT(singleton) DO UPDATE SET root_path = excluded.root_path""",
                (str(root),),
            )
        return WorkspaceStatus(
            configured=True,
            root_label=root.name or str(root),
            detail="Selected workspace is restricted to read-only diagnostics until a future approved tool is added.",
        )

    def clear(self) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM workspace_settings WHERE singleton = 1")
        return cursor.rowcount > 0

    def status(self) -> WorkspaceStatus:
        workspace = self._workspace()
        if workspace is None:
            return WorkspaceStatus(
                configured=False,
                detail="No workspace selected. Igris has no file access until you select a project folder.",
            )
        return WorkspaceStatus(
            configured=True,
            root_label=workspace.root.name or str(workspace.root),
            detail="Read-only diagnostics are confined to the selected workspace.",
        )

    def _workspace(self) -> _Workspace | None:
        with self._connect() as connection:
            row = connection.execute("SELECT root_path FROM workspace_settings WHERE singleton = 1").fetchone()
        if row is None:
            return None
        try:
            root = Path(row["root_path"]).resolve(strict=True)
        except (OSError, RuntimeError):
            return None
        if not root.is_dir():
            return None
        return _Workspace(root=root)

    def _resolve_child(self, relative_path: str) -> tuple[_Workspace, Path]:
        workspace = self._workspace()
        if workspace is None:
            raise WorkspaceError("Select a workspace before using Igris diagnostics.")
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise WorkspaceError("Use a path relative to the selected workspace.")
        try:
            resolved = (workspace.root / candidate).resolve(strict=True)
            resolved.relative_to(workspace.root)
        except (OSError, RuntimeError, ValueError) as error:
            raise WorkspaceError("That path is outside the selected workspace or no longer exists.") from error
        return workspace, resolved

    def list_entries(self, relative_path: str = ".") -> list[WorkspaceEntry]:
        workspace, directory = self._resolve_child(relative_path)
        if not directory.is_dir():
            raise WorkspaceError("Choose a directory to inspect its files.")
        try:
            directory_entries = list(directory.iterdir())
        except OSError as error:
            raise WorkspaceError("Igris cannot read that folder inside the selected workspace.") from error
        entries: list[WorkspaceEntry] = []
        for entry in sorted(directory_entries, key=lambda item: (not item.is_dir(), item.name.casefold())):
            if len(entries) >= _MAX_LIST_ENTRIES:
                break
            try:
                resolved = entry.resolve(strict=True)
                relative = resolved.relative_to(workspace.root)
            except (OSError, RuntimeError, ValueError):
                # Do not surface a symlink that escapes the selected root.
                continue
            if resolved.is_dir():
                entries.append(WorkspaceEntry(name=entry.name, relative_path=relative.as_posix(), kind="directory"))
            elif resolved.is_file():
                entries.append(
                    WorkspaceEntry(
                        name=entry.name,
                        relative_path=relative.as_posix(),
                        kind="file",
                        size_bytes=resolved.stat().st_size,
                    )
                )
        return entries

    def search_entries(self, query: str, relative_path: str = ".", max_results: int = 50) -> WorkspaceSearch:
        """Search file and folder names only inside a selected workspace.

        The NEXA repository's file-search concept is reimplemented here without
        importing its code. This method reads no file content, executes no file,
        opens no application and cannot leave the explicit workspace root.
        """

        workspace, start_directory = self._resolve_child(relative_path)
        if not start_directory.is_dir():
            raise WorkspaceError("Choose a directory to search inside the selected workspace.")
        normalized_query = query.strip().casefold()
        if not normalized_query:
            raise WorkspaceError("Enter a non-blank file or folder name to search.")

        result_limit = min(max(1, max_results), _MAX_SEARCH_RESULTS)
        pending: deque[Path] = deque([start_directory])
        visited_directories: set[Path] = {start_directory}
        results: list[WorkspaceEntry] = []
        scanned_directories = 0
        truncated = False

        while pending:
            if scanned_directories >= _MAX_SEARCH_DIRECTORIES:
                truncated = True
                break
            directory = pending.popleft()
            scanned_directories += 1
            try:
                # Do not materialise an unbounded directory listing: even a
                # name-only search must stay predictably small on a workspace
                # with generated dependencies or pathological directory trees.
                directory_entries: list[Path] = []
                with os.scandir(directory) as iterator:
                    for directory_entry in iterator:
                        if len(directory_entries) >= _MAX_SEARCH_DIRECTORY_ENTRIES:
                            truncated = True
                            break
                        directory_entries.append(Path(directory_entry.path))
                directory_entries.sort(key=lambda item: item.name.casefold())
            except OSError:
                # A disappearing/unreadable child should not broaden the search
                # or disclose a system-level error outside the selected root.
                continue

            result_limit_reached = False
            for entry in directory_entries:
                try:
                    # A filename convenience feature has no need to traverse a
                    # link. Skipping every symlink removes both escape and loop
                    # paths, including a link that could change during a scan.
                    if entry.is_symlink():
                        continue
                    resolved = entry.resolve(strict=True)
                    relative = resolved.relative_to(workspace.root)
                except (OSError, RuntimeError, ValueError):
                    # Exclude paths that race away from the selected root.
                    continue

                if resolved.is_dir():
                    if resolved not in visited_directories:
                        if len(visited_directories) >= _MAX_SEARCH_DIRECTORIES:
                            truncated = True
                        else:
                            visited_directories.add(resolved)
                            pending.append(resolved)
                    result = WorkspaceEntry(name=entry.name, relative_path=relative.as_posix(), kind="directory")
                elif resolved.is_file():
                    try:
                        size_bytes = resolved.stat().st_size
                    except OSError:
                        continue
                    result = WorkspaceEntry(
                        name=entry.name,
                        relative_path=relative.as_posix(),
                        kind="file",
                        size_bytes=size_bytes,
                    )
                else:
                    # Ignore devices, FIFOs, sockets and other special files.
                    continue

                if normalized_query in entry.name.casefold():
                    if len(results) >= result_limit:
                        truncated = True
                        result_limit_reached = True
                        break
                    results.append(result)
            if result_limit_reached:
                break

        return WorkspaceSearch(
            query=query.strip(),
            relative_path=start_directory.relative_to(workspace.root).as_posix(),
            results=results,
            scanned_directories=scanned_directories,
            truncated=truncated,
        )

    def analyze_text_file(self, relative_path: str) -> WorkspaceAnalysis:
        workspace, file_path = self._resolve_child(relative_path)
        if file_path.suffix.casefold() not in _TEXT_SUFFIXES:
            raise WorkspaceError("Igris read-only analysis supports common text and source files only.")

        # Open the already-confined path without following a last-moment symlink
        # on platforms that provide O_NOFOLLOW. O_NONBLOCK plus the regular-file
        # check avoids hanging on a FIFO/device swapped in after path resolution.
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        if hasattr(os, "O_NONBLOCK"):
            flags |= os.O_NONBLOCK
        descriptor: int | None = None
        try:
            descriptor = os.open(file_path, flags)
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise WorkspaceError("Choose a regular text file inside the selected workspace.")
            size_bytes = metadata.st_size
            with os.fdopen(descriptor, "rb") as file:
                descriptor = None
                raw = file.read(_MAX_ANALYSIS_BYTES + 1)
        except WorkspaceError:
            raise
        except OSError as error:
            raise WorkspaceError("That file could not be read safely inside the selected workspace.") from error
        finally:
            if descriptor is not None:
                os.close(descriptor)

        truncated = len(raw) > _MAX_ANALYSIS_BYTES
        raw = raw[:_MAX_ANALYSIS_BYTES]
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
        lines = text.splitlines()
        normalized = text.casefold()
        import_count = sum(
            line.lstrip().startswith(("import ", "from ", "require(", "use "))
            for line in lines
        )
        symbol_count = sum(
            line.lstrip().startswith(("def ", "class ", "function ", "export ", "fun ", "struct ", "interface "))
            for line in lines
        )
        return WorkspaceAnalysis(
            relative_path=file_path.relative_to(workspace.root).as_posix(),
            language=_LANGUAGE_BY_SUFFIX.get(file_path.suffix.casefold(), "Text"),
            size_bytes=size_bytes,
            line_count=len(lines),
            todo_count=normalized.count("todo"),
            fixme_count=normalized.count("fixme"),
            import_count=import_count,
            symbol_count=symbol_count,
            sha256=hashlib.sha256(raw).hexdigest(),
            truncated=truncated,
        )
