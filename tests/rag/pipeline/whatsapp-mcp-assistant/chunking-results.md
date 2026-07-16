# Chunking results — whatsapp-mcp-assistant

## Summary
- Parents: 6
- Boundary units: 19
- Child chunks: 6
- README chars: 2564

## Parents
- `WhatsApp MCP Assistant` — 132 tokens
- `WhatsApp MCP Assistant > Tools` — 118 tokens
- `WhatsApp MCP Assistant > Setup` — 114 tokens
- `WhatsApp MCP Assistant > QR Login Flow` — 96 tokens
- `WhatsApp MCP Assistant > Demo Flow` — 77 tokens
- `WhatsApp MCP Assistant > Current Bridge Limitation` — 72 tokens

## Child chunks
### WhatsApp MCP Assistant (chunk 0, 132 tokens, readme_section)
**whatsapp-mcp-assistant** — MCP server that exposes a real WhatsApp account to Cursor through safe, approval-gated tools and a local bridge.  This project exposes a real WhatsApp account to Cursor through an MCP server. Cursor is the agent interface; this repo only provides MCP tools and a local WhatsApp bridge.  V1 uses:  - Python `FastMCP` server for Cursor. - Local Go `whatsmeow` HTTP bridge f...

### WhatsApp MCP Assistant > Tools (chunk 1, 118 tokens, readme_section)
- `get_connection_status()` - `get_login_qr()` - `logout_whatsapp(confirm)` - `get_recent_chats(limit=10, unread_only=false, include_groups=true)` - `search_contact(query, include_groups=true, limit=5)` - `get_messages_from_contact(chat_id, limit=20, include_outgoing=true)` - `draft_reply(chat_id, instruction, recent_messages=[], tone="natural")` - `send_whatsapp_message(chat_id, message, approved...

### WhatsApp MCP Assistant > Setup (chunk 2, 114 tokens, readme_section)
Install Python dependencies:  ```powershell python -m pip install -r requirements.txt ```  Install Go, then install Go bridge dependencies:  ```powershell cd go-whatsapp-bridge go mod tidy ```  Start the WhatsApp bridge:  ```powershell go run . ```  Start Cursor with this MCP server config shape:  ```json {   "mcpServers": {     "whatsapp-assistant": {       "command": "python",       "args": comp...

### WhatsApp MCP Assistant > QR Login Flow (chunk 3, 96 tokens, readme_section)
1. Start the Go bridge. 2. Ask Cursor: `Check WhatsApp connection`. 3. If disconnected, ask Cursor: `Get WhatsApp login QR`. 4. Scan the returned QR string using WhatsApp > Linked Devices. 5. Ask Cursor to check connection again.  Every user must run the server locally and scan their own WhatsApp QR. Do not share `sessions/`, `.env`, QR codes, tokens, or connected server instances.

### WhatsApp MCP Assistant > Demo Flow (chunk 4, 77 tokens, readme_section)
Use a test WhatsApp number.  1. Send a WhatsApp message from another phone to the connected test account. 2. Ask Cursor: `Show my recent WhatsApp chats`. 3. Ask Cursor: `What did Bilal message me today?` 4. Ask Cursor: `Draft a reply saying I will come at 6`. 5. After reviewing the draft, say: `Okay, send it`.

### WhatsApp MCP Assistant > Current Bridge Limitation (chunk 5, 72 tokens, readme_section)
The local bridge records real messages it receives while the bridge is running and keeps them in `sessions/message_cache.json`. WhatsApp Web libraries do not reliably provide full historical chat export through this simple bridge, so test by sending messages after the bridge is connected.
