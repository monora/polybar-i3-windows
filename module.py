#! /usr/bin/python3

import os
import asyncio
import getpass
import i3ipc
import platform
import re
from time import sleep

from icon_resolver import IconResolver

#: Max length of single window title
MAX_LENGTH = 10
#: Base 1 index of the font that should be used for icons
ICON_FONT = 3

HOSTNAME = platform.node()
USER = getpass.getuser()

ICONS = [
    ("class=Spotify", "\uf9c6"),
    ("class=Emacs", "\ue779"),
    ("class=firefox", "\ue745"),
    ("class=XTerm", "\ue795"),
    ("class=Code", "\ue70c"),
    ("class=code-oss-dev", "\ue70c"),
    ("class=Signal", "\uf70d"),
    ("*", "\uf2d0"),
]

FORMATERS = {
    "Chromium": lambda title: title.replace(" – Chromium", ""),
    "Firefox": lambda title: title.replace(" – Mozilla Firefox", ""),
    "Emacs": lambda title: title.replace(" – Doom Emacs", ""),
    "Xterm": lambda title: title.replace("%s@%s: " % (USER, HOSTNAME), ""),
}

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
COMMAND_PATH = os.path.join(SCRIPT_DIR, "command.py")

icon_resolver = IconResolver(ICONS)


def main():
    i3 = i3ipc.Connection()

    i3.on("workspace::focus", on_change)
    i3.on("window::focus", on_change)
    i3.on("window", on_change)

    loop = asyncio.get_event_loop()

    loop.run_in_executor(None, i3.main)

    render_apps(i3)

    loop.run_forever()


def on_change(i3, e):
    render_apps(i3)


def render_apps(i3):
    tree = i3.get_tree()
    apps = tree.leaves()
    apps.sort(key=lambda app: app.workspace().name)

    out = "%{O12}".join(format_entry(app) for app in apps)

    print(out, flush=True)


def format_entry(app):
    title = make_title(app)
    u_color = "#b4619a" if app.focused else "#e84f4f" if app.urgent else "#404040"

    return "%%{u%s} %s %%{u-}" % (u_color, title)


def make_title(app):
    out = get_prefix(app) + "  " + format_title(app)

    if app.focused:
        out = "%{F#fff}" + out + "%{F}"

    return "%%{A1:%s %s:}%s%%{A}" % (COMMAND_PATH, app.id, out)


def get_prefix(app):
    icon = icon_resolver.resolve(
        {
            "class": app.window_class,
            "name": app.name,
        }
    )

    return "%%{T%s}%s%%{T-}" % (ICON_FONT, icon)

def shorten_title(title):
    if len(title) > MAX_LENGTH:
        title = title[: MAX_LENGTH - 3] + "..."

    return title


def format_title(app):
    klass = app.window_class
    name = app.name

    for pattern, formatter in FORMATERS.items():
        if re.match(pattern, klass):
            return shorten_title(formatter(name))
    return shorten_title(name)


main()
