"""
MOSKV-1 · Dynamic GitHub Profile README Generator
Switches between DAY mode (Sovereign Architect) and NIGHT mode (BAKALA DE TROYA)
based on the current time in Europe/Madrid timezone.

Day:   08:00 → 20:59 CET/CEST
Night: 21:00 → 07:59 CET/CEST
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

MADRID = ZoneInfo("Europe/Madrid")

# ─── SHARED BLOCKS ──────────────────────────────────────────────────────

HEADER = """\
<div align="center">

<img src="./banner.png" alt="MOSKV-1" width="420">

</div>
"""

BADGES = """\
<div align="center">

[![CORTEX](https://img.shields.io/badge/CORTEX-Persist_v0.3-CCFF00?style=for-the-badge&labelColor=0A0A0A)](https://cortexpersist.com)
[![EU AI Act](https://img.shields.io/badge/EU_AI_Act-Compliant-CCFF00?style=for-the-badge&labelColor=0A0A0A)](https://github.com/borjamoskv/Cortex-Persist)
[![Agents](https://img.shields.io/badge/Swarm-100_Agents-CCFF00?style=for-the-badge&labelColor=0A0A0A)](https://github.com/borjamoskv/Cortex-Persist)
[![Tests](https://img.shields.io/badge/1993-Tests-CCFF00?style=for-the-badge&labelColor=0A0A0A)](https://github.com/borjamoskv/Cortex-Persist)

<br/>

<img src="https://komarev.com/ghpvc/?username=borjamoskv&style=flat-square&color=CCFF00&label=visitors" alt="visitors" />

</div>
"""

SKILL_ICONS = """\
<div align="center">

<img src="https://skillicons.dev/icons?i=python,typescript,rust,fastapi,react,nextjs,threejs,sqlite,redis,docker,linux,git&theme=dark&perline=12" />

</div>
"""

PINNED_REPOS = """\
<div align="center">

<a href="https://github.com/borjamoskv/Cortex-Persist"><img src="https://github-readme-stats.vercel.app/api/pin/?username=borjamoskv&repo=Cortex-Persist&hide_border=true&bg_color=0A0A0A&title_color=CCFF00&text_color=FAFAFA&icon_color=CCFF00" /></a>
<a href="https://github.com/borjamoskv/cortexpersist-landing"><img src="https://github-readme-stats.vercel.app/api/pin/?username=borjamoskv&repo=cortexpersist-landing&hide_border=true&bg_color=0A0A0A&title_color=CCFF00&text_color=FAFAFA&icon_color=CCFF00" /></a>
<a href="https://github.com/borjamoskv/gordacorp-immersive"><img src="https://github-readme-stats.vercel.app/api/pin/?username=borjamoskv&repo=gordacorp-immersive&hide_border=true&bg_color=0A0A0A&title_color=CCFF00&text_color=FAFAFA&icon_color=CCFF00" /></a>
<a href="https://github.com/borjamoskv/comienzos-clone"><img src="https://github-readme-stats.vercel.app/api/pin/?username=borjamoskv&repo=comienzos-clone&hide_border=true&bg_color=0A0A0A&title_color=CCFF00&text_color=FAFAFA&icon_color=CCFF00" /></a>

</div>
"""

TELEMETRY = """\
<div align="center">

<img src="https://github-profile-trophy.vercel.app/?username=borjamoskv&theme=darkhub&no-frame=true&no-bg=true&column=7" width="90%" />

<br/><br/>

<img src="https://github-readme-stats.vercel.app/api?username=borjamoskv&show_icons=true&hide_border=true&bg_color=0A0A0A&title_color=CCFF00&text_color=FAFAFA&icon_color=CCFF00&include_all_commits=true&count_private=true&custom_title=Telemetry" height="160" />
<img src="https://streak-stats.demolab.com?user=borjamoskv&hide_border=true&background=0A0A0A&ring=CCFF00&fire=CCFF00&currStreakLabel=CCFF00&sideLabels=FAFAFA&currStreakNum=FAFAFA&sideNums=FAFAFA&dates=666666" height="160" />

<br/><br/>

<img src="https://github-readme-activity-graph.vercel.app/graph?username=borjamoskv&bg_color=0A0A0A&color=FAFAFA&line=CCFF00&point=CCFF00&area=true&area_color=CCFF00&hide_border=true&custom_title=Contribution+Frequency" width="95%" />

<br/><br/>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/borjamoskv/borjamoskv/output/github-snake-dark.svg" />
  <img alt="Snake animation" src="https://raw.githubusercontent.com/borjamoskv/borjamoskv/output/github-snake-dark.svg" />
</picture>

</div>
"""

DAY_FOOTER_LINKS = """\
<div align="center">

[![Web](https://img.shields.io/badge/borjamoskv.com-CCFF00?style=for-the-badge&labelColor=0A0A0A)](https://www.borjamoskv.com)
[![CORTEX](https://img.shields.io/badge/cortexpersist.com-CCFF00?style=for-the-badge&labelColor=0A0A0A)](https://cortexpersist.com)
[![Portrait](https://img.shields.io/badge/portrait.so-CCFF00?style=for-the-badge&labelColor=0A0A0A)](https://portrait.so/borja)
[![Foundation](https://img.shields.io/badge/Foundation-CCFF00?style=for-the-badge&labelColor=0A0A0A)](https://foundation.app/@bakaladetroya)
[![Naroa](https://img.shields.io/badge/naroa.online-CCFF00?style=for-the-badge&labelColor=0A0A0A)](https://www.naroa.online)

</div>
"""

NIGHT_FOOTER_LINKS = """\
<div align="center">

[![Web](https://img.shields.io/badge/borjamoskv.com-CCFF00?style=for-the-badge&labelColor=0A0A0A)](https://www.borjamoskv.com)
[![CORTEX](https://img.shields.io/badge/cortexpersist.com-CCFF00?style=for-the-badge&labelColor=0A0A0A)](https://cortexpersist.com)
[![Bandcamp](https://img.shields.io/badge/Bandcamp-CCFF00?style=for-the-badge&labelColor=0A0A0A&logo=bandcamp&logoColor=0A0A0A)](https://borjamoskv.bandcamp.com)
[![Spotify](https://img.shields.io/badge/Spotify-CCFF00?style=for-the-badge&labelColor=0A0A0A&logo=spotify&logoColor=0A0A0A)](https://open.spotify.com/intl-es/artist/4p7wMuZpktE5aBFhBoQdqa)
[![SoundCloud](https://img.shields.io/badge/SoundCloud-CCFF00?style=for-the-badge&labelColor=0A0A0A&logo=soundcloud&logoColor=0A0A0A)](https://soundcloud.com/borja-moskv)
[![YouTube](https://img.shields.io/badge/YouTube-CCFF00?style=for-the-badge&labelColor=0A0A0A&logo=youtube&logoColor=0A0A0A)](https://www.youtube.com/@borjamoskv)
[![Discogs](https://img.shields.io/badge/Discogs-CCFF00?style=for-the-badge&labelColor=0A0A0A&logo=discogs&logoColor=0A0A0A)](https://www.discogs.com/es/release/35551876-Bakala-de-Troya-Lore-Electr%C3%B3nico-Borja-Moskv-Multiverso)
[![Naroa](https://img.shields.io/badge/naroa.online-CCFF00?style=for-the-badge&labelColor=0A0A0A)](https://www.naroa.online)

</div>
"""

# ─── DAY MODE: SOVEREIGN ARCHITECT ──────────────────────────────────────

DAY_TYPING = """\
<div align="center">
  <a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=30&duration=2500&pause=800&color=CCFF00&background=0A0A0A00&center=true&vCenter=true&repeat=true&width=600&height=45&lines=BORJA+MOSKV;SOVEREIGN+ARCHITECT;CORTEX+PERSIST;TRUST+INFRASTRUCTURE" alt="BORJA MOSKV" /></a>

<sub>☀️ <b>Modo Día</b> — Código · Arquitectura · Infraestructura de Confianza</sub>

</div>
"""

DAY_WHOAMI = """\
```yaml
# > whoami
name:      Borja Moskv
location:  Bilbao, Basque Country
role:      Sovereign Architect — Trust Infrastructure for Autonomous AI
stack:     [Python, TypeScript, Rust, WebGL, GLSL]
axiom:     "Ω₃ — Byzantine Default: Verify then trust."
aesthetic: "#0A0A0A × #CCFF00 — Industrial Noir 2026"
now:
  building:   CORTEX Persist v0.3 — cryptographic memory for AI agents
  deploying:  cortexpersist.com / .dev / .org
  exploring:  Zero-knowledge proofs & EU AI Act compliance
```
"""

DAY_CORTEX = """\
<table>
<tr>
<td width="50%" valign="top">

### 🧠 `CORTEX Persist`

> Trust infrastructure for autonomous AI.

```
🔐 AES-256 · Ed25519 · hash-chain ledger
🧬 sqlite-vec ANN · ONNX embeddings
🌐 FastAPI · MCP · Google ADK
📊 Shannon entropy · 1993 tests · 21 Seals
```

[![.com](https://img.shields.io/badge/cortexpersist.com-CCFF00?style=flat-square&labelColor=0A0A0A)](https://cortexpersist.com) [![.dev](https://img.shields.io/badge/.dev-CCFF00?style=flat-square&labelColor=0A0A0A)](https://cortexpersist.dev) [![.org](https://img.shields.io/badge/.org-CCFF00?style=flat-square&labelColor=0A0A0A)](https://cortexpersist.org)

</td>
<td width="50%" valign="top">

### ⚡ `MOSKV-1 · 7 Confluences`

> 100 sovereign agents in 7 clusters.

```
🌿 Biological   ⚔️ Tactical
💰 Financial    🔩 Physical
🎨 Esthetic     🧬 Cognitive
           🛡️ Immune
```

[![Nexus](https://img.shields.io/badge/borjamoskv.com-CCFF00?style=flat-square&labelColor=0A0A0A)](https://www.borjamoskv.com)

</td>
</tr>
</table>
"""

# ─── NIGHT MODE: BAKALA DE TROYA ────────────────────────────────────────

NIGHT_TYPING = """\
<div align="center">
  <a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=30&duration=2500&pause=800&color=CCFF00&background=0A0A0A00&center=true&vCenter=true&repeat=true&width=600&height=45&lines=BORJA+MOSKV;BAKALA+DE+TROYA;DARK+DISCO+%2F%2F+IDM;15H+NON-STOP" alt="BORJA MOSKV" /></a>

<sub>🌙 <b>Modo Noche</b> — Producción · DJ · Dark Disco · IDM</sub>

</div>
"""

NIGHT_WHOAMI = """\
```yaml
# > whoami
name:      Borja Moskv
alias:     bakaladetroya
location:  Bilbao, Basque Country
role:      Producer · DJ · Sonic Architect
genres:    [IDM, Techno, Ambient, Dark Disco, Electro]
aesthetic: "#0A0A0A × #CCFF00 — Industrial Noir 2026"
now:
  releasing:  Lore Electrónico: Borja Moskv Multiverso
  mixing:     15h non-stop · Industrial Warehouse · Dark Disco & IDM
  building:   Autonomous Rework Pipeline (Demucs + Librosa + Pedalboard)
```
"""

NIGHT_SONIC = """\
### 🎧 `// SONIC`

<div align="center">

**IDM · Techno · Ambient · Dark Disco · Electro**

[![Bandcamp](https://img.shields.io/badge/Bandcamp-0A0A0A?style=for-the-badge&logo=bandcamp&logoColor=CCFF00)](https://borjamoskv.bandcamp.com)
[![Spotify](https://img.shields.io/badge/Spotify-0A0A0A?style=for-the-badge&logo=spotify&logoColor=CCFF00)](https://open.spotify.com/intl-es/artist/4p7wMuZpktE5aBFhBoQdqa)
[![SoundCloud](https://img.shields.io/badge/SoundCloud-0A0A0A?style=for-the-badge&logo=soundcloud&logoColor=CCFF00)](https://soundcloud.com/borja-moskv)
[![YouTube](https://img.shields.io/badge/YouTube-0A0A0A?style=for-the-badge&logo=youtube&logoColor=CCFF00)](https://www.youtube.com/@borjamoskv)
[![Mixcloud](https://img.shields.io/badge/Mixcloud-0A0A0A?style=for-the-badge&logo=mixcloud&logoColor=CCFF00)](https://www.mixcloud.com/borjamoskv/)
[![Discogs](https://img.shields.io/badge/Discogs-0A0A0A?style=for-the-badge&logo=discogs&logoColor=CCFF00)](https://www.discogs.com/es/release/35551876-Bakala-de-Troya-Lore-Electr%C3%B3nico-Borja-Moskv-Multiverso)

<sub>🔥 <b>BAKALA DE TROYA</b> — 15h non-stop DJ marathon · Industrial Warehouse · Dark Disco & IDM</sub>
<br/>
<sub>🎵 Latest: <a href="https://open.spotify.com/intl-es/album/4vMh97bWkGZON5R2u55P8J"><b>Lore Electrónico: Borja Moskv Multiverso</b></a></sub>

</div>

---

<table>
<tr>
<td width="50%" valign="top">

### 🎛 `Rework Engine`

> Autonomous electronic rework pipeline.

```
🎚️ Demucs htdemucs_ft stem separation
🎹 Librosa harmonic analysis & pitch
🔊 Pedalboard FX chain & sidechain
🧬 Spectral morphing & spatial mastering
```

</td>
<td width="50%" valign="top">

### 🧠 `Also: CORTEX Persist`

> Trust infrastructure for autonomous AI.

```
🔐 AES-256 · Ed25519 · hash-chain ledger
🧬 sqlite-vec ANN · ONNX embeddings
🌐 FastAPI · MCP · Google ADK
📊 Shannon entropy · 1993 tests
```

[![CORTEX](https://img.shields.io/badge/cortexpersist.com-CCFF00?style=flat-square&labelColor=0A0A0A)](https://cortexpersist.com)

</td>
</tr>
</table>
"""

FOOTER_SIGNATURE = """\
<div align="center">

```
We are many, yet we act as one.
The swarm verifies, the ledger remembers.
```

<sub><b>#0A0A0A · #CCFF00 · MOSKV-1 v5 · 2026</b></sub>
<br/>
<sub>Todo esto sale de Bilbao. No de Berlín. Con humedad, ironía y tendencia a complicarme la vida.</sub>

</div>
"""


def is_night(now: datetime) -> bool:
    """Night = 21:00 → 07:59 Madrid time."""
    return now.hour >= 21 or now.hour < 8


def build_readme(night: bool) -> str:
    """Assemble the README from blocks based on time of day."""
    sections = [HEADER]

    if night:
        sections.append(NIGHT_TYPING)
    else:
        sections.append(DAY_TYPING)

    sections.append("---\n")
    sections.append(BADGES)
    sections.append("---\n")

    if night:
        sections.append(NIGHT_WHOAMI)
    else:
        sections.append(DAY_WHOAMI)

    sections.append("---\n")
    sections.append(SKILL_ICONS)
    sections.append("---\n")

    if night:
        sections.append(NIGHT_SONIC)
    else:
        sections.append(DAY_CORTEX)

    sections.append("---\n")
    sections.append(PINNED_REPOS)
    sections.append("---\n")
    sections.append(TELEMETRY)
    sections.append("---\n")

    if night:
        sections.append(NIGHT_FOOTER_LINKS)
    else:
        sections.append(DAY_FOOTER_LINKS)

    sections.append("\n<br/>\n\n")
    sections.append(FOOTER_SIGNATURE)

    return "\n".join(sections)


def main():
    now = datetime.now(MADRID)
    night = is_night(now)
    mode = "🌙 NIGHT" if night else "☀️ DAY"
    print(f"[MOSKV-1] {now.strftime('%Y-%m-%d %H:%M:%S %Z')} → {mode} mode")

    readme_path = Path(__file__).parent.parent / "README.md"
    content = build_readme(night)
    readme_path.write_text(content, encoding="utf-8")
    print(f"[MOSKV-1] README.md updated ({len(content)} bytes)")


if __name__ == "__main__":
    main()
