# Project Brief

Ad Mint AI is an end-to-end platform for planning, generating, and refining AI-assisted advertising assets (stories, reference images, storyboards, and videos). The current focus is the **Interactive Pipeline**, which lets creatives iterate on each stage through chat-style feedback before spending compute on the next step. The product must feel fast, reliable, and transparent: creatives should clearly see the pipeline state, provide adjustments conversationally, and approve stages with confidence that their intent is preserved throughout.

### Core Goals
- Provide a guided, multi-stage creative workflow that pauses after each deliverable (story → reference images → storyboard → video).
- Capture conversational feedback and convert it into structured modifications for regeneration.
- Keep users informed in real time via WebSocket updates and UI progress indicators.
- Guard production resources: only proceed once a stage is approved, and highlight any blockers or quality issues immediately.

### Success Criteria
- Creatives can start a session from the UI, watch outputs stream in, and give feedback without page reloads.
- Feedback feels natural (chat UX) and reliably changes subsequent generations.
- Errors surface clearly with actionable follow-ups (retry, edit prompt, contact support).
- System state survives restarts in production via Redis/Postgres storage.
