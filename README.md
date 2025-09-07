# ChatGPTEnabled

A practical starter repo for building **ChatGPT-assisted workflows, automations, and small apps**. It’s designed to be copy-paste friendly, Windows-friendly, and easy to grow from a single script into a real project.

<p align="center">
  <img alt="ChatGPTEnabled banner" src="https://placehold.co/1200x260?text=ChatGPTEnabled" />
</p>

---

## What is this?

**ChatGPTEnabled** is a scaffold + docs pattern to help you:
- Capture repeatable prompts and “how-tos” next to code.
- Script local helpers (Windows PowerShell / Python) that call APIs or tools.
- Keep notes, roadmaps, and decisions versioned inside the repo.

If you just want a place where ChatGPT can say “put this file here” and you can copy/paste and commit—this is it.

---

## Quick Start (Windows-friendly)

### 1) Create the repo (if you haven’t yet)

**Command Prompt / PowerShell**
```bat
mkdir ChatGPTEnabled && cd ChatGPTEnabled
git init
```

### 2) Add this README

- Create a new file named `README.md` and paste the contents of this document.
- Then:
```bat
git add README.md
git commit -m "chore: add initial README for ChatGPTEnabled"
```

*(If you want this on GitHub: create a new empty repo named `ChatGPTEnabled` and then run `git remote add origin https://github.com/<YOU>/ChatGPTEnabled.git` followed by `git push -u origin main`.)*

---

## Suggested Structure (grow as you go)

You don’t need to create these yet—this is the north star for where things will live.

```
ChatGPTEnabled/
├─ README.md
├─ /docs/                 # Decisions, design notes, playbooks, handover.md
│  ├─ ROADMAP.md
│  └─ HANDOVER.md
├─ /prompts/              # Prompt templates & usage notes
│  └─ example.prompt.md
├─ /scripts/              # Local helper scripts (PowerShell & Python)
│  ├─ windows/            # Windows-first scripts
│  │  └─ bootstrap.ps1
│  └─ python/
│     └─ example.py
├─ /config/               # .env.example, settings.json, etc.
│  └─ .env.example
└─ /data/                 # Scratch data, exported logs (gitignore-heavy)
```

---

## Conventions

- **Windows-first**: Wherever possible, include **PowerShell** instructions. Bash is optional.
- **Whole files over diffs**: When making changes via ChatGPT, prefer full file drops so you can copy/paste directly.
- **One-file commits**: Early on, favor small commits with clear messages.

---

## What to ask ChatGPT next

1. **Create a `docs/ROADMAP.md`** with a 30/60/90-day outline for this repo.
2. **Add a `/prompts/example.prompt.md`** that shows how to structure reusable prompts.
3. **Drop a PowerShell bootstrap** in `/scripts/windows/bootstrap.ps1` to set up a Python venv and install dependencies from `requirements.txt`.
4. **Add `.gitignore` and `.gitattributes`** tailored for Windows + Python.
5. **Create `/config/.env.example`** and explain what secrets will eventually live there.

---

## License

You choose! Common options:
- **MIT** – very permissive.
- **Apache-2.0** – permissive with patent protection.
- **Unlicense** – public domain style.

> If you’re unsure, MIT is usually fine. Ask ChatGPT to generate `LICENSE` text.

---

## Changelog

- **v0.0.1** – Initial README scaffold.

---

### Optional: one-shot file creation

If you’d like to create `README.md` from the terminal without opening an editor:

**PowerShell (recommended on Windows)**
```powershell
@"
# ChatGPTEnabled

A practical starter repo for building **ChatGPT-assisted workflows, automations, and small apps**. It’s designed to be copy-paste friendly, Windows-friendly, and easy to grow from a single script into a real project.

<p align="center">
  <img alt="ChatGPTEnabled banner" src="https://placehold.co/1200x260?text=ChatGPTEnabled" />
</p>

--- (snip) ---  <-- Replace this whole block with the full README content above
"@ | Set-Content -Encoding UTF8 README.md
```

After saving:
```bat
git add README.md
git commit -m "chore: initial README"
```
