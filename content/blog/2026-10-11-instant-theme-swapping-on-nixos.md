---
title: Instant Theme Swapping on NixOS
date: 2026-10-11
description: Using flavours for Instant Theme Swapping on NixOS
tags: blog, rice, nixos, linux, hardware
slug: instant-theme-swapping-on-nixos
---

## 01. introduction

It's so easy for me to lose an evening tweaking terminal colors instead of getting anything done.

I run a minimal NixOS setup on my ThinkPad with the Niri tiling compositor. The trouble with NixOS for tweaking visuals is the rebuild cycle. You tweak a color value, rebuild the system, wait a minute or so, and by then whatever thought you had in your head is gone.

I just wanted to hit a key, pick a theme, and have the whole screen update instantly.

---

## Separating the OS from the Colors

NixOS manages the packages and system configs, but I let a little tool called [Flavours](https://github.com/Misterio77/flavours) handle theme switching at runtime.

To keep things clean, Flavours doesn't touch my actual config files. It just writes out tiny, dedicated color files that my apps import:

* **Waybar and SwayOSD** import `colors.css`
* **Foot** terminal imports `theme.ini`
* **Niri** imports `colors.kdl` for window borders
* **Rofi, Qutebrowser, and Hyprlock** pull in their own small theme files

Hit `Mod+Shift+T`, pick a theme from Rofi (Kanagawa, Gruvbox, Nord, Tokyo Night, etc.), and everything updates immediately. Waybar repaints, Foot flips colors, and the window borders change with zero downtime.

![The Rofi theme chooser menu ready to select a palette](/media/shift+super+t.png)

---

## Fixing Waybar and Light Mode

Once the colors worked, a few small details needed attention:

* **Dark and light switching:** A small hook checks the brightness of the theme's background color. If it's a light theme, it tells the system to prefer light mode so Chrome and GTK apps adapt cleanly instead of staying dark.
* **Waybar drift:** My clock kept moving around because the media player was sharing the center of the bar. I moved media controls to the left and locked the center down to a single pill with just the weather and the time.
* **Weather icons:** White cloud emojis were invisible on light backgrounds. I switched to Nerd Font weather icons tinted with the theme's accent color so they stay visible on any background.

![Desktop switched over to the Rosé Pine light theme](/media/rose_pine_light.png)

---

## What Broke Along the Way

A couple of quick fixes were needed during setup:

1. Some newer Base16 themes (like Kanagawa and Everforest) use a format Flavours didn't like, so I converted the files back to classic Base16 YAML.
2. Waybar crashed when using standard CSS `:empty` to hide the active window pill when no windows were open. GTK CSS doesn't support that, so I used Waybar's built-in `#window.empty` class instead.
3. Updated the Foot terminal template to silence warnings about deprecated color sections.

![Desktop running the Nord theme with updated terminal and bar](/media/nord_theme.png)

---

Now when I want a change of scenery, a quick shortcut switches the whole desktop in a fraction of a second, and I can get right back to what I was actually trying to do.
