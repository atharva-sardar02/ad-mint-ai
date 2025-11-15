# Sound Effects Library

This directory contains sound effect files for video transitions and effects.

## Structure

Sound effect files should be named by type:
- `transition.mp3` - Sound effect for scene transitions
- `click.mp3` - Click sound effect
- `whoosh.mp3` - Whoosh sound effect

## File Format

- Format: MP3 or WAV
- Sample Rate: 44.1kHz or 48kHz
- Bitrate: 128kbps minimum (for MP3)

## Usage

The audio service (`backend/app/services/pipeline/audio.py`) selects sound effects based on type:
- "transition" → `transition.mp3` or `transition.wav`
- Other types can be added as needed

## Adding Sound Effects

1. Ensure sound effects are royalty-free and licensed for commercial use
2. Name files according to the type (e.g., `transition.mp3`)
3. Place files in this directory
4. Sound effects are optional - service will continue if file not found

## Notes

- Sound effects are added at scene transitions (0.5s duration)
- Sound effects are composited with background music
- If a sound effect file is not found, the service continues without it (logs warning)



