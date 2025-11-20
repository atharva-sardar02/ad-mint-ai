# CLI Tools - Quick Start Guide

## 🚀 Fastest Way to Get Started

### 1. Full Pipeline (YOLO Mode!)

```bash
# Prompt → Final Video in one command
python3 cli_tools/pipeline.py "Your product description here" --yolo
```

**What it does:**
- ✨ Enhances your prompt
- 🎨 Generates reference image (4 variations)
- 📖 Creates narrative structure
- 🎬 Generates storyboard frames (3 clips)
- ✨ Enhances motion prompts
- 🎥 Generates video clips (3 attempts each)
- 🎞️ Assembles final video

**Time:** ~10-15 minutes | **Cost:** ~$0.50-$1.00

---

### 2. Quick Test (Reference Image Only)

```bash
# Test your idea quickly
python3 cli_tools/pipeline.py "Your concept" --stop-at ref-image
```

**What it does:**
- ✨ Enhances prompt
- 🎨 Generates 4 reference images
- 🏆 Ranks by quality score

**Time:** ~2-3 minutes | **Cost:** ~$0.05-$0.10

---

### 3. Preview Storyboard (No Video Yet)

```bash
# See storyboard before generating videos
python3 cli_tools/pipeline.py "Your story" --stop-at storyboard
```

**What it does:**
- Everything in #2 above
- 🎬 Creates storyboard with start/end frames
- 📖 Generates narrative document

**Time:** ~5-7 minutes | **Cost:** ~$0.20-$0.40

---

### 4. Interactive Mode (Review Each Stage)

```bash
# Pause at each stage for approval
python3 cli_tools/pipeline.py "Your idea" --interactive
```

**What it does:**
- Runs each stage sequentially
- ⏸️ Pauses for your approval before continuing
- 👍 You decide: continue or stop

**Best for:** Learning the pipeline, quality control

---

## 📋 Common Customizations

```bash
# More clips
python3 cli_tools/pipeline.py prompt.txt --yolo --num-clips 5

# Vertical video (social media)
python3 cli_tools/pipeline.py prompt.txt --yolo --aspect-ratio 9:16

# Longer video
python3 cli_tools/pipeline.py prompt.txt --yolo --duration 30 --num-clips 6

# Different story style
python3 cli_tools/pipeline.py prompt.txt --yolo --story-type transformation

# Higher quality (more attempts)
python3 cli_tools/pipeline.py prompt.txt --yolo --video-attempts 5
```

---

## 🔧 Individual Tools (Manual Control)

### Just Enhance a Prompt

```bash
python3 cli_tools/enhance_image_prompt.py prompt.txt
# Output: enhanced_prompt.txt
```

### Just Generate Images

```bash
python3 cli_tools/generate_images.py prompt.txt --num-variations 8
# Output: 8 ranked images
```

### Just Create Storyboard

```bash
python3 cli_tools/create_storyboard.py prompt.txt \
  --reference-image best_image.png \
  --num-clips 5
# Output: start/end frames for 5 clips
```

### Just Generate Videos

```bash
python3 cli_tools/generate_videos.py \
  --storyboard storyboard_metadata.json \
  --num-attempts 3
# Output: video clips (3 attempts per clip)
```

---

## 💡 Pro Tips

1. **Start small**: Use `--stop-at ref-image` to test your concept first
2. **Save money**: Use `--video-attempts 2` for testing, `--video-attempts 5` for production
3. **Resume anytime**: Pipeline saves state automatically - Ctrl+C and resume later
4. **Use seeds**: `--seed 42` for reproducible results
5. **Review before video**: Use `--stop-at storyboard` to approve frames before expensive video generation

---

## 🎯 Quick Decision Tree

**"I just want a video now!"**
```bash
python3 cli_tools/pipeline.py prompt.txt --yolo
```

**"I want to test my idea first"**
```bash
python3 cli_tools/pipeline.py prompt.txt --stop-at ref-image
```

**"I want to approve each step"**
```bash
python3 cli_tools/pipeline.py prompt.txt --interactive
```

**"I want to see the storyboard before making videos"**
```bash
python3 cli_tools/pipeline.py prompt.txt --stop-at storyboard
```

**"I want maximum control"**
```bash
# Run each tool individually (see COMMANDS.md)
```

---

## 📂 Where Are My Outputs?

```
output/pipeline_runs/20250119_120000/
├── 02_reference_images/image_001.png       # Best reference image
├── 03_storyboard/storyboard_metadata.json  # Storyboard data
├── 05_video_clips/                         # Individual clips
│   ├── clip_001/clip_001_video_001.mp4    # Best clip 1
│   ├── clip_002/clip_002_video_001.mp4    # Best clip 2
│   └── clip_003/clip_003_video_001.mp4    # Best clip 3
└── 06_final_video/final_video.mp4         # Final assembled video
```

---

## ⚙️ Setup (First Time Only)

1. **Create `.env` file in `backend/` directory:**

```bash
REPLICATE_API_TOKEN=your_replicate_token_here
OPENAI_API_KEY=your_openai_key_here
```

2. **Install FFmpeg (for final video assembly):**

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

3. **Test it works:**

```bash
python3 cli_tools/pipeline.py --help
```

---

## 🆘 Need More Help?

- **Full command reference:** See `COMMANDS.md`
- **Tool documentation:** See `README.md`
- **Test individual tools:** Run `python3 cli_tools/{tool_name}.py --help`

---

## 🎬 Example: Marketing Video

```bash
# Create marketing_brief.txt with your content:
echo "Showcase our new eco-friendly water bottle.
Emphasize sustainability, modern design, and lifestyle benefits." > marketing_brief.txt

# Run pipeline
python3 cli_tools/pipeline.py marketing_brief.txt --yolo \
  --num-clips 5 \
  --story-type problem_solution \
  --aspect-ratio 9:16

# Wait ~10-15 minutes
# Find your video in: output/pipeline_runs/{timestamp}/06_final_video/final_video.mp4
```

**Done! 🎉**

---

**Ready to create?** Pick a command above and run it! 🚀
