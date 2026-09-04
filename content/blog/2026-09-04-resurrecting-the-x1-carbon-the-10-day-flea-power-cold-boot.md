---
title: Resurrecting the X1 Carbon: The 10-Day Flea Power Cold Boot
date: 2026-09-04
description: Brief description of Resurrecting the X1 Carbon: The 10-Day Flea Power Cold Boot
tags: blog, linux, hardware
slug: resurrecting-the-x1-carbon-the-10-day-flea-power-cold-boot
---

## 01. introduction

A few weeks ago, I wrote an [untimely eulogy](https://binbot.dev/posts/the-brief-life-of-a-dialed-in-thinkpad.html) for my 6th Gen ThinkPad X1 Carbon after it died mid-compile and refused to power back on. The emergency reset pinhole did nothing, the charge indicator stayed completely dark, and it looked like the board had given up the ghost for good.

Turns out, it wasn't dead—it was locked in a hardware protection latch. During a heavy `./gradlew :app:assembleDebug` compile, the sudden burst power draw exceeded the supply threshold, tripping an over-current safety gate inside the USB-PD/BMS controller. Because tiny amounts of residual flea power kept the microcontroller's fault registers active, the machine refused to budge.

After sitting disconnected on a shelf for ten days, the quiescent draw finally drained every stray capacitor down to true zero. With the registers wiped clean, the protection latch dropped. I plugged it back in yesterday on a whim, the charging LED blinked to life, and it booted from scratch like nothing had ever happened.

### Tuning for Stability

To make sure a transient power surge doesn't trigger the BMS fail-safe again, I dialed in a few key adjustments:

* **Tamed Gradle:** Added conservative limits in `~/.gradle/gradle.properties` (`org.gradle.workers.max=2` alongside tighter JVM memory ceilings) to stop parallel build threads from pegging every core at maximum boost.
* **NixOS Power Packages:** Installed dedicated power-management packages and daemon profiles via Nix to keep wattage spikes and thermals capped under load.
* **BIOS Sleep States:** Adjusted the sleep settings in the BIOS to properly match the NixOS configuration, eliminating weird suspend quirks.

The laptop is running noticeably cooler, the battery is stretching further, and my trusty lightweight daily driver is officially back in service.

![Updated in all its glory](/media/screenshot_nix-pad.png)
*Updated in all its glory: fastfetch running cleanly on NixOS.*

