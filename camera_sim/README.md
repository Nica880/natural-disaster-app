# Camera Simulator

A static HTML page that simulates 3 surveillance cameras posting frames to
the RAID backend at a configurable interval. Used to demonstrate the
end-to-end pipeline: **camera → /ingest → incident grouping → SSE → operator monitor**.

## Run

```bash
cd camera_sim
python3 -m http.server 5174
```

Then open <http://localhost:5174> and click "Start" on any camera.

You'll need the backend running on port 8000 and (optionally) the operator
frontend on port 5173 — the monitor page at <http://localhost:5173/monitor>
shows incidents as they materialise.

## Adding cameras / images

- New images: drop them into `samples/<camera-id>/` and regenerate the
  manifest:
  ```bash
  python3 -c "import json, os; [json.dump(sorted(f for f in os.listdir(d) if not f.startswith('.') and f != 'manifest.json'), open(f'{d}/manifest.json', 'w'), indent=2) for d in ['samples/cam-highway', 'samples/cam-forest', 'samples/cam-city']]"
  ```
- New camera: add an entry to the `CAMERAS` array in `index.html` and create
  a `samples/<new-id>/` folder with images + manifest.

## Why static HTML instead of another Vite app?

The simulator is a tool, not a product. A single HTML file with vanilla JS
and Tailwind via CDN does the job in ~150 lines, with no `node_modules`,
no build step, and no extra package to maintain.
