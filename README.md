# Touch of Water
### Memory-Mapping with AR and Sound Journal

**MMU · Cyberjaya, Malaysia · 24 June 2026 · 2:00pm–6:00pm**

**Live:** [binyoun.github.io/touch-of-water](https://binyoun.github.io/touch-of-water)

---

## About

*Touch of Water* is a half-day collaborative workshop that uses the MMU campus as a site for exploring personal and collective memories of water. Participants work in small teams to produce two interlocking outputs: a location-responsive WebAR memory map and a sound journal, integrated into a single shareable digital experience.

Drawing from *Lọc* (Filter · Strain · Purify, 2026), a site-specific WebAR installation developed for the Tẻ Canal in Ho Chi Minh City, the AR component uses photographed objects converted into 3D digital models using AI, placed in a markerless AR space navigated by touch. GPS coordinates and bilingual text fragments function as a poetic layer. The camera feed is filtered to render the world alien -- blue-shifted, seen as if through a membrane. The phone screen is not a window but a filter. The body is a primary sensing instrument before the device.

The sound journal layer is introduced by Sigisora, a Jakarta-based listening initiative. Their practice documents the conditions under which listening occurs -- the personal, social, and infrastructural orientations that shape how we hear water. Field recordings and in-situ soundscape compositions form the audio layer accompanying each team's AR experience.

Water here is not a metaphor. It is the material, the method, and the memory.

---

## People

**Workshop Coordinator**
Prof. Suk-Jun Kim — Composer, Sound Artist, Researcher · University of Aberdeen, Scotland

**AR — Educator & Curator**
Bin Youn — Multimedia Artist, Educator, Researcher · Associate Lecturer, Digital Media · RMIT University Vietnam

**Sound Journal — Educators & Curators**
Van Luber Parensen — Artist, Filmmaker · Sigisora & Forum Lenteng, Jakarta, Indonesia
Dyah Nindyasari — Researcher · Sigisora, Jakarta, Indonesia

---

## How It Works

The workshop produces a shared WebAR map. Each team claims a location on the MMU campus, collects an object and a sound, and contributes one dot to the map. All dots are connected -- the path between them forms the memory map of the day.

**Landing page** -- a satellite map of the MMU campus with 5 GPS dots (4 teams + demo) connected by a line. Tap a dot to see team info and enter their AR experience.

**AR experience** -- the phone camera opens with a blue-shift filter. A bilingual text and GPS coordinates drift across the background like water currents. Tap to place the team's 3D model. Drag to rotate it. Pinch (mobile) or scroll wheel (desktop) to resize -- the model's size controls the volume of the sound.

---

## What Each Team Submits

| Item | Format | How to get it |
|---|---|---|
| GPS coordinates | lat, lng | Long-press your site in Google Maps |
| 3D model | `.glb` | Photograph object → upload to Luma AI or Meshy → export GLB |
| Sound recording | `.mp3` or `.wav` | Any field recorder or phone |
| Text fragment (English) | One sentence | A memory, observation, or question about water at your site |
| Text fragment (native language) | One sentence | Same or different sentence in your language |
| Language name | e.g. Indonesian | Name of the native language used |
| Team name | Any | Chosen by the team |

---

## Tools Used in the Workshop

**Making the 3D model**
- [Luma AI](https://lumalabs.ai) — photograph an object from multiple angles, AI generates a 3D model. Free tier available.
- [Meshy](https://meshy.ai) — alternative AI 3D generation tool.
- Export as `.glb` from either tool.

**Optimising the 3D model for web** (if the file is over 5MB)
- Web tool (no install): [gltf.report](https://gltf.report) — drag and drop, click Optimize, download.
- Command line: `npx gltf-transform optimize input.glb output.glb --compress draco --texture-compress webp --texture-size 1024`

**Recording sound**
- Any recorder. Zoom H-series, phone voice memo, or the Sigisora sound journal method.
- Export or convert to `.mp3` (recommended) or `.wav`.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Map | Leaflet.js 1.9.4 + Esri World Imagery satellite tiles |
| 3D rendering | Three.js 0.170.0 (WebGL, ACES tone mapping) |
| AR | Markerless -- camera feed via `getUserMedia` with CSS blue-shift filter |
| 3D models | GLB format, Draco-compressed |
| Audio | Howler.js 2.2.4 (ambient loop, volume tied to model scale) |
| Text flow | Custom 2D canvas particle system (phrase-level streams) |
| Build | No build step -- plain HTML + CDN imports |
| Hosting | GitHub Pages |

---

## Project Structure

```
touch-of-water/
├── index.html          # Landing map
├── ar.html             # AR experience (loads team config from URL param)
├── teams.json          # All team data: GPS, text, asset paths
└── teams/
    ├── demo/
    │   ├── model.glb
    │   └── sound.mp3
    ├── team1/
    │   ├── model.glb
    │   └── sound.mp3
    ├── team2/
    ├── team3/
    └── team4/
```

`teams.json` is the single file that connects everything. Each entry:

```json
{
  "id": 1,
  "name": "Team 1",
  "lat": 2.92550,
  "lng": 101.63920,
  "model": "teams/team1/model.glb",
  "sound": "teams/team1/sound.mp3",
  "textEn": "The canal holds what the city forgets.",
  "textNative": "운하는 도시가 잊은 것을 품는다.",
  "lang": "Korean",
  "placeholder": false
}
```

---

## Reference Work

*Lọc · Filter · Strain · Purify* (2026)
Site-specific WebAR installation · Kênh Tẻ Canal, Ho Chi Minh City
[github.com/binyoun/loc](https://github.com/binyoun/loc)

---

Bin Youn · 2026
