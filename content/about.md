---
title: binbot ~ /about
status: load: nominal | connection: low-bandwidth
description: About binbot - a lightweight digital outpost hosted on a retro Raspberry Pi.
---

## 01. about this machine

welcome to **binbot**, a small digital outpost serving files directly from a vintage single-board computer sitting on a shelf.

by keeping web pages lightweight (under 10KB total load), avoiding complex frontend frameworks, and serving pre-rendered static content, this machine operates at extremely low power levels while maintaining sub-second page delivery.

## 02. physical configuration

<div style="text-align: center; margin: 1.5rem 0;">
  <img src="/media/retro_terminal.png" alt="Retro Terminal Artwork" style="max-width: 100%; height: auto; border: 1px solid var(--border-color); padding: 4px; background: var(--card-bg);" />
  <p class="text-muted" style="font-size: 0.8rem; margin-top: 0.5rem;">[fig 1.1: visualization of the local hosting console environment]</p>
</div>

this website is configured with Nginx optimized for static file delivery. static content is served directly from RAM caching rules, which minimizes reading requests from the micro-SD card and extends the physical lifespan of the server storage.

theme presets (Warm Paper, Dark Mode, Amber, and Green) allow you to view the server content using custom terminal retro color schemes. options are stored locally in your browser's session state.

## 03. external interfaces

- **version:** v2.1-lts
- **hosting:** raspberry pi OS lite
- **source:** vanilla HTML/CSS & zero-dependency JS
