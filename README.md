# Python XML Editor

`python_xml_editor` is a local browser-based XML prompt editor with a tiny Python launcher.

It is designed for editing prompt documents that contain:

- a free-form preamble, such as a Markdown heading or note
- an XML body that can be edited visually instead of by hand

The app runs entirely locally. Python serves the static files, and the browser handles parsing, editing, preview, and export.

## Features

- open `.md`, `.txt`, and `.xml` files
- edit a prompt preamble separately from the XML structure
- rename tags and edit attributes inline
- add root, child, and sibling elements
- reorder nodes with buttons or drag-and-drop
- edit text nodes directly
- escape XML special characters on export
- support common XML-style attribute names such as `data-id` and `xml:lang`
- preview raw XML output
- export either AI-ready XML text or full editor format

## Project Structure

- `XML_Editor.py`: local launcher that serves the app and opens the browser
- `index.html`: single HTML mount point
- `app.js`: main application logic, parsing, tree editing, rendering, and export
- `style.css`: application styling
- `CONTRIBUTING.md`: contribution workflow and expectations
- `docs/ARCHITECTURE.md`: architecture and state model notes

## Requirements

- Python 3.10 or newer is recommended
- no third-party Python dependencies are required

## Run Locally

From the repository root:

```bash
python XML_Editor.py
```

If your machine uses the Windows launcher instead of `python`, you can also use:

```bash
py XML_Editor.py
```

The launcher will:

1. find a free local port
2. serve the repository directory over HTTP
3. open `index.html` in your default browser

Stop the server with `Ctrl+C`.

## Build Windows EXE

The app can be packaged as a self-contained Windows executable while keeping the current Python launcher architecture.

Recommended packaging tool:

```bash
py -3 -m pip install pyinstaller
```

Then build from the repository root:

```powershell
.\build_exe.ps1
```

The build script will:

1. read the current app version from `app.js`
2. run PyInstaller directly with the bundled launcher assets
3. create a versioned executable in `release/`

Example output:

```text
release\XML_Prompt_Editor_v0.4.3.exe
```

Packaging notes:

- the executable still uses the system browser
- `index.html`, `app.js`, and `style.css` are bundled into the executable
- `XML_Editor.py` contains a small PyInstaller compatibility path so the bundled assets can still be served correctly

## Development Workflow

1. branch from `main`
2. make and test your changes locally
3. open a pull request with a clear summary
4. include screenshots for UI changes when useful

This repository includes:

- a pull request template in `.github/pull_request_template.md`
- issue templates for bugs and feature requests
- a basic GitHub Actions workflow for pull requests and pushes

## Architecture

The application has two parts:

1. a Python wrapper in `XML_Editor.py` that starts a local HTTP server
2. a plain JavaScript single-page app in `app.js` that parses mixed preamble + XML text into a tree, renders it visually, and serializes it back out for export

The editor keeps all state in memory in the browser session and does not currently save automatically.

More detail is available in `docs/ARCHITECTURE.md`.

## Notes

- the XML parsing logic is custom and currently optimized for simple prompt-style XML
- export escapes text and attribute values so characters like `&`, `<`, and `"` remain valid XML
- the app is intentionally lightweight and has no front-end framework or backend service
