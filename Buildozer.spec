
[app]

title = Flappy Bird

package.name = flappybird
package.domain = org.rajgames

source.dir = .
source.include_exts = py,wav

version = 1.0

requirements = python3,kivy

orientation = portrait
fullscreen = 1

android.permissions = VIBRATE

android.api = 35
android.minapi = 23
android.archs = arm64-v8a

android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1
