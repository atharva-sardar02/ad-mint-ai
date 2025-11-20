# Music Library

This directory contains royalty-free background music files for video generation.

## Structure

Music files should be organized by mood/style:
- `energetic.mp3` - Upbeat, energetic music
- `calm.mp3` - Relaxed, calm music
- `professional.mp3` - Corporate, professional music

## File Format

- Format: MP3
- Sample Rate: 44.1kHz or 48kHz
- Bitrate: 128kbps minimum (192kbps recommended)

## Usage

The audio service (`backend/app/services/pipeline/audio.py`) selects music based on style keywords:
- "energetic", "upbeat" → `energetic.mp3`
- "calm", "relaxed" → `calm.mp3`
- "professional", "corporate" → `professional.mp3`
- Default → `professional.mp3`

## Adding Music Files

1. Ensure music is royalty-free and licensed for commercial use
2. Name files according to the style mapping in `audio.py`
3. Place MP3 files in this directory
4. Test music selection with the audio service

## Notes

- Music will be automatically trimmed to match video duration
- Volume is adjusted to 30% to avoid overwhelming video content
- Music can be looped if shorter than video duration






