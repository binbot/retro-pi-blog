---
title: building websites for old hardware
date: 2026-06-07
description: Why writing raw, lightweight HTML is a powerful design choice for vintage hardware.
tags: web, performance, self-hosting
slug: building-lightweight
---

## 01. the bloat of the modern web

the average web page today is several megabytes in size. between mega-sized javascript bundles, web trackers, heavy libraries, and massive auto-playing video banners, we've created a web that requires multi-gigahertz processors and gigabytes of RAM to render.

but does a personal blog or CV really need all of that?

## 02. raw simplicity is elegant

when you strip away the layers of abstraction and go back to raw HTML and simple CSS, magic happens:

- **instant rendering:** the page is parsed and rendered in milliseconds.
- **low bandwidth:** the entire transfer size is under 10KB (excluding media).
- **hardware longevity:** a single-board computer from 2012 can serve this page to dozens of visitors concurrently without breaking a sweat.

by adopting a retro-terminal or classic paper aesthetic, we turn limitations into a deliberate style choice. raw monospace fonts, simple borders, and ASCII art become features rather than compromises.

> "simplicity is the ultimate sophistication." &mdash; unknown

in future posts, i'll share my exact nginx configuration to ensure this raspberry pi remains secure and online 24/7.
