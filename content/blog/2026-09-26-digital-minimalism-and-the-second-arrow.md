---
title: Digital Minimalism and the Second Arrow
date: 2026-09-26
description: Brief description of Digital Minimalism and the Second Arrow
tags: blog, linux, mac, yazi, minimalism, second_arrow
slug: digital-minimalism-and-the-second-arrow
---

## 01. introduction

I've been doing a lot of yoga this past year, and along with it came some meditation and reading. Something I came across recently that stuck with me is the [parable of the second arrow](https://e-buddhism.com/the-second-arrow/).

The idea is simple: if you get hit by an arrow, that's pain. It hurts, but it's already done. The second arrow is our reaction to it—the frustration, the dwelling on it, the mental spiral. Pain is inevitable, but suffering is not.

It feels a bit heavy to bring Buddhist parables into a blog about computers, or maybe like I'm making light of it, but it fits a lot of things. Even digital minimalism.

The other day I was transferring some field recordings to this machine, a minimal install of [Fedora Asahi Remix on an M1 MacBook Pro](http://binbot.dev/posts/installing-fedora-asahi-linux-remix-on-an-m1-macbook-pro-14.html). Right away, I ran into a couple of issues.

First: my file manager, [Yazi](https://yazi-rs.github.io), doesn't show mounted external drives in the sidebar like a traditional graphical file manager does. No big deal. I just hopped into `/run/` with Yazi, copied the files over, and dropped them into a new folder. Done.

Then came the next problem: I had no way to quickly preview the files.

I'm used to hitting spacebar to preview things—`gnome-sushi` on Linux, Quick Look on macOS. Yazi handles text, code, and even image previews right in the terminal, but it doesn't do audio playback out of the box.

Since I actually needed to hear what was on the card, I started looking around for workarounds. None of the options felt right. I could install `gnome-sushi`, but that pulls down a ton of GNOME dependencies and cruft I really don't want on a clean system. Or I could find a small, lightweight audio player. But even with TUI or CLI players, you're usually stuck adding extra repos or dealing with awkward dependency trees.

None of this is life-threatening, of course /smile. But nothing fit what I wanted, and I caught myself spending way too much time going down rabbit holes trying to find a pre-made fix.

So instead of continuing to get annoyed, I just built a quick script using stuff I already had on the system: `fzf` and everyone's friend, `#!/bin/bash`.

Enter `st`:

![screenshot of st running](/media/sound-triage.png)

It's an overdone, MrBeast-style "sound-triage" script. It lets me fuzzy-search and play files, plus it has quick helper actions to rename tracks and edit metadata on the fly. It took some time to piece together, but I learned a few things, and looking back it was actually fun to make.

In both of those spots where I took a hit from a digital arrow, I managed to sidestep the suffering part. Maybe it's just that once you learn about the parable, you start noticing it everywhere. Not sure.

Either way, computers are still fun :)

---


