# Chrome DevTools Protocol (CDP) Examples

## Overview

Chrome DevTools Protocol enables direct browser automation without simulating mouse/keyboard input. Useful for:
- Navigating to URLs reliably (no keyboard layout issues)
- Extracting page content
- Managing downloads

## Prerequisites

Chrome must be started with `--remote-debugging-port=9222`. 

**⚠️ Do NOT kill the user's browser to start with CDP flags** — this destroys authenticated sessions. Only use CDP if Chrome was already started with debugging enabled.

## Checking CDP Status

```bash
curl -s http://localhost:9222/json/version
```

Expected response:
```json
{
  "Browser": "Chrome/150.0.7871.46",
  "Protocol-Version": "1.3",
  "webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser/..."
}
```

## Navigate to a URL

```bash
# Find the page/tab ID
curl -s http://localhost:9222/json

# Connect via WebSocket and navigate
python3 << 'EOF'
import json, websocket

ws = websocket.create_connection(
    "ws://localhost:9222/devtools/page/PAGE_ID", timeout=10
)

# Navigate
ws.send(json.dumps({
    "id": 1,
    "method": "Page.navigate",
    "params": {"url": "https://example.com"}
}))

response = json.loads(ws.recv())
print("Navigation result:", response)
ws.close()
EOF
```

## Extract Page Content

```python
import json, websocket

ws = websocket.create_connection(
    "ws://localhost:9222/devtools/page/PAGE_ID", timeout=10
)

# Evaluate JavaScript
ws.send(json.dumps({
    "id": 1,
    "method": "Runtime.evaluate",
    "params": {"expression": "document.title"}
}))

result = json.loads(ws.recv())
print("Page title:", result)
```

## Trigger Downloads

The most reliable method for Google Takeout and similar services:

```python
import json, websocket, time

ws = websocket.create_connection(
    "ws://localhost:9222/devtools/page/PAGE_ID", timeout=10
)

# Change download directory
ws.send(json.dumps({
    "id": 1,
    "method": "Browser.setDownloadBehavior",
    "params": {
        "behavior": "allow",
        "downloadPath": "C:\\path\\to\\downloads"
    }
}))

# Navigate to download URL
ws.send(json.dumps({
    "id": 2,
    "method": "Page.navigate",
    "params": {"url": "https://takeout.google.com/takeout/download?..."}
}))

time.sleep(2)
ws.close()
```

## Finding Page IDs

```bash
curl -s http://localhost:9222/json | python3 -c "
import json, sys
tabs = json.load(sys.stdin)
for t in tabs:
    print(f\"{t['id'][:12]} | {t['title'][:60]} | {t['url'][:80]}\")
"
```

## Pitfalls

1. **DO NOT** use `window.open()` in a loop — creates N login tabs
2. **DO NOT** kill Chrome to start with CDP — loses auth sessions
3. **DO** verify page loaded after navigation by checking `Page.downloadProgress`
4. **`isDownload: false`** does NOT mean it failed — Chrome downloads in background
