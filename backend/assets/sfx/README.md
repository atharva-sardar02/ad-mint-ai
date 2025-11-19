# Sound Effects Library

This directory contains sound effect files for video transitions and effects.

## ⚠️ IMPORTANT: Sound Effects Currently Missing

**Status:** This directory is currently empty (only contains this README). Sound effects will NOT be added to videos until you add the required files.

## Required Files

To enable sound effects in your video generation, add the following files to this directory:

### Transition Sound Effects
- `transition.mp3` or `transition.wav` - Sound effect for scene transitions (0.5s duration)

### Ambient Sound Effects (Optional but Recommended)
The system will automatically map scene sound_design descriptions to these files:
- `room_tone.mp3` or `room_tone.wav` - General ambient/room tone
- `fabric_movement.mp3` or `fabric_movement.wav` - Fabric/cloth movement sounds
- `footsteps.mp3` or `footsteps.wav` - Footstep sounds
- `paper_rustle.mp3` or `paper_rustle.wav` - Paper rustling
- `breeze.mp3` or `breeze.wav` - Wind/breeze sounds
- `nature_ambient.mp3` or `nature_ambient.wav` - Outdoor/nature ambient

## File Format Requirements

- **Format:** MP3 or WAV
- **Sample Rate:** 44.1kHz or 48kHz
- **Bitrate:** 128kbps minimum (for MP3)
- **License:** Must be royalty-free and licensed for commercial use

## How It Works

The audio service (`backend/app/services/pipeline/audio.py`) automatically:
1. Adds transition SFX at scene boundaries (0.5s duration)
2. Maps LLM `sound_design` descriptions to ambient SFX files
3. Composites SFX with background music at appropriate volumes
4. Continues gracefully if files are missing (logs warnings)

## Adding Sound Effects

1. **Source royalty-free SFX:**
   - [Freesound.org](https://freesound.org) (check license)
   - [Zapsplat](https://www.zapsplat.com) (free with attribution)
   - [Adobe Stock](https://stock.adobe.com) (paid)
   - Create your own

2. **Name files correctly:**
   - Transition: `transition.mp3` or `transition.wav`
   - Ambient: Use the names listed above

3. **Place files in this directory:**
   ```
   backend/assets/sfx/
   ├── transition.mp3
   ├── room_tone.mp3
   ├── fabric_movement.mp3
   └── ...
   ```

4. **Test:** Run a video generation and check logs for SFX confirmation

## Current Behavior

- ✅ Background music is added (from `assets/music/`)
- ❌ Transition sound effects are **skipped** (no `transition.mp3` file)
- ❌ Ambient sound effects are **skipped** (no ambient SFX files)
- ⚠️ Warnings will appear in logs when SFX files are missing

## Notes

- Sound effects are optional - videos will still be generated without them
- Transition SFX are added at scene boundaries (0.5s duration)
- Ambient SFX are matched to scene `sound_design` descriptions from LLM
- All SFX are composited with background music
- Volume levels: Music 30%, Ambient SFX 20%, Transition SFX 100%






