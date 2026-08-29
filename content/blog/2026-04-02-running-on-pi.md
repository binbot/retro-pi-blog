---
title: reviving an original 2012 raspberry pi
date: 2026-04-02
description: A guide/reflection on setting up a lightweight web server on the original Raspberry Pi Model B.
tags: hardware, linux, retro
slug: running-on-pi
---

## 01. the hardware in question

the original raspberry pi model b, released in 2012, features a single-core armv6 processor clocked at 700 MHz and a modest 512MB (or 256MB on earlier models) of RAM.

by modern standards, this is slower than a smart lightbulb. trying to boot a standard desktop GUI on this machine is an exercise in extreme patience.

## 02. repurposing as a server

however, a headless linux server has very low requirements. if we strip away the desktop environment and run a minimal distribution, we can do quite a lot.

here is the baseline recipe i used:

1. **OS:** Raspberry Pi OS Lite (headless, no desktop).
2. **Web Server:** Nginx (configured with micro-caching).
3. **Swap:** Turned off swap or moved it to a USB drive to protect the SD card from write cycles.
4. **Services:** Disabled unnecessary systemd services (like bluetooth, avahi-daemon, and triggerhappy).

## 03. performance metrics

with this setup, the pi sits at an idle memory consumption of just ~42MB. serving static HTML pages takes less than 1% CPU utilization per request. pages load in under 100ms when accessed locally, and under 500ms over WAN, bottlenecked only by residential DSL upload speeds.

it is a testament to the longevity of linux and the efficiency of simple protocols. we don't need new hardware; we need better-optimized software.
