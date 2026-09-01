---
title: The Brief Life of a Dialed-In ThinkPad
date: 2026-08-25
description: A lesson about attachments
tags: linux, nixos, thinkpad, hardware
slug: the-brief-life-of-a-dialed-in-thinkpad
---

## 01. introduction


A buddy handed down an X1 Carbon Gen 6 his office wasn't using anymore. Windows was sluggish on it, but it was a great candidate for a lightweight Linux setup.

I started with Ubuntu, but it felt heavy and kept getting in the way. With a little help from opencode and antigravity, I gave NixOS a shot instead. Once things clicked, it was great. I had a really minimal, fast setup running—Niri, Waybar, SwayOSD, and the fingerprint reader working without fuss. Declarative configs are addictive, and watching rebuilds finish cleanly was super satisfying.

![Desktop rice on NixOS](/media/nix_os.png)

Then it died mid-use.

The screen cut out while plugged in. No charging indicator, no fan, no response to hardware resets. Might be the motherboard, might be power delivery, but with no spare budget to throw at it right now, it sits configured on my desk doing nothing.

Felt pretty in tune with this scene the next day:

![Car with a tree on it](/media/tree_car.jpg)

The upside to declarative setups is that the machine is dead, but the config lives on in git. Whenever I get replacement hardware, it's just one rebuild command away.
