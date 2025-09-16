# Causal Blob System

An interactive causal web visualization that blends live news ingestion with personal idea inventories. The interface renders "blobs"—nodes that represent causal hypotheses, news stories, or personal reflections—inside a dynamic force-directed map. Users can add their own beliefs, weight how strongly they agree with a story, compare worldviews, and explore dimensional reductions of their causal space.

![Causal Blob System banner](https://placehold.co/1200x260?text=Causal+Blob+System)

---

## Feature Highlights

### MVP 1 – Static causal blobs
- Minimalist 2D visualization using D3 with thin black outlines and white fill.
- Hover tooltips surface summaries, tags, and existing opinions.
- Initial data seeded from `app/data/initial_state.json`.

### MVP 2 – Dynamic ingestion & authoring
- RSS/Atom ingest (default feeds from NYTimes, BBC, Al Jazeera or provide your own).
- News items are normalized into causal blobs with heuristically generated tags and links to similar nodes.
- Idea form allows anyone to add opinions, stance, and causal links into the graph in real time.

### MVP 3 – Opinion weighting & comparison
- Sliders capture agreement, confidence, stance, and weighting for any blob.
- Comparative view renders side-by-side personal causal maps for two users.
- All user submissions persist to `app/data/runtime_state.json` so state survives restarts.

### MVP 4 – Worldview geometry
- The system derives feature vectors per user (agreement, contradiction ratio, diversity, etc.).
- Custom PCA implementation projects users into a multi-dimensional ideological space.
- Interactive controls switch axes to explore different worldview cross-sections.

### Bonus waypoints
- Opinion-aware heuristics create causal links during ingestion based on shared tags.
- Tooltips and legends convey why nodes are important and how users relate to them.
- Programmatic API for automations or agent-driven analysis.

---

## Architecture

| Layer | Key Pieces |
| ----- | ---------- |
| **Frontend** | `frontend/index.html`, `frontend/css/styles.css`, `frontend/js/app.js` – static assets served by FastAPI. Uses D3.js for force layouts and worldview geometry. |
| **Backend** | FastAPI app (`app/main.py`) orchestrates state, ingestion, and analysis services. |
| **State** | `StateManager` reads/writes JSON to `app/data/runtime_state.json` with seed data in `app/data/initial_state.json`. |
| **Ingestion** | `app/services/ingestion.py` normalizes RSS feeds into nodes and generates causal links. |
| **Analysis** | `app/services/worldview.py` computes user feature vectors and applies PCA-style dimensional reduction using NumPy. |
| **Tests** | `pytest` suite validating idea creation, feed ingestion, and worldview projection (`app/tests/`). |

The backend serves `/` (the visualization) and `/static/*` assets. API routes power ingestion, ideas, opinions, comparisons, and worldview analytics.

---

## Getting Started

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the API + static server
uvicorn app.main:app --reload --port 8000
```

Open <http://localhost:8000> to explore the blob map.

### Local development tips
- The UI updates immediately after adding ideas or opinions; simply refresh to reload persisted state.
- Runtime state is stored in `app/data/runtime_state.json`. Delete it to revert to the seeded baseline.
- Use the ingest form to pull from a custom RSS/Atom URL. Leave the field empty to fetch from the default feed rotation.

---

## Core API Endpoints

| Method & Path | Description |
| ------------- | ----------- |
| `GET /api/state` | Current nodes, links, and registered users. |
| `GET /api/users` | Convenience list of users and display metadata. |
| `POST /api/ideas` | Add a new idea blob with stance, weights, and optional causal link. |
| `POST /api/opinions` | Attach or update a user’s weighting on any blob. |
| `POST /api/ingest` | Fetch news stories (`feed_url` optional, defaults rotate across curated climate/policy feeds). |
| `GET /api/comparison?user_ids=alex-analyst,sam-strategist` | Subgraphs for specific users. |
| `GET /api/worldview` | Dimensional reduction + feature vectors used by the worldview view. |
| `GET /health` | Liveness probe. |

All endpoints return JSON payloads and are suitable for automation or further integration.

---

## Testing

```bash
pytest
```

The suite covers idea creation flow, RSS ingestion heuristics, and worldview projections. Warnings from third-party libraries (e.g., `feedparser` using `cgi`) are expected.

---

## Directory Guide

```
ChatGPTEnabled/
├─ app/
│  ├─ main.py               # FastAPI app & routes
│  ├─ models.py             # Pydantic models & request schemas
│  ├─ services/
│  │  ├─ ingestion.py       # RSS/Atom ingestion helpers
│  │  ├─ state_manager.py   # JSON-backed state persistence
│  │  └─ worldview.py       # Feature extraction & PCA projection
│  ├─ data/
│  │  └─ initial_state.json # Seed nodes, links, and users
│  └─ tests/
│     ├─ sample_feed.xml    # Deterministic feed for tests
│     └─ test_services.py   # pytest coverage of core flows
├─ frontend/
│  ├─ index.html            # Single-page UI
│  ├─ css/styles.css        # Minimalist blob design
│  └─ js/app.js             # D3 rendering + UI logic
├─ requirements.txt         # Python dependencies
├─ README.md                # This documentation
└─ .gitignore
```

---

## Roadmap Ideas

- Integrate clustering/shape detection to highlight worldview "bubbles".
- Add per-user export/import of blob inventories for collaboration.
- Expand ingestion to include forums or archived discussions and auto-link references.
- Introduce agent-based simulation that tests alternative causal chains inside the blobspace.

Contributions and experiments are welcome—fork, extend, and keep iterating on the causal landscape.
