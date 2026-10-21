"""Generate reel/index.html from the edit decision list (EDL)."""
import json, sys

OUT = sys.argv[1]

# id, source in, source out, zoom from, zoom to, caption chunks (*word* = highlight)
EDL = [
    ("h1", 18.98, 20.96, 1.22, 1.30, ["Kepada para *belia*", "di luar sana,", "marilah"]),
    ("h2", 21.56, 22.70, 1.45, 1.50, ["kita *bersama-sama*"]),
    ("a", 1.86, 4.28, 1.00, 1.05, ["Assalamualaikum", "warahmatullahi", "wabarakatuh"]),
    ("b", 4.92, 7.20, 1.15, 1.18, ["Hari ini saya", "berkesempatan bertemu", "dengan"]),
    ("c", 8.24, 9.90, 1.02, 1.04, ["barisan kepimpinan", "*PRISMA*"]),
    ("d", 10.48, 14.48, 1.10, 1.18, ["Dan saya mendoakan", "agar *PRISMA*", "akan terus *cemerlang*", "dalam memperjuangkan"]),
    ("e", 15.04, 16.42, 1.32, 1.34, ["akan *hak-hak belia*"]),
    ("f", 16.66, 18.32, 1.06, 1.08, ["dan juga negara", "secara keseluruhannya"]),
    ("g", 23.10, 26.96, 1.00, 1.07, ["Dan saya mendoakan", "kalian akan menjadi", "sebahagian daripada", "kekuatan *PRISMA*"]),
    ("h", 27.48, 29.06, 1.22, 1.24, ["dalam membawa", "wadah *perjuangan*"]),
    ("i", 29.50, 30.92, 1.06, 1.08, ["yang akan", "membela *nasib*"]),
    ("j", 31.16, 32.94, 1.00, 1.03, ["seluruh *rakyat Malaysia*,", "khususnya"]),
    ("k", 33.18, 34.16, 1.28, 1.30, ["*belia* di Malaysia."]),
    ("l", 34.50, 35.26, 1.12, 1.14, ["Salam *perjuangan*."]),
]
END_CARD = 2.2

segs, t = [], 0.0
for sid, a, b, z0, z1, chunks in EDL:
    d = round(b - a, 2)
    segs.append(dict(id=sid, src=a, start=round(t, 2), dur=d, z0=z0, z1=z1, chunks=chunks))
    t += d
SPEECH_END = round(t, 2)
TOTAL = round(SPEECH_END + END_CARD, 2)

# Caption groups: chunks share a segment's time in proportion to their length.
groups = []
for s in segs:
    total_chars = sum(len(c.replace("*", "")) + 4 for c in s["chunks"])
    cur = s["start"]
    for c in s["chunks"]:
        d = s["dur"] * (len(c.replace("*", "")) + 4) / total_chars
        groups.append(dict(text=c, start=round(cur, 2), end=round(cur + d, 2), seg=s["id"]))
        cur += d


def seg(sid):
    return next(s for s in segs if s["id"] == sid)


def group_start(sid, idx):
    return [g for g in groups if g["seg"] == sid][idx]["start"]


# Keyword callouts: (id, text, accent, start, end, sfx)
CALLOUTS = [
    ("co-belia", "BELIA", "yellow", 0.25, 1.95, None),
    ("co-mari", "MARI BERSAMA!", "red", 1.98, 3.05, "impact"),
    ("co-cemerlang", "CEMERLANG", "yellow", group_start("d", 2) + 0.35, seg("d")["start"] + seg("d")["dur"] - 0.1, "sparkle"),
    ("co-hak", "HAK-HAK BELIA", "red", seg("e")["start"] + 0.2, seg("e")["start"] + seg("e")["dur"], "impact"),
    ("co-kekuatan", "KEKUATAN PRISMA", "yellow", group_start("g", 3), seg("g")["start"] + seg("g")["dur"], "impact"),
    ("co-wadah", "WADAH PERJUANGAN", "red", group_start("h", 1), seg("h")["start"] + seg("h")["dur"], "whoosh"),
    ("co-rakyat", "SELURUH RAKYAT MALAYSIA", "yellow", seg("j")["start"] + 0.15, seg("j")["start"] + seg("j")["dur"], "pop"),
    ("co-khusus", "KHUSUSNYA BELIA", "red", seg("k")["start"], seg("k")["start"] + seg("k")["dur"], "pop"),
]
LOWER_THIRD = (seg("b")["start"] + 0.3, seg("c")["start"] + seg("c")["dur"] - 0.05)


def caption_html(text):
    parts, out = text.split("*"), []
    for i, p in enumerate(parts):
        if not p:
            continue
        out.append(f'<span class="hl">{p}</span>' if i % 2 else p)
    return "".join(out)


videos = "\n".join(
    f'''      <div id="cam-{s["id"]}" class="cam">
        <video id="v-{s["id"]}" class="clip" src="raw.mp4" playsinline data-has-audio="true"
          data-start="{s["start"]}" data-duration="{s["dur"]}" data-media-start="{s["src"]}" data-track-index="0"></video>
      </div>'''
    for s in segs
)

captions = "\n".join(
    f'        <div id="cg-{i}" class="cg"><span class="cg-text">{caption_html(g["text"])}</span></div>'
    for i, g in enumerate(groups)
)

callouts = "\n".join(
    f'        <div id="{cid}" class="co co-{acc}"><span class="co-bar"></span><span class="co-text">{txt}</span></div>'
    for cid, txt, acc, *_ in CALLOUTS
)

# SFX placements: (file, timeline time of the hit, peak offset in file, duration, volume)
SFX_FILES = {
    "impact": ("assets/sfx/impact-bass-1.mp3", 0.07, 1.6, 0.45),
    "sparkle": ("assets/sfx/sparkle.mp3", 0.03, 1.5, 0.35),
    "whoosh": ("assets/sfx/whoosh-short.mp3", 0.16, 0.57, 0.45),
    "pop": ("assets/sfx/pop.mp3", 0.12, 0.6, 0.4),
}
sfx = []
for cid, _txt, _acc, st, _en, kind in CALLOUTS:
    if kind:
        sfx.append((f"sfx-{cid}", kind, st))
# Transitions: whoosh into the salam after the hook, and into the end card.
sfx.append(("sfx-trans-hook", "whoosh", seg("a")["start"]))
sfx.append(("sfx-lower-third", "pop", LOWER_THIRD[0]))
sfx.append(("sfx-endcard-in", "whoosh", SPEECH_END - 0.1))
sfx.append(("sfx-endcard-hit", "impact", SPEECH_END + 0.15))
sfx.append(("sfx-endcard-logo", "sparkle", SPEECH_END + 0.75))

audio_tags = []
for i, (aid, kind, hit) in enumerate(sfx):
    src, peak, d, vol = SFX_FILES[kind]
    start = max(0.0, round(hit - peak, 2))
    d = min(d, round(TOTAL - start, 2))
    audio_tags.append(
        f'    <audio id="{aid}" src="{src}" data-start="{start}" data-duration="{d}" data-volume="{vol}" data-track-index="{20 + i}"></audio>'
    )
audios = "\n".join(audio_tags)

js_data = json.dumps(
    dict(
        segs=[{k: s[k] for k in ("id", "start", "dur", "z0", "z1")} for s in segs],
        groups=[{k: g[k] for k in ("start", "end")} for g in groups],
        callouts=[dict(id=c[0], start=round(c[3], 2), end=round(c[4], 2)) for c in CALLOUTS],
        lowerThird=[round(LOWER_THIRD[0], 2), round(LOWER_THIRD[1], 2)],
        speechEnd=SPEECH_END,
        total=TOTAL,
    )
)

html = f'''<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Anton"; src: url("assets/fonts/anton-latin-400-normal.woff2") format("woff2"); font-weight: 400; }}
      @font-face {{ font-family: "Inter"; src: url("assets/fonts/inter-latin-600-normal.woff2") format("woff2"); font-weight: 600; }}
      @font-face {{ font-family: "Inter"; src: url("assets/fonts/inter-latin-800-normal.woff2") format("woff2"); font-weight: 800; }}
      :root {{ --navy: #0b1f4b; --yellow: #ffc72c; --red: #e63946; --white: #ffffff; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
      body {{ font-family: "Inter", sans-serif; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #000; }}

      /* A-roll: one wrapper per cut so each cut gets its own punch-in */
      .cam {{ position: absolute; inset: 0; transform-origin: 50% 24%; }}
      .cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
      #grade {{ position: absolute; inset: 0; pointer-events: none;
        background: linear-gradient(180deg, rgba(11,31,75,0.35) 0%, rgba(11,31,75,0) 18%, rgba(0,0,0,0) 55%, rgba(5,12,30,0.65) 100%); }}
      #flash {{ position: absolute; inset: 0; background: #fff; opacity: 0; pointer-events: none; }}

      /* Top: progress bar + hook tag */
      #progress {{ position: absolute; left: 0; top: 0; width: 1080px; height: 10px; background: var(--yellow); transform-origin: 0 50%; }}
      #tag {{ position: absolute; left: 0; right: 0; top: 96px; display: flex; justify-content: center; }}
      #tag-pill {{ display: block; padding: 14px 30px; border-radius: 999px; background: var(--red); color: var(--white);
        font: 800 34px/1 "Inter", sans-serif; letter-spacing: 3px; }}

      /* Keyword callouts (chest area, above captions) */
      #callouts {{ position: absolute; left: 0; right: 0; top: 1040px; height: 220px; }}
      .co {{ position: absolute; left: 0; right: 0; top: 0; display: flex; flex-direction: column; align-items: center; opacity: 0; }}
      .co-text {{ display: block; padding: 10px 34px 4px; font: 400 128px/1.05 "Anton", sans-serif; letter-spacing: 2px;
        text-transform: uppercase; color: var(--navy); text-align: center; max-width: 1000px; }}
      .co-yellow .co-text {{ background: var(--yellow); }}
      .co-red .co-text {{ background: var(--red); color: var(--white); }}
      .co-bar {{ display: block; width: 260px; height: 12px; margin-bottom: 12px; background: var(--white); transform-origin: 50% 50%; }}
      #co-rakyat .co-text, #co-wadah .co-text, #co-kekuatan .co-text {{ font-size: 96px; }}

      /* Lower third */
      #lt {{ position: absolute; left: 60px; top: 1060px; width: 820px; height: 170px; opacity: 0; }}
      #lt-strip {{ position: absolute; left: 0; top: 0; width: 16px; height: 170px; background: var(--yellow); }}
      #lt-box {{ position: absolute; left: 16px; top: 0; width: 804px; height: 170px; background: rgba(11,31,75,0.92); padding: 24px 34px; }}
      #lt-kicker {{ display: block; font: 600 32px/1.2 "Inter", sans-serif; color: var(--yellow); letter-spacing: 2px; }}
      #lt-title {{ display: block; font: 400 72px/1.15 "Anton", sans-serif; color: var(--white); letter-spacing: 1px; }}

      /* Captions */
      #captions {{ position: absolute; left: 0; right: 0; top: 1330px; height: 160px; }}
      .cg {{ position: absolute; left: 40px; right: 40px; top: 0; height: 160px; display: flex; align-items: center; justify-content: center; opacity: 0; }}
      .cg-text {{ display: block; text-align: center; font: 800 76px/1.1 "Inter", sans-serif; color: var(--white);
        text-shadow: 0 4px 0 rgba(0,0,0,0.55), 0 0 22px rgba(0,0,0,0.6); -webkit-text-stroke: 2px rgba(0,0,0,0.35); }}
      .cg-text .hl {{ color: var(--yellow); }}

      /* End card */
      #end {{ position: absolute; inset: 0; opacity: 0; }}
      #end-bg {{ position: absolute; inset: 0; background: var(--navy); }}
      #end-stripe-1 {{ position: absolute; left: 0; top: 700px; width: 1080px; height: 40px; background: var(--red); }}
      #end-stripe-2 {{ position: absolute; left: 0; top: 1180px; width: 1080px; height: 40px; background: var(--yellow); }}
      #end-title {{ position: absolute; left: 0; right: 0; top: 790px; text-align: center; font: 400 150px/1.05 "Anton", sans-serif; color: var(--white); }}
      .end-line {{ display: block; }}
      #end-title .hl {{ color: var(--yellow); }}
      #end-brand {{ position: absolute; left: 0; right: 0; top: 1270px; display: flex; justify-content: center; }}
      #end-brand-pill {{ display: block; padding: 18px 46px; background: var(--yellow); color: var(--navy); font: 400 84px/1 "Anton", sans-serif; letter-spacing: 8px; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
      <div id="aroll">
{videos}
      </div>
      <div id="grade"></div>
      <div id="flash"></div>

      <div id="progress"></div>
      <div id="tag"><span id="tag-pill">MESEJ UNTUK BELIA</span></div>

      <div id="lt">
        <div id="lt-strip"></div>
        <div id="lt-box"><span id="lt-kicker">BERSAMA</span><span id="lt-title">KEPIMPINAN PRISMA</span></div>
      </div>

      <div id="callouts">
{callouts}
      </div>

      <div id="captions">
{captions}
      </div>

      <div id="end">
        <div id="end-bg"></div>
        <div id="end-stripe-1"></div>
        <div id="end-stripe-2"></div>
        <div id="end-title"><span class="end-line">SALAM</span><span class="end-line hl">PERJUANGAN</span></div>
        <div id="end-brand"><span id="end-brand-pill">PRISMA</span></div>
      </div>
    </div>

{audios}

    <script>
      const EDIT = {js_data};
      const tl = gsap.timeline({{ paused: true }});

      // Punch-in per cut: alternate framing hides the jump cuts, slow drift keeps it alive.
      EDIT.segs.forEach((s) => {{
        tl.fromTo("#cam-" + s.id, {{ scale: s.z0 }}, {{ scale: s.z1, duration: s.dur, ease: "none" }}, s.start);
      }});

      // Progress bar across the spoken part.
      tl.fromTo("#progress", {{ scaleX: 0 }}, {{ scaleX: 1, duration: EDIT.speechEnd, ease: "none" }}, 0);

      // Hook tag.
      tl.fromTo("#tag-pill", {{ y: -40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0.05);
      tl.to("#tag-pill", {{ opacity: 0, y: -30, duration: 0.25, ease: "power2.in" }}, 2.85);

      // Flash transition out of the hook into the salam.
      const hookEnd = EDIT.segs[2].start;
      tl.fromTo("#flash", {{ opacity: 0 }}, {{ opacity: 0.85, duration: 0.06 }}, hookEnd - 0.06);
      tl.to("#flash", {{ opacity: 0, duration: 0.3, ease: "power2.out" }}, hookEnd);

      // Lower third.
      const [ltIn, ltOut] = EDIT.lowerThird;
      tl.fromTo("#lt", {{ opacity: 0, x: -80 }}, {{ opacity: 1, x: 0, duration: 0.4, ease: "power3.out" }}, ltIn);
      tl.fromTo("#lt-strip", {{ scaleY: 0 }}, {{ scaleY: 1, duration: 0.35, ease: "power3.out" }}, ltIn);
      tl.fromTo("#lt-title", {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.35, ease: "power3.out" }}, ltIn + 0.15);
      tl.to("#lt", {{ opacity: 0, x: -60, duration: 0.3, ease: "power2.in" }}, ltOut - 0.3);
      tl.set("#lt", {{ opacity: 0, visibility: "hidden" }}, ltOut);

      // Keyword callouts: slam in, hold, quick exit.
      EDIT.callouts.forEach((c) => {{
        const el = "#" + c.id;
        tl.fromTo(el, {{ opacity: 0, scale: 1.6 }}, {{ opacity: 1, scale: 1, duration: 0.22, ease: "back.out(2.2)" }}, c.start);
        tl.fromTo(el + " .co-bar", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.3, ease: "power3.out" }}, c.start + 0.08);
        tl.to(el, {{ opacity: 0, y: -20, duration: 0.15, ease: "power2.in" }}, c.end - 0.15);
        tl.set(el, {{ opacity: 0, visibility: "hidden" }}, c.end);
      }});

      // Captions: one group at a time, pop in, hard kill at the end.
      EDIT.groups.forEach((g, i) => {{
        const el = "#cg-" + i;
        tl.fromTo(el, {{ opacity: 0, y: 24, scale: 0.92 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.14, ease: "back.out(1.8)" }}, g.start);
        tl.to(el, {{ opacity: 0, duration: 0.06 }}, g.end - 0.06);
        tl.set(el, {{ opacity: 0, visibility: "hidden" }}, g.end);
      }});

      // End card.
      const e0 = EDIT.speechEnd - 0.15;
      tl.fromTo("#end", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, e0);
      tl.fromTo("#end-stripe-1", {{ xPercent: -100 }}, {{ xPercent: 0, duration: 0.45, ease: "power3.out" }}, e0);
      tl.fromTo("#end-stripe-2", {{ xPercent: 100 }}, {{ xPercent: 0, duration: 0.45, ease: "power3.out" }}, e0 + 0.05);
      tl.fromTo("#end-title", {{ scale: 1.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(1.8)" }}, e0 + 0.25);
      tl.fromTo("#end-brand-pill", {{ y: 60, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.4, ease: "back.out(2)" }}, e0 + 0.85);

      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''
open(OUT, "w").write(html)
print("speech", SPEECH_END, "total", TOTAL, "groups", len(groups))
for s in segs:
    print(s["id"], s["start"], s["dur"], s["src"], " | ".join(s["chunks"]))
