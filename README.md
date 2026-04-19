# Python XML Editor

`python_xml_editor` is a local browser-based XML prompt editor with a tiny Python launcher.

The Python app starts a local web server, opens the editor in your default browser, and serves a static front-end that lets you:

- open `.md`, `.txt`, and `.xml` files
- edit a prompt preamble and XML structure visually
- add, rename, reorder, drag, and delete XML nodes
- preview raw output
- export either AI-ready XML text or a full editor-friendly document

## Project Structure

- `app.py`: local launcher that serves the app and opens the browser
- `index.html`: single HTML mount point
- `app.js`: main application logic, parsing, tree editing, rendering, and export
- `style.css`: application styling

## Requirements

- Python 3.10 or newer is recommended
- No third-party Python dependencies are required

## Run Locally

From the repository root:

```bash
python app.py
```

The launcher will:

1. find a free local port
2. serve the repository directory over HTTP
3. open `index.html` in your browser

Stop the server with `Ctrl+C`.

## How The App Works

The application has two parts:

1. A Python wrapper in `app.py` that starts a local HTTP server.
2. A plain JavaScript single-page app in `app.js` that parses mixed preamble + XML text into a tree, renders it visually, and serializes it back out for export.

The editor keeps all state in memory in the browser session. It does not currently persist files automatically.

## Suggested Git Workflow

For ongoing maintenance:

1. Create a feature branch from `main`.
2. Make and test your changes locally.
3. Open a pull request with a short summary, screenshots if the UI changed, and any testing notes.
4. Merge after review.

## Pull Requests

This repository includes a pull request template under `.github/pull_request_template.md` to keep changes easy to review.

## Notes

- The XML parsing logic is custom and currently optimized for simple prompt-style XML.
- The app is intentionally lightweight and has no front-end framework or backend service.
