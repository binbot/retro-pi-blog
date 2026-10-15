---
title: The Learning Curve of Self-hosting and a Half-Gigabyte Blog
date: 2026-10-15
description: Diagnosing an accidental 759 mb git folder, navigating the self-hosting learning curve, and wondering what happens when you force-push your own life.
tags: blog, linux, self-hosting, diy, git, web, codeberg
slug: the-learning-curve-of-self-hosting-and-a-half-gigabyte-blog
---

## 01. The Self-Hosting Learning Curve

When you get into self-hosting, you quickly realize it isn't just about spinning up a service and letting it run. It’s an ongoing series of small lessons, usually triggered by something quietly breaking behind the scenes. You think you’re just setting up a modest corner of the internet, but you’re actually signing up to maintain all the plumbing yourself.

A personal blog is supposed to be simple. A handful of Markdown files, a few static stylesheets, maybe some audio clips and photos of homemade bread. Yet a routine check on disk usage showed something wild: my blog repository had ballooned to over half a gigabyte.

At 759 MB, my first thought went straight to Codeberg.

Codeberg is a donation-backed, community-run non-profit for free and open-source software. They generously provide Codeberg Pages for static sites, but their terms clearly state that Codeberg is not a personal cloud locker, backup drive, or media dump. Their acceptable use policy has a 100 MB soft limit on personal repositories like blogs and dotfiles.

![A little on the heavy side](/media/on-the-heavy-side.png)

Pushing a 550 MB pile of files felt like a breach of good manners. GitHub has a 1 GB soft limit, but even there, stuffing huge image histories into Git guarantees friction down the road.

At first, moving my media to external cloud storage or setting up a bare Git repo on my Raspberry Pi crossed my mind as quick workarounds. But jumping to a new setup wouldn't tell me what was actually broken. Why had a site with barely 70 commits swelled into the size of a small operating system?

---

## 02. The Ghost in the Build Script

To see where the extra weight was hiding, I checked the actual site files against Git's hidden history folder:

* **Working files on disk:** ~70 MB (mostly images in `media/`)
* **`.git` folder:** **759 MB**

The live site wasn't the problem. The bloat was entirely in the history—invisible baggage piling up inside Git's storage files.

Digging into Git's history revealed the culprit: single JPEG files had over 100 saved versions. Every single deploy was re-saving and re-uploading the exact same photos:

```text
120 revisions: media/tree_car.jpg
120 revisions: media/on_the_sd.jpg
104 revisions: media/sliced.jpg
 96 revisions: media/aerial.jpg
```

Comparing the first and last versions showed zero visual difference. They were the exact same pictures. So why was Git saving a brand new copy every time I updated the site?

The answer was tucked away in `build.py`. To strip out camera data and location tags for privacy, the script had an automatic cleanup step:

```python
# The culprit in build.py:
for fname in os.listdir(media_dir):
    if fname.lower().endswith(valid_exts):
        subprocess.run(["magick", "mogrify", "-strip", fpath])
```

ImageMagick's `mogrify -strip` is great for removing EXIF and GPS data, but on JPEGs, it slightly rewrites the file header every single time it runs. Even if a photo was already cleaned yesterday, running `mogrify` today changed the file's digital fingerprint just enough to look brand new.

Pair that with `deploy.sh`:

```bash
python3 build.py
git add -A
git commit -m "chore(deploy): sync site build..."
git push origin main
```

Every time I deployed, the script re-saved all 39 images in `media/`, tricking Git into thinking every single picture had been edited. Across 61 deploys, that one harmless line of code added nearly half a gigabyte of duplicate photos to my Git history.

---

## 03. The Fix: Checking First and Cleaning Up History

Fixing this took two steps: stopping the script from re-saving clean photos, and clearing out the old duplicates.

### Step 1: Only Strip Metadata Once

In `build.py`, I updated the script to check if a photo actually had camera data before touching it:

```python
# Only strip if EXIF, IPTC, or XMP metadata actually exists
check = subprocess.run(
    ["magick", "identify", "-format", "%[exif:*]%[iptc:*]%[xmp:*]", fpath],
    capture_output=True, text=True
)
if check.stdout.strip():
    subprocess.run(["magick", "mogrify", "-strip", fpath], check=True)
```

Now, if an image has already been cleaned, ImageMagick leaves it alone. The file stays untouched, and Git ignores it on the next deploy.

### Step 2: Pruning the Old History

After making a full backup (`git bundle create backup.bundle --all`), I used `git-filter-repo` to clean out the old duplicate versions of `media/*` while keeping the current, clean copies.

The cleanup worked right away:
* `.git` dropped from 759 MB down to 70 MB (an 87% drop).
* Commit messages, dates, and text history stayed 100% intact.
* I didn't have to move any photos to external cloud storage, and my scripts (`deploy.sh`, `new-audio.sh`, `new-post.sh`) kept working without a hitch.

---

## 04. How to Recover on Other Machines (The Git Pull Trap)

If you ever rewrite Git history on a remote server, there is one major trap when moving to your other computers: never run `git pull`.

`git pull` doesn't mean "make my folder match the server." It actually downloads the server's changes and tries to merge them with what's already on your computer. Because rewriting history gives every past commit a brand new ID, Git looks at your computer and the server and sees two completely separate histories. If you run `git pull`:

1. Git merges the old bloated history with the new clean history.
2. Your computer keeps both, bringing all those 500 MB of duplicate files right back from the dead.
3. The next time you push, you accidentally re-upload all that bloat right back to Codeberg and GitHub.

### The Clean Way to Sync:

**Option A: Fresh Clone (Fastest)**  
Since the repo is only 70 MB now, downloading a fresh copy takes five seconds:

```bash
mv retro-pi-blog retro-pi-blog.old
git clone git@codeberg.org:binbot/retro-pi-blog.git
```

**Option B: Hard Reset**  
If you want to keep your existing folder and force it to match the server:

```bash
git fetch origin
git reset --hard origin/main
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

---

## 05. What If Life Had `git reset --hard`?

Watching `git-filter-repo` wipe out hundreds of megabytes of old mistakes made me wonder: what would life look like if humans had access to a force-push?

Imagine being able to clean up your own history. You could strip out that awkward comment you made at dinner in 2018, edit the timeline of a messy breakup so it looks like a clean mutual decision, or replace five years of questionable career detours with a tidy commit message: `chore(life): figuring things out`.

Your personal history would look spotless. Lightweight, fast, no heavy baggage dragging behind you.

But then comes the merge conflict.

In Git, history isn’t just yours—it exists on the computer of everyone who ever shared the project with you. If you rewrite your own past, everyone else is still walking around with the old version of you in their memory.

Imagine running into an old friend on the street:

* **You:** "Hey! Remember when we went camping a few years back?"
* **Friend:** "Wait, didn't you cancel that trip because your car broke down?"
* **You:** `error: update rejected. please force-pull my updated timeline.`

The social merge conflicts would be a mess:

```text
<<<<<<< HEAD (your updated timeline)
We parted ways respectfully with mutual admiration and no hard feelings.
=======
You threw a glass of orange juice across the kitchen and blocked my number.
>>>>>>> origin/reality
```

Who resolves that conflict? How do two people agree on what happened when one person edits their archive?

In the end, maybe Git gets it right. In version control, rewriting the past takes force, coordination, and getting everyone else to reset their copies too. In real life, we don't get `git-filter-repo`. We have to carry our full history—bloat, bad deploys, and all.

At least for this blog, though, 70 megabytes feels a whole lot lighter.

---

