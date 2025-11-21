# Product Context

### Users & Problems
- **Creative strategists / performance marketers** need rapid storyboards and on-brand narratives without spinning up large production teams.
- **Video editors / producers** want to validate a script, look, and storyboard collaboratively before committing to expensive renders.
- Pain points today: scattered CLI tooling, slow manual feedback loops, unclear handoffs between narrative, imagery, and final render.

### How It Should Work
1. User launches the Interactive Pipeline from the UI.
2. System captures prompt + metadata, launches a session, and shows live status.
3. After each stage completes, the UI surfaces outputs plus a chat box for guidance.
4. Feedback routes over WebSockets to the backend conversation handler, which interprets intent and prepares modifications for regeneration.
5. User either regenerates or approves to unlock the next pipeline stage.

### Experience Goals
- **Clarity:** Users always know which stage they are on, what’s pending, and what actions are available.
- **Responsiveness:** Real-time updates via heartbeats and event streams; errors must explain what broke.
- **Traceability:** Conversation history should reflect every user/assistant turn so approvals and regenerations are auditable.
- **Safety:** Prevent accidental progression (require approvals) and protect API credits.
