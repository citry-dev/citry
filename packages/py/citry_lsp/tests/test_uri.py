from pathlib import PurePosixPath, PureWindowsPath

from citry_lsp.uri import _file_uri_pure_path


def test_windows_drive_file_uri_is_absolute_and_keeps_its_drive() -> None:
    path = _file_uri_pure_path("file:///C:/repo/My%20App/app.py", windows=True)

    assert path == PureWindowsPath("C:/repo/My App/app.py")
    assert path.drive == "C:"
    assert path.is_absolute()


def test_windows_localhost_drive_uri_stays_local() -> None:
    path = _file_uri_pure_path("file://localhost/C:/repo/caf%C3%A9.py", windows=True)

    assert path == PureWindowsPath("C:/repo/café.py")
    assert path.drive == "C:"
    assert path.is_absolute()


def test_windows_legacy_drive_authority_uri_stays_absolute() -> None:
    path = _file_uri_pure_path("file://C:/repo/app.py", windows=True)

    assert path == PureWindowsPath("C:/repo/app.py")
    assert path.drive == "C:"
    assert path.is_absolute()


def test_windows_unc_file_uri_keeps_its_authority() -> None:
    path = _file_uri_pure_path("file://server/share/pkg/app.py", windows=True)

    assert path == PureWindowsPath("//server/share/pkg/app.py")
    assert path.drive == "\\\\server\\share"
    assert path.is_absolute()


def test_windows_unc_file_uri_decodes_its_path() -> None:
    path = _file_uri_pure_path("file://build-server/shared/My%20App/app.py", windows=True)

    assert path == PureWindowsPath("//build-server/shared/My App/app.py")
    assert path.drive == "\\\\build-server\\shared"
    assert path.is_absolute()


def test_posix_file_uri_keeps_localhost_local_and_remote_authority_unc_like() -> None:
    assert _file_uri_pure_path("file://localhost/workspace/app.py", windows=False) == PurePosixPath(
        "/workspace/app.py"
    )
    assert _file_uri_pure_path("file://server/share/app.py", windows=False) == PurePosixPath("//server/share/app.py")


def test_non_file_uri_is_not_a_filesystem_path() -> None:
    assert _file_uri_pure_path("untitled:Untitled-1", windows=True) is None
    assert _file_uri_pure_path("https://example.com/app.py", windows=False) is None
