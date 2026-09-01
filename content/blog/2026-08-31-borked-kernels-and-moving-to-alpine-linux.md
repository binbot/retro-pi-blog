---
title: Borked Kernels and Moving to Alpine Linux
date: 2026-08-31
description: Lessons on attachments, part two
tags: raspberry-pi, alpine-linux, self-hosting, hardware
slug: borked-kernels-and-moving-to-alpine-linux
---

## 01. introduction

Last night I went to update Debian Trixie on the Raspberry Pi. A kernel update failed mid-process, I rebooted without thinking, and the install broke completely.

The data was safe, so instead of restoring Debian, I decided to try Alpine Linux.

I knew nothing about Alpine going in. Using antigravity CLI to walk through it, we accidentally set it up to run in RAM only. It was fast, but every time I rebooted, the entire OS vanished. After restarting setup a few times, I realized what was happening, did a proper install to the SD card, and got persistent storage working.

![Bare metal worked](/media/on_the_sd.jpg)

Porting configs and services over took some patience, but it's finally back up and running.

![Alpine Linux fastfetch](/media/alpine.png)

The Pi hosts this site and handles the scripts that build the markdown files and pull in my Navidrome [listening history](https://binbot.dev/blog/#listening-log). Now that the server is stable again, I can finally start using the blog for actual posts instead of just placeholder text.

