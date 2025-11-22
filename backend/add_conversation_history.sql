-- Add llm_conversation_history column to generations table
-- Run this with: sqlite3 app.db < add_conversation_history.sql

ALTER TABLE generations ADD COLUMN llm_conversation_history TEXT;

