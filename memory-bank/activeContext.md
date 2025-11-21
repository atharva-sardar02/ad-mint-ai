# Active Context

## Current Focus
- Investigating WebSocket feedback failures (`FEEDBACK_PROCESSING_FAILED - unhashable type: 'slice'`) when users provide chat feedback in the interactive pipeline UI.
- Need to inspect `conversation_history` serialization because `_build_conversation_context` assumes a list before slicing the last five items.
- Local dev is running with in-memory session storage (Redis not configured, Postgres skipped due to SQLite), so session data only lives in process memory.

## Recent Actions
- Validated frontend WebSocket flow (service + hook) and backend handler call stack.
- Confirmed SQLite DB lacks pipeline tables, indicating persistence fallback.
- Created Memory Bank scaffold (project brief, product context, system patterns, tech context, progress notes) to maintain continuity.

## Next Steps
1. Add targeted logging around `conversation_history` when handling feedback to capture actual types/structures.
2. Reproduce the UI feedback flow and inspect logs to see why slicing fails.
3. Depending on findings, normalize `conversation_history` before slicing (convert dicts or other iterables into ordered lists) and add regression tests.
