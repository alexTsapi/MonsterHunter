[app]
title = Monster Hunter
package.name = monsterhunter
package.domain = com.alextsapi
source.dir = .
source.include_exts = py,ttf
source.exclude_dirs = .github,bin,.buildozer
version = 1.0

# pygame για Android (κλειδωμένη έκδοση που δουλεύει σίγουρα)
requirements = python3,pygame
p4a.branch = v2023.09.16
p4a.bootstrap = sdl2

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png
android.presplash_color = #222E5C

orientation = landscape
fullscreen = 1
android.archs = arm64-v8a, armeabi-v7a
android.api = 33
android.minapi = 21
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 0
