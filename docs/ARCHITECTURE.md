# Architecture

## Overview

The application has two layers:

1. `XML_Editor.py` launches a local HTTP server and opens the browser.
2. `app.js` implements the editor as a plain JavaScript single-page app.

There is no backend API, database, or framework runtime. All editing happens in memory in the browser.

## Runtime Flow

1. `XML_Editor.py` finds a free local port.
2. It serves the repository directory with `http.server`.
3. It opens `index.html` in the default browser.
4. The browser loads `app.js` and initializes the editor with a sample document.

## Front-End Structure

The JavaScript is organized as a single file with a few logical layers:

- parsing helpers that split preamble text from XML and build a node tree
- serialization helpers that convert the node tree back into text
- tree update helpers for add, remove, rename, reorder, and move operations
- rendering functions that rebuild the UI from current state

The app uses a full re-render approach. After significant state changes, it calls `render()` and reconstructs the visible interface.

## State Model

Global state lives in a single `state` object in `app.js`.

UI state includes:

- current export modal visibility and export mode
- raw view toggle
- help panel toggle
- copied-to-clipboard status
- drag-and-drop state
- collapsed tree state
- preamble editing state

Document state includes:

- `doc.preamble`: free-form text before the XML block
- `doc.root`: array of root nodes

## Node Model

The XML tree uses two node shapes.

Element nodes contain:

- `id`
- `type: "element"`
- `tag`
- `attributes`
- `children`
- optional `parent`

Text nodes contain:

- `id`
- `type: "text"`
- `text`
- `children`
- optional `parent`

## Parsing Model

The editor accepts documents with a free-form preamble followed by XML.

`parseDocument()`:

1. scans line-by-line until it finds the start of XML
2. treats everything before that as preamble
3. tokenizes the XML text
4. builds a nested tree structure from the tokens

The parser is custom and lightweight. It is built for the editor's simple XML structure rather than strict general-purpose XML compatibility.

Current parser/serializer behavior intentionally includes a few pragmatic rules:

- common XML entities in imported text and attribute values are decoded into the in-memory document model
- exported text and attribute values are escaped again so special characters remain valid XML
- attribute names support common XML-style characters such as `.`, `-`, `_`, and `:`
- tag rename validation uses a lightweight XML-name check to avoid exporting obviously invalid tag names

## Export Model

The app supports two export modes:

- AI-ready export: clean XML without the preamble
- editor export: preamble plus XML, suitable for reopening in the editor

## Maintenance Notes

- there is currently no persistent storage layer
- there are no third-party package managers or dependencies
- most future changes will happen in `app.js`, with `style.css` for UI styling and `XML_Editor.py` only for launcher behavior
