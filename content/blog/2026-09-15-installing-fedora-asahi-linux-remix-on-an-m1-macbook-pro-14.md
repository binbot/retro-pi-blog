---
title: Installing Fedora Asahi Linux Remix on an M1 MacBook Pro 14"
date: 2026-09-15
description: Brief description of Installing Fedora Asahi Linux Remix on an M1 MacBook Pro 14"
tags: blog, linux, fedora, mac, hardware
slug: installing-fedora-asahi-linux-remix-on-an-m1-macbook-pro-14
---

## 01. introduction

Running bare-metal Linux on Apple Silicon has come a long way, shifting from an experimental curiosity into a reliable daily workstation. I finally took the plunge and installed [**Fedora Asahi Linux Remix**](https://asahilinux.org/fedora/) on my 14-inch M1 MacBook Pro.

Overall verdict: it was noticeably easier than anticipated. That said, it definitely came with a couple of nail-biting pauses and display quirks worth documenting.

### The Installer Script & APFS Resizing

The installation kicks off directly inside macOS Terminal by running the official Asahi installer script. It guides you through analyzing your storage and carving out unallocated disk space for the Linux environment alongside macOS.

The APFS container resizing step was the real test of patience. Watching a terminal cursor sit on a disk partitioning operation is always a mild nail-biter, and it took about **25 minutes** to finish. If your screen seems frozen or unresponsive during the disk resizing phase, don't interrupt it—just let it cook, and it will finish successfully.

![Asahi Linux installer script running in macOS Terminal](/media/asahi_script_running1.jpg)

![Asahi installer script completing the APFS volume resize](/media/asahi_script_running2.jpg)

### First Boot & Startup Options

Once the script completes, you can't just perform a normal software reboot. The machine needs to be shut down completely:

1. Shut down the computer completely.
2. Press and **hold the Touch ID / power button** until the screen displays *"Loading startup options"*.
3. Choose the new **Fedora** option from the Apple boot picker to proceed to the initial OS setup.

![Apple Silicon bootloader screen showing boot options for Fedora, macOS, and Recovery](/media/apple_bootloader_options.jpg)
Before reaching the Fedora setup screen, though, you get hit with a scary-looking terminal authentication prompt from macOS asking to verify and bless the new boot volume.

![Scary macOS terminal authentication warning message before booting into Fedora](/media/mac_os_terminal_warning.jpg)
Once authenticated, the machine hands over execution to Linux.

### A Warning: High-DPI & Microscopic Setup Text

Once you reach the Fedora setup screen, get ready to squint.

Because display scaling hasn't been applied yet to the 14-inch MacBook Pro's native Liquid Retina XDR display (3024 × 1964), the text is *so* small it's practically impossible to read without magnification. Worse, you can't easily change the font or scaling until you finish the wizard and land at a prompt.

Be prepared to use a phone magnifier or lean right in while completing the initial setup (configuring your user, Wi-Fi credentials, SSH, and basic locale options).

Once you finally land at a shell prompt, bumping up the virtual console font size makes the display readable immediately:

![Screenshot of running the setfont command to enlarge the console font](/media/set_font_console_command.jpg)
With the user, Wi-Fi, and SSH configured, we cross the finish line into a working Linux system.

### Building from Minimal: Compositor & Applications

I opted for the **Fedora Minimal Install**. It comes with only the barest essentials—no pre-bundled desktop environment, no default graphical file manager, and no extra apps. I wanted to build the entire system up from scratch for the experience.

For the window manager and desktop shell, I chose:

* **Window Manager:** [niri](https://github.com/niri-wm/niri) – A scrollable-tiling Wayland compositor.
* **Desktop Shell:** [Noctalia Shell v5](https://github.com/noctalia-dev/noctalia) – A sleek, minimal desktop shell crafted specifically for Wayland that handles bars, docks, widgets, and notifications cohesively.

#### The Bare Essentials

On the application side, I kept things strictly limited to the tools I use daily:

* **Browsers:** Chrome Beta, Firefox
* **Chat:** Signal
* **Music Streaming:** Feishin
* **Task Manager:** Planify
* **Password Manager:** 1Password
* **System Monitor:** btop
* **Editor & Terminal:** Neovim and Foot

![Desktop showing the Noctalia Shell launcher dropdown menu](/media/desktop_launcher_dropdown.png)

#### Quality-of-Life Terminal Tools

I also brought over a set of fast, modern CLI utilities:

* `eza` (modern `ls`)
* `atuin` (shell history sync and search)
* `zoxide` (directory jumping)
* `tealdeer` (fast `tldr` implementation)
* `fuck` (*thefuck* command correction)
* `lazyvim` (modular Neovim setup)

### Final Thoughts

Cheers to a speedy, fresh Linux desktop running bare-metal on M1 Apple Silicon! The hardware support, snappiness, and battery efficiency make the minimal niri setup feel right at home on the MacBook Pro.

![Desktop with Foot terminal open displaying fastfetch system details on Fedora Asarhi Linux Remix](/media/desktop_fastfetch_asahi.png)


