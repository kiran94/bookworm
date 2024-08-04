from enum import Enum


class Browser(str, Enum):
    BRAVE = "brave"
    CHROME = "chrome"


# Configuration for various browsers and details about them
# The bookmark_file_path is the path to the bookmarks file for the browsers, in order for it to be used it must be used in conjunction with
# os.path.expanduser as it may contain environment variables
#
# The platform configuration is keyed off the values from https://docs.python.org/3/library/sys.html#sys.platform
#
browsers = {
    Browser.BRAVE: {
        "linux": {"bookmark_file_path": "~/.config/BraveSoftware/Brave-Browser/Default/Bookmarks"},
        "win32": {},
        "darwin": {},
    },
    Browser.CHROME: {
        "linux": {"bookmark_file_path": "~/.config/google-chrome/Default/Bookmarks"},
        "win32": {},
        "darwin": {},
    },
}
