
> **2026-07-05:** Browser row below refers to **Kimi WebBridge** (Browser-Use deprecated). See [`System Design/kimi-webbridge-provider.md`](System%20Design/kimi-webbridge-provider.md).

### lean Version — What Stays, What Goes

| Feature                            | Keep             | Cut              |
| ---------------------------------- | ---------------- | ---------------- |
| Kimi WebBridge opens LinkedIn/Indeed | ✅               |                  |
| Searches jobs by role              | ✅               |                  |
| Extracts job listings              | ✅               |                  |
| Scores each job vs CV              | ✅ simple prompt |                  |
| HITL — user picks one job         | ✅               |                  |
| CV rewrite for that job            | ✅ single prompt |                  |
| Gmail API sends email              | ✅               |                  |
| Memory — logs application         | ✅ one DB write  |                  |
| Separate scoring sub-agent         |                  | ❌               |
| Separate CV optimization sub-agent |                  | ❌               |
| GitHub repo scanner                |                  | ❌               |
| Multi-platform (Indeed + LinkedIn) |                  | ❌ just LinkedIn |
| Project swap variant A/B logic     |                  | ❌<br />         |
