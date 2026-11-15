[app]
title = Luck Dice Offline
package.name = luckdiceoffline
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,ttf
source.exclude_dirs = bin,.buildozer,__pycache__
source.exclude_patterns = test_*.py
version = 1.0.0
requirements = python3,kivy==2.3.0,sqlite3
orientation = portrait
fullscreen = 0
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1

