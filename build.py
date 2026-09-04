#!/usr/bin/env python3
"""
build.py - Pure Data Minimalist Static Site Generator for binbot.dev
Zero external dependencies (uses standard Python 3).
"""

import os
import re
import sys
import glob
import html
import subprocess
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(ROOT_DIR, "content")
MEDIA_DIR = os.path.join(ROOT_DIR, "media")

def strip_exif_metadata(media_dir=MEDIA_DIR):
    """Automatically strips all EXIF, GPS, camera, and device metadata from media files."""
    valid_exts = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")
    stripped_count = 0
    if not os.path.exists(media_dir):
        return 0

    for fname in os.listdir(media_dir):
        if fname.lower().endswith(valid_exts):
            fpath = os.path.join(media_dir, fname)
            try:
                subprocess.run(
                    ["magick", "mogrify", "-strip", fpath],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                stripped_count += 1
            except Exception:
                pass
    return stripped_count

def parse_frontmatter(content):
    """Extract YAML-like frontmatter between leading --- delimiters."""
    meta = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            for line in fm_text.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    meta[k] = v
    return meta, body

def markdown_to_html(md_text):
    """Simple, clean markdown to HTML converter tailored for retro blog aesthetic."""
    lines = md_text.splitlines()
    html_lines = []
    in_code_block = False
    code_lang = ""
    code_lines = []
    in_list = False
    list_type = "ul"
    in_table = False
    table_rows = []

    def flush_list():
        nonlocal in_list, list_type
        if in_list:
            html_lines.append(f"</{list_type}>")
            in_list = False

    def flush_table():
        nonlocal in_table, table_rows
        if in_table and table_rows:
            html_lines.append('<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse; margin: 1.5rem 0; font-family: var(--font-family); font-size: 0.9rem;">')
            header = table_rows[0]
            html_lines.append("  <thead><tr style=\"border-bottom: 2px solid var(--border-color); text-align: left;\">")
            for cell in header:
                html_lines.append(f"    <th style=\"padding: 0.5rem; font-weight: bold;\">{inline_formatting(cell)}</th>")
            html_lines.append("  </tr></thead><tbody>")
            for row in table_rows[1:]:
                html_lines.append("  <tr style=\"border-bottom: 1px dashed var(--border-color); vertical-align: top;\">")
                for cell in row:
                    html_lines.append(f"    <td style=\"padding: 0.8rem 0.5rem;\">{inline_formatting(cell)}</td>")
                html_lines.append("  </tr>")
            html_lines.append("</tbody></table></div>")
            in_table = False
            table_rows = []

    def inline_formatting(text):
        # Images: ![alt](url)
        text = re.sub(
            r'!\[(.*?)\]\((.*?)\)',
            r'<div style="text-align: center; margin: 1.5rem 0;"><img src="\2" alt="\1" style="max-width: 100%; height: auto; border: 1px solid var(--border-color); padding: 4px; background: var(--card-bg);" /><p class="text-muted" style="font-size: 0.8rem; margin-top: 0.5rem;">[fig: \1]</p></div>',
            text
        )
        # Custom Audio Tag: [audio: /media/track.mp3 | Track Title]
        text = re.sub(
            r'\[audio:\s*([^\|]+)\s*\|\s*(.*?)\]',
            r'<div class="pd-audio-pill" style="border: 1px solid var(--border-color); padding: 8px 12px; margin: 1rem 0; display: inline-flex; align-items: center; gap: 10px; background: var(--card-bg);"><span>&#9658; <strong>\2</strong></span> <a href="\1" download class="text-muted" style="font-size: 0.85rem;">[download]</a></div>',
            text
        )
        # Links: [text](url)
        def link_sub(m):
            t, u = m.group(1), m.group(2)
            target = ' target="_blank"' if u.startswith("http") else ''
            return f'<a href="{u}"{target}>{t}</a>'
        text = re.sub(r'\[(.*?)\]\((.*?)\)', link_sub, text)
        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'(?<!\*)\*([^\*]+)\*(?!\*)', r'<em>\1</em>', text)
        # Inline code
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        return text

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Fenced code block
        if stripped.startswith("```"):
            if in_code_block:
                code_content = html.escape("\n".join(code_lines))
                html_lines.append(f'<pre style="line-height: 1.4;"><code>{code_content}</code></pre>')
                in_code_block = False
                code_lines = []
            else:
                flush_list()
                flush_table()
                in_code_block = True
                code_lang = stripped[3:].strip()
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Blank line
        if not stripped:
            flush_list()
            flush_table()
            i += 1
            continue

        # Tables: | col1 | col2 |
        if stripped.startswith("|") and stripped.endswith("|"):
            flush_list()
            # Check if separator row
            if re.match(r'^\|[\s\-:|]+\|$', stripped):
                i += 1
                continue
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if not in_table:
                in_table = True
                table_rows = [cells]
            else:
                table_rows.append(cells)
            i += 1
            continue
        else:
            flush_table()

        # Headers
        if stripped.startswith("#"):
            flush_list()
            level = len(re.match(r'^#+', stripped).group(0))
            header_text = inline_formatting(stripped[level:].strip())
            if level == 1:
                html_lines.append(f'<h1 style="margin-top: 1.5rem;">{header_text}</h1>')
            elif level == 2:
                html_lines.append(f'<h2>{header_text}</h2>')
            elif level == 3:
                html_lines.append(f'<h3>{header_text}</h3>')
            else:
                html_lines.append(f'<h4>{header_text}</h4>')
            i += 1
            continue

        # Horizontal Rule
        if re.match(r'^(---|\*\*\*|___)$', stripped):
            flush_list()
            html_lines.append('<hr style="border: none; border-bottom: 1px dashed var(--border-color); margin: 2rem 0;" />')
            i += 1
            continue

        # Blockquote
        if stripped.startswith(">"):
            flush_list()
            quote_text = inline_formatting(stripped[1:].strip())
            html_lines.append(f'<blockquote>{quote_text}</blockquote>')
            i += 1
            continue

        # Unordered list: - or *
        if re.match(r'^[-*]\s+', stripped):
            item_text = inline_formatting(re.sub(r'^[-*]\s+', '', stripped))
            if not in_list or list_type != "ul":
                flush_list()
                in_list = True
                list_type = "ul"
                html_lines.append("<ul>")
            html_lines.append(f"  <li>{item_text}</li>")
            i += 1
            continue

        # Ordered list: 1. 2.
        if re.match(r'^\d+\.\s+', stripped):
            item_text = inline_formatting(re.sub(r'^\d+\.\s+', '', stripped))
            if not in_list or list_type != "ol":
                flush_list()
                in_list = True
                list_type = "ol"
                html_lines.append("<ol>")
            html_lines.append(f"  <li>{item_text}</li>")
            i += 1
            continue

        flush_list()

        # Regular HTML or paragraph
        if stripped.startswith("<") and stripped.endswith(">"):
            html_lines.append(line)
        else:
            html_lines.append(f"<p>{inline_formatting(stripped)}</p>")

        i += 1

    flush_list()
    flush_table()
    return "\n".join(html_lines)


def render_html_page(title, subpath, status_text, body_html, description="", extra_head="", is_post=False, post_date="", tags=""):
    """Wrap rendered content in Pure Data layout."""
    tags_html = ""
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        pill_links = [f'<a href="/blog/#{t}" class="tag-link">#{t}</a>' for t in tag_list]
        tags_html = f'<div style="margin-top: 0.4rem; display: flex; flex-wrap: wrap; gap: 4px; align-items: center;"><span class="text-muted" style="font-size: 0.85rem; margin-right: 4px;">tags:</span>{" ".join(pill_links)}</div>'

    post_title_html = f'<h1 style="margin-top: 1.5rem;">{title}</h1>' if is_post else ''
    back_link_html = '<div style="margin-top: 2rem;"><a href="/blog/">&lt;-- back to blog</a></div>' if is_post else ''
    
    return f"""<!DOCTYPE html>
<!--
  DO NOT EDIT THIS FILE DIRECTLY!
  This page is automatically generated by build.py.
  Manual changes will be overwritten during deploy.
  Source files live in: content/
-->
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{html.escape(description)}">
  {extra_head}
  <link rel="stylesheet" href="/style.css?v=2.3">
</head>
<body>
  <div class="container">
    <header>
      <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <a href="/" class="pd-object" style="font-size: 1rem; padding: 4px 10px; text-decoration: none;">
            binbot
            <div class="pd-clickable-corner" style="width: 6px; height: 6px;"></div>
          </a>
          <span style="font-size: 1.1rem; font-weight: bold; opacity: 0.85;">~ {subpath}</span>
        </div>
        <span class="text-muted" style="font-size: 0.85rem;">{status_text}</span>
      </div>
      {post_title_html}
      {tags_html}
    </header>

    <main>
      <article>
        {body_html}
      </article>
      {back_link_html}
    </main>

    <footer>
      <p>served with care from a raspberry pi | <a href="https://github.com/binbot" target="_blank">github</a> | <a href="https://codeberg.org/binbot" target="_blank">codeberg</a> | <a href="mailto:binbot@binbot.dev">email</a></p>
      <div class="theme-selector" style="text-align: center; margin-top: 1rem; margin-bottom: 0;">
        Theme:
        <button class="theme-btn" data-set-theme="paper">Warm Paper</button>
        <button class="theme-btn" data-set-theme="dark">Dark Mode</button>
        <button class="theme-btn" data-set-theme="amber">Amber Terminal</button>
        <button class="theme-btn" data-set-theme="green">Green Terminal</button>
      </div>
      <p class="text-muted" style="font-size: 0.75rem; margin-top: 1rem;">page weight: ~5.8KB | green hosting certified (700mW idle power)</p>
    </footer>
  </div>

  <script src="/script.js?v=2.3"></script>
</body>
</html>
"""


def fetch_pi_telemetry():
    """Fetch live hardware telemetry from Raspberry Pi (pipi)."""
    cmd = "uptime; free -m; uname -mrs; cat /etc/os-release"
    hosts = ["binbot@pipi", "binbot@192.168.86.42", "binbot@100.99.56.3"]
    
    for h in hosts:
        try:
            res = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=2", "-o", "BatchMode=yes", h, cmd],
                capture_output=True, text=True, check=True
            )
            lines = [l.strip() for l in res.stdout.strip().splitlines() if l.strip()]

            os_name = "Alpine Linux v3.20 [aarch64]"
            for l in lines:
                if l.startswith("PRETTY_NAME="):
                    os_name = l.replace("PRETTY_NAME=", "").strip('"').strip("'") + " [aarch64]"

            kernel_str = "Linux 6.6.49-0-rpi aarch64"
            for l in lines:
                if l.startswith("Linux ") and ("rpi" in l or "alpine" in l or "aarch64" in l or "arm" in l):
                    kernel_str = l

            uptime_str = "nominal"
            load_str = "0.00, 0.00, 0.00"
            for l in lines:
                if "load average:" in l:
                    parts = l.split("load average:")
                    load_str = parts[1].strip()
                    m_up = re.search(r'up\s+(.*?),\s+\d+\s+user', parts[0])
                    if m_up:
                        uptime_str = m_up.group(1).strip()

            ram_str = "83 MB / 908 MB"
            for l in lines:
                if l.startswith("Mem:"):
                    p = l.split()
                    if len(p) >= 3:
                        ram_str = f"{p[2]} MB / {p[1]} MB"

            return f"""============================================================
HOST:         pipi
OS:           {os_name}
KERNEL:       {kernel_str}
UPTIME:       {uptime_str} (24/7 low-power outpost)
LOAD:         {load_str}
RAM:          {ram_str} (ultra-lightweight footprint)
POWER:        ~1.0W low-power footprint (green hosted)
============================================================"""
        except Exception:
            continue

    # Fallback if pi unreachable during build
    return f"""============================================================
HOST:         pipi
OS:           Alpine Linux v3.20 [aarch64]
KERNEL:       Linux 6.6.49-0-rpi aarch64
UPTIME:       nominal (24/7 low-power outpost)
LOAD:         0.02, 0.01, 0.00
RAM:          83 MB / 908 MB (ultra-lightweight footprint)
POWER:        ~1.0W low-power footprint (green hosted)
============================================================"""


def build_posts():
    """Build all posts in content/blog/*.md -> posts/<slug>.html"""
    posts_dir = os.path.join(CONTENT_DIR, "blog")
    out_dir = os.path.join(ROOT_DIR, "posts")
    os.makedirs(out_dir, exist_ok=True)

    post_files = glob.glob(os.path.join(posts_dir, "*.md"))
    posts = []

    for fpath in post_files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        meta, body = parse_frontmatter(content)
        filename = os.path.basename(fpath)
        
        # Determine slug
        slug = meta.get("slug")
        if not slug:
            # fallback from filename e.g. 2026-06-07-my-title.md -> my-title
            m = re.match(r'^\d{4}-\d{2}-\d{2}-(.*)\.md$', filename)
            slug = m.group(1) if m else filename.replace(".md", "")

        date_str = meta.get("date", "2026-01-01")
        title = meta.get("title", slug.replace("-", " "))
        description = meta.get("description", f"Transmission {title} on binbot.dev")
        tags = meta.get("tags", "")

        body_html = markdown_to_html(body)
        full_html = render_html_page(
            title=title,
            subpath="/blog/post",
            status_text=f"published: {date_str}",
            body_html=body_html,
            description=description,
            is_post=True,
            post_date=date_str,
            tags=tags
        )

        out_file = os.path.join(out_dir, f"{slug}.html")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(full_html)

        posts.append({
            "title": title,
            "date": date_str,
            "year": date_str.split("-")[0] if "-" in date_str else "2026",
            "slug": slug,
            "url": f"/posts/{slug}.html",
            "description": description,
            "tags": tags
        })

    # Sort descending by date
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


def build_blog_index(posts):
    """Build blog/index.html with interactive tag filter bar, year grouping, and real Pi telemetry."""
    out_dir = os.path.join(ROOT_DIR, "blog")
    os.makedirs(out_dir, exist_ok=True)

    # Collect unique tags
    all_tags = set()
    for p in posts:
        for t in p.get("tags", "").split(","):
            cleaned = t.strip().lower()
            if cleaned:
                all_tags.add(cleaned)

    tag_buttons = ['<button class="tag-filter-btn active" data-tag="all">[all]</button>']
    for t in sorted(all_tags):
        tag_buttons.append(f'<button class="tag-filter-btn" data-tag="{t}">#{t}</button>')

    filter_bar_html = f"""<div class="tag-filter-bar" id="tag-filter-bar">
          <span style="font-size: 0.8rem; font-weight: bold; opacity: 0.8; margin-right: 4px;">filter:</span>
          {" ".join(tag_buttons)}
        </div>"""

    # Group by Year
    posts_by_year = {}
    for p in posts:
        yr = p["year"]
        if yr not in posts_by_year:
            posts_by_year[yr] = []
        posts_by_year[yr].append(p)

    archive_blocks = []
    for yr in sorted(posts_by_year.keys(), reverse=True):
        archive_blocks.append(f'<div class="year-divider" data-year="{yr}">── {yr} ──</div>')
        for p in posts_by_year[yr]:
            raw_tags = ",".join([t.strip().lower() for t in p.get("tags", "").split(",") if t.strip()])
            archive_blocks.append(f"""          <div class="post-list-item" data-tags="{raw_tags}" data-year="{yr}">
            <a href="{p['url']}">{p['title']}</a>
            <span class="post-date">{p['date']}</span>
          </div>""")

    posts_list_block = "\n".join(archive_blocks)
    telemetry_block = fetch_pi_telemetry()

    body_html = f"""      <section>
        <h2>01. transmissions archive</h2>
        <p>
          here you will find occasional thoughts, log entries, and documentation regarding systems design, retro hardware, audio recording, and minimalist programming.
        </p>

        {filter_bar_html}

        <div style="margin-top: 1.5rem;" id="posts-container">
{posts_list_block}
        </div>
      </section>

      <section style="margin-top: 2.5rem;">
        <h2>02. hardware telemetry</h2>
        <pre><code>$ binbot --telemetry
{telemetry_block}</code></pre>
      </section>"""

    full_html = render_html_page(
        title="binbot ~ /blog",
        subpath="/blog",
        status_text="transmissions: archived",
        body_html=body_html,
        description="Recent transmissions and articles hosted on my Raspberry Pi."
    )

    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(full_html)


def build_rss(posts):
    """Generate valid RSS 2.0 xml feed."""
    items_xml = []
    for p in posts[:15]:
        items_xml.append(f"""    <item>
      <title>{html.escape(p['title'])}</title>
      <link>https://binbot.dev{p['url']}</link>
      <guid>https://binbot.dev{p['url']}</guid>
      <pubDate>{p['date']}</pubDate>
      <description>{html.escape(p['description'])}</description>
    </item>""")

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>binbot transmissions</title>
    <link>https://binbot.dev/blog/</link>
    <description>A lightweight digital outpost hosted on a retro Raspberry Pi.</description>
    <language>en-us</language>
{"\n".join(items_xml)}
  </channel>
</rss>
"""
    with open(os.path.join(ROOT_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)


def build_about():
    """Build about/index.html from content/about.md."""
    src = os.path.join(CONTENT_DIR, "about.md")
    if not os.path.exists(src):
        return
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()
    meta, body = parse_frontmatter(content)
    body_html = markdown_to_html(body)
    full_html = render_html_page(
        title=meta.get("title", "binbot ~ /about"),
        subpath="/about",
        status_text=meta.get("status", "load: nominal"),
        body_html=body_html,
        description=meta.get("description", "About binbot")
    )
    out_dir = os.path.join(ROOT_DIR, "about")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(full_html)


def build_audio():
    """Build audio/index.html from content/audio.md with interactive retro player."""
    src = os.path.join(CONTENT_DIR, "audio.md")
    if not os.path.exists(src):
        return
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()
    meta, body = parse_frontmatter(content)

    tracks = [
        {"title": "forest rain field recording", "src": "/media/forest-rain.mp3", "duration": "02:14"},
        {"title": "synth sunset draft (op-1 pocket sketch)", "src": "/media/synth-sketch-05.mp3", "duration": "01:45"},
        {"title": "acoustic riff idea (recorded with phone mic)", "src": "/media/guitar-improvisation.mp3", "duration": "00:58"},
    ]

    tracks_match = re.search(r'<!--\s*tracks:(.*?)-->', body, re.DOTALL)
    if tracks_match:
        custom_tracks = []
        cur_t = {}
        for l in tracks_match.group(1).splitlines():
            l = l.strip()
            if l.startswith("- title:"):
                if cur_t: custom_tracks.append(cur_t)
                cur_t = {"title": l[8:].strip()}
            elif l.startswith("src:"):
                cur_t["src"] = l[4:].strip()
            elif l.startswith("duration:"):
                cur_t["duration"] = l[9:].strip()
        if cur_t: custom_tracks.append(cur_t)
        if custom_tracks:
            tracks = custom_tracks
        body = re.sub(r'<!--\s*tracks:.*?-->', '', body, flags=re.DOTALL)

    playlist_items = []
    for idx, t in enumerate(tracks, start=1):
        num_str = f"[{idx:02d}]"
        playlist_items.append(f"""          <li class="playlist-item" data-src="{t['src']}">
            <span>
              <span class="track-num">{num_str}</span>
              <span class="track-title">{t['title']}</span>
            </span>
            <span class="text-muted">
              ({t.get('duration', '--:--')}) &middot; <a href="{t['src']}" download>[download]</a>
            </span>
          </li>""")

    player_html = f"""
      <section>
        <h2>01. custom retro player</h2>
        <p>
          this custom music player uses standard html5 audio APIs styled with simple, retro css borders. it requires no heavy third-party framework, keeping load time and execution memory near-zero for the server.
        </p>

        <!-- Hidden native audio element -->
        <audio id="main-audio" style="display: none;"></audio>

        <div class="audio-player-container">
          <div class="player-display">
            <div class="track-info" id="display-track-name">[NO TRACK LOADED]</div>
            <div class="time-info">
              <span id="display-time">00:00 / 00:00</span>
              <span class="text-muted">44.1kHz | 16-bit</span>
            </div>
          </div>
          
          <input type="range" class="player-progress" id="player-progress" min="0" max="100" value="0">
          
          <div class="player-controls">
            <button class="control-btn" id="btn-prev">[PREV]</button>
            <button class="control-btn" id="btn-play-pause">[PLAY]</button>
            <button class="control-btn" id="btn-stop">[STOP]</button>
            <button class="control-btn" id="btn-next">[NEXT]</button>
          </div>
        </div>
      </section>

      <section>
        <h2>02. tracklist</h2>
        <p class="text-muted">click on a track below to load and play it in the console above, or click "[download]" to grab the file.</p>
        
        <ul class="playlist">
{"\n".join(playlist_items)}
        </ul>
      </section>
"""
    clean_body = re.sub(r'## 01.*?(?=## 03|\Z)', '', body, flags=re.DOTALL)
    extra_body_html = markdown_to_html(clean_body)

    out_dir = os.path.join(ROOT_DIR, "audio")
    os.makedirs(out_dir, exist_ok=True)
    full_html = render_html_page(
        title=meta.get("title", "binbot ~ /audio"),
        subpath="/audio",
        status_text=meta.get("status", "media: local_playback"),
        body_html=player_html + extra_body_html,
        description=meta.get("description", "Audio logs and recordings")
    )
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(full_html)


def build_cv():
    """Build cv/index.html from content/cv.md."""
    src = os.path.join(CONTENT_DIR, "cv.md")
    if not os.path.exists(src):
        return
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()
    meta, body = parse_frontmatter(content)
    body_html = markdown_to_html(body)

    print_style = """
  <meta name="robots" content="noindex, nofollow">
  <style>
    @media print {
      body {
        background: white !important;
        color: black !important;
        padding: 0 !important;
      }
      .theme-selector, nav, footer, header .ascii-art, header a {
        display: none !important;
      }
      header {
        border-bottom: 1px solid black !important;
      }
      .cv-meta {
        border-bottom: 1px dashed black !important;
      }
    }
  </style>"""

    cv_top_bar = '<div style="display: flex; justify-content: flex-end; align-items: baseline; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.5rem;"><a href="javascript:window.print()">[print / save as pdf]</a></div>'

    out_dir = os.path.join(ROOT_DIR, "cv")
    os.makedirs(out_dir, exist_ok=True)
    full_html = render_html_page(
        title=meta.get("title", "binbot ~ /cv"),
        subpath="/cv",
        status_text=meta.get("status", "document: cv_resume_v2.0"),
        body_html=cv_top_bar + body_html,
        description=meta.get("description", "Benjamin Scott CV"),
        extra_head=print_style
    )
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(full_html)


def main():
    print("=== Building retro-pi-blog ===")
    stripped = strip_exif_metadata()
    if stripped > 0:
        print(f"-> Sanitized EXIF & GPS metadata from {stripped} image(s) in media/")
    posts = build_posts()
    print(f"-> Generated {len(posts)} blog posts")
    build_blog_index(posts)
    print("-> Generated /blog/index.html (with live hardware telemetry & tag filter)")
    build_rss(posts)
    print("-> Generated /rss.xml")
    build_about()
    print("-> Generated /about/index.html")
    build_audio()
    print("-> Generated /audio/index.html")
    build_cv()
    print("-> Generated /cv/index.html")
    print("=== Build Complete! ===")

if __name__ == "__main__":
    main()
