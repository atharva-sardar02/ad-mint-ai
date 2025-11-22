"""
Master Mode API routes for simplified video generation.
"""
import logging
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.models.generation import Generation
from app.db.session import get_db
from app.services.master_mode import convert_scenes_to_video_prompts, generate_and_stitch_videos
from app.services.master_mode.streaming_wrapper import (
    generate_story_iterative_with_streaming,
    generate_scenes_with_streaming
)
from app.services.master_mode.schemas import StoryGenerationResult, ScenesGenerationResult
from app.api.routes.master_mode_progress import (
    create_progress_queue,
    send_progress_update,
    close_progress_queue,
    send_llm_interaction,
    get_conversation_history,
    clear_conversation_history
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/master-mode", tags=["master-mode"])


@router.post("/generate-story")
async def generate_story(
    prompt: str = Form(..., description="User prompt for the advertisement"),
    title: Optional[str] = Form(None, description="Optional video title"),
    brand_name: Optional[str] = Form(None, description="Optional brand name"),
    client_generation_id: Optional[str] = Form(None, description="Client-provided generation ID"),
    reference_images: List[UploadFile] = File(default=[], description="Reference images (up to 3)"),
    max_iterations: int = Form(3, description="Maximum number of iterations (default: 3)"),
    generate_scenes: bool = Form(True, description="Whether to generate scenes after story (default: True)"),
    generate_videos: bool = Form(False, description="Whether to generate and stitch videos (default: False)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a story using the two-agent system (Story Director and Story Critic).
    Optionally generate detailed scenes using the three-agent system (Scene Writer, Scene Critic, Scene Cohesor).
    Returns the story, scenes, and full conversation history between agents.
    """
    try:
        # Generate unique ID for this generation (use client-provided ID if available)
        generation_id = client_generation_id or str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"[Master Mode] Story generation requested by user {current_user.id}, generation_id: {generation_id}")
        
        # Create database record for this generation
        db_generation = Generation(
            id=generation_id,
            user_id=current_user.id,
            prompt=prompt,
            title=title or "Master Mode Video",
            status="processing",
            progress=0,
            current_step="Initializing...",
            framework="master_mode",  # Special framework identifier
            created_at=start_time
        )
        db.add(db_generation)
        db.commit()
        logger.info(f"[Master Mode] Created database record for generation {generation_id}")
        
        # Create progress queue
        create_progress_queue(generation_id)
        await send_progress_update(generation_id, "init", "in_progress", 0, "Starting generation...")
        
        # Save reference images temporarily
        temp_dir = Path("temp") / "master_mode" / str(current_user.id) / generation_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        await send_progress_update(generation_id, "upload", "in_progress", 5, "Saving reference images...")
        
        saved_image_paths = []
        for idx, image_file in enumerate(reference_images):
            if image_file and image_file.filename:
                # Save image to temp directory
                image_path = temp_dir / f"reference_{idx + 1}_{image_file.filename}"
                with open(image_path, "wb") as f:
                    content = await image_file.read()
                    f.write(content)
                saved_image_paths.append(str(image_path))
                logger.info(f"[Master Mode] Saved reference image {idx + 1}: {image_path}")
        
        await send_progress_update(generation_id, "upload", "completed", 10, f"Saved {len(saved_image_paths)} reference images")
        
        # Generate story iteratively with reference images
        await send_progress_update(generation_id, "story", "in_progress", 15, "Generating story with vision-enhanced AI...")
        
        story_result: StoryGenerationResult = await generate_story_iterative_with_streaming(
            user_prompt=prompt,
            generation_id=generation_id,
            max_iterations=max_iterations,
            reference_image_paths=saved_image_paths if saved_image_paths else None,
            brand_name=brand_name
        )
        
        await send_progress_update(generation_id, "story", "completed", 30, f"Story generated (score: {story_result.final_score}/100)")
        
        # Update database with story progress
        db_generation.progress = 30
        db_generation.current_step = "Story generated"
        db.commit()
        
        # Build response
        response = {
            "success": True,
            "generation_id": generation_id,
            "story": story_result.final_story,
            "approval_status": story_result.approval_status,
            "final_score": story_result.final_score,
            "total_iterations": story_result.total_iterations,
            "story_conversation_history": [
                {
                    "role": entry.role,
                    "iteration": entry.iteration,
                    "content": entry.content,
                    "timestamp": entry.timestamp.isoformat()
                }
                for entry in story_result.conversation_history
            ],
            "story_iterations": [
                {
                    "iteration": it.iteration,
                    "story_draft": it.story_draft,
                    "critique": {
                        "approval_status": it.critique.approval_status,
                        "overall_score": it.critique.overall_score,
                        "critique": it.critique.critique,
                        "strengths": it.critique.strengths,
                        "improvements": it.critique.improvements,
                        "priority_fixes": it.critique.priority_fixes
                    },
                    "timestamp": it.timestamp.isoformat()
                }
                for it in story_result.iterations
            ]
        }
        
        # Generate scenes if requested
        if generate_scenes:
            await send_progress_update(generation_id, "scenes", "in_progress", 35, "Generating detailed scenes...")
            
            logger.info(f"[Master Mode] Generating scenes from story")
            scenes_result: ScenesGenerationResult = await generate_scenes_with_streaming(
                story=story_result.final_story,
                generation_id=generation_id,
                max_iterations_per_scene=3,
                max_cohesor_iterations=2
            )
            
            await send_progress_update(generation_id, "scenes", "completed", 55, f"Generated {scenes_result.total_scenes} scenes (cohesion: {scenes_result.cohesion_score}/100)")
            
            # Update database with scene progress
            db_generation.progress = 55
            db_generation.current_step = f"Generated {scenes_result.total_scenes} scenes"
            db_generation.num_scenes = scenes_result.total_scenes
            db.commit()
            
            response["scenes"] = {
                "total_scenes": scenes_result.total_scenes,
                "cohesion_score": scenes_result.cohesion_score,
                "scenes": [
                    {
                        "scene_number": scene.scene_number,
                        "content": scene.content,
                        "iterations": scene.iterations,
                        "approved": scene.approved,
                        "final_critique": {
                            "approval_status": scene.final_critique.approval_status,
                            "overall_score": scene.final_critique.overall_score,
                            "critique": scene.final_critique.critique,
                            "strengths": scene.final_critique.strengths,
                            "improvements": scene.final_critique.improvements,
                            "priority_fixes": scene.final_critique.priority_fixes
                        }
                    }
                    for scene in scenes_result.scenes
                ],
                "cohesion_analysis": {
                    "overall_cohesion_score": scenes_result.cohesion_analysis.overall_cohesion_score,
                    "pair_wise_analysis": [
                        {
                            "from_scene": pa.from_scene,
                            "to_scene": pa.to_scene,
                            "transition_score": pa.transition_score,
                            "issues": pa.issues,
                            "recommendations": pa.recommendations
                        }
                        for pa in scenes_result.cohesion_analysis.pair_wise_analysis
                    ],
                    "global_issues": scenes_result.cohesion_analysis.global_issues,
                    "scene_specific_feedback": scenes_result.cohesion_analysis.scene_specific_feedback,
                    "consistency_issues": scenes_result.cohesion_analysis.consistency_issues,
                    "overall_recommendations": scenes_result.cohesion_analysis.overall_recommendations
                },
                "conversation_history": scenes_result.conversation_history,
                "total_iterations": scenes_result.total_iterations
            }
            
            # Convert scenes to video generation parameters
            await send_progress_update(generation_id, "video_params", "in_progress", 60, "Preparing video generation parameters...")
            
            logger.info(f"[Master Mode] Converting scenes to video generation prompts")
            video_params_list = await convert_scenes_to_video_prompts(
                scenes=[
                    {
                        "scene_number": scene.scene_number,
                        "content": scene.content
                    }
                    for scene in scenes_result.scenes
                ],
                story=story_result.final_story,
                reference_image_paths=saved_image_paths if saved_image_paths else None,
                generation_id=generation_id  # NEW: Pass for streaming
            )
            
            response["video_generation_params"] = video_params_list
            logger.info(f"[Master Mode] Generated {len(video_params_list)} video generation parameter sets")
            
            await send_progress_update(generation_id, "video_params", "completed", 65, f"Prepared {len(video_params_list)} video generation parameter sets")
            
            # Generate and stitch videos if requested
            if generate_videos:
                await send_progress_update(generation_id, "videos", "in_progress", 70, "Generating scene videos (this may take several minutes)...")
                
                logger.info(f"[Master Mode] Generating and stitching videos")
                
                # Create output directories
                video_output_dir = temp_dir / "scene_videos"
                final_output_path = temp_dir / f"final_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                
                # Generate and stitch videos
                final_video_path = await generate_and_stitch_videos(
                    video_params_list=video_params_list,
                    cohesion_analysis=scenes_result.cohesion_analysis.model_dump(),
                    output_dir=video_output_dir,
                    final_output_path=final_output_path,
                    generation_id=generation_id,
                    max_parallel=4
                )
                
                if final_video_path:
                    logger.info(f"[Master Mode] Final video created: {final_video_path}")
                    
                    # Convert file paths to URLs accessible from frontend
                    # The paths are like: temp/master_mode/user_id/generation_id/...
                    # We need to convert them to: /temp/master_mode/user_id/generation_id/...
                    def path_to_url(path_str: str) -> str:
                        """Convert file system path to URL path"""
                        from pathlib import Path
                        
                        # Convert to Path object for easier manipulation
                        path_obj = Path(path_str)
                        
                        # If it's an absolute path, make it relative to the backend directory
                        if path_obj.is_absolute():
                            # Get the backend directory (where we're running from)
                            backend_dir = Path(__file__).parent.parent.parent  # routes -> api -> app -> backend
                            try:
                                # Make path relative to backend directory
                                relative_path = path_obj.relative_to(backend_dir)
                                normalized = str(relative_path).replace("\\", "/")
                            except ValueError:
                                # If path is not relative to backend_dir, try to find 'temp' in the path
                                path_parts = path_obj.parts
                                if "temp" in path_parts:
                                    temp_index = path_parts.index("temp")
                                    normalized = "/".join(path_parts[temp_index:])
                                else:
                                    # Fallback: just use the path as-is
                                    normalized = str(path_obj).replace("\\", "/")
                        else:
                            # Already relative, just normalize separators
                            normalized = str(path_obj).replace("\\", "/")
                        
                        # Ensure it starts with /
                        if not normalized.startswith("/"):
                            normalized = "/" + normalized
                        return normalized
                    
                    final_video_url = path_to_url(final_video_path)
                    scene_video_urls = [
                        path_to_url(video_output_dir / f"scene_{i+1:02d}.mp4")
                        for i in range(len(video_params_list))
                    ]
                    
                    response["final_video_path"] = final_video_url
                    response["video_generation_status"] = "success"
                    response["scene_videos"] = scene_video_urls
                    
                    await send_progress_update(generation_id, "videos", "completed", 95, "Videos generated and stitched successfully!", {
                        "final_video_path": final_video_url,
                        "scene_videos": scene_video_urls
                    })
                    
                    # Update database record with video information
                    db_generation.video_path = final_video_path
                    db_generation.video_url = final_video_url
                    db_generation.temp_clip_paths = scene_video_urls
                    db_generation.num_scenes = len(video_params_list)
                    db_generation.num_clips = len(video_params_list)
                    db_generation.status = "completed"
                    db_generation.progress = 100
                    db_generation.current_step = "Complete"
                    db_generation.completed_at = datetime.utcnow()
                    db_generation.generation_time_seconds = int((datetime.utcnow() - start_time).total_seconds())
                    
                    # Save LLM conversation history for later viewing
                    conversation_history = get_conversation_history(generation_id)
                    if conversation_history:
                        db_generation.llm_conversation_history = conversation_history
                        logger.info(f"[Master Mode] Saved {len(conversation_history)} conversation entries to database")
                        # Clean up in-memory storage
                        clear_conversation_history(generation_id)
                    
                    db.commit()
                    logger.info(f"[Master Mode] Updated database record with video information")
                else:
                    logger.error(f"[Master Mode] Video generation failed")
                    response["video_generation_status"] = "failed"
                    response["final_video_path"] = None
                    
                    # Save story and scenes data even if videos failed
                    if "story" in response and "scenes" in response:
                        import json
                        db_generation.llm_specification = json.dumps({
                            "story": response["story"],
                            "story_score": response.get("final_score", 0),
                            "approval_status": response.get("approval_status", ""),
                            "total_iterations": response.get("total_iterations", 0)
                        })
                        db_generation.scene_plan = json.dumps({
                            "total_scenes": response["scenes"].get("total_scenes", 0),
                            "cohesion_score": response["scenes"].get("cohesion_score", 0),
                            "scenes": response["scenes"].get("scenes", [])
                        })
                    
                    # Update database to reflect failure
                    db_generation.status = "failed"
                    db_generation.error_message = "Video generation failed - content flagged by Google API as sensitive (E005). Try different reference images or simpler prompts."
                    db_generation.progress = 70
                    db.commit()
                    
                    await send_progress_update(generation_id, "videos", "failed", 70, "Video generation failed")
        else:
            # If videos weren't generated, mark as completed but without video
            db_generation.status = "completed"
            db_generation.progress = 100
            db_generation.current_step = "Complete (Story and Scenes only)"
            db_generation.completed_at = datetime.utcnow()
            db_generation.generation_time_seconds = int((datetime.utcnow() - start_time).total_seconds())
            db.commit()
        
        # Send final completion with video paths if available
        completion_data = {}
        if "final_video_path" in response and response.get("video_generation_status") == "success":
            completion_data["final_video_path"] = response["final_video_path"]
            completion_data["scene_videos"] = response.get("scene_videos", [])
            completion_data["num_scenes"] = len(response.get("scene_videos", []))
        
        # Add story and scene quality scores
        if "final_score" in response:
            completion_data["story_score"] = response["final_score"]
        if "scenes" in response:
            completion_data["cohesion_score"] = response["scenes"].get("cohesion_score", 0)
            if "num_scenes" not in completion_data:  # Only set if not already set from videos
                completion_data["num_scenes"] = response["scenes"].get("total_scenes", 0)
        
        await send_progress_update(generation_id, "complete", "completed", 100, "Generation complete!", completion_data)
        await close_progress_queue(generation_id)
        
        return response
        
    except Exception as e:
        logger.error(f"[Master Mode] Error generating story: {str(e)}", exc_info=True)
        
        # Update database record with error
        try:
            if 'db_generation' in locals() and db_generation:
                db_generation.status = "failed"
                db_generation.error_message = str(e)
                db_generation.progress = 0
                db_generation.current_step = "Failed"
                db.commit()
        except Exception as db_error:
            logger.error(f"[Master Mode] Failed to update database with error: {db_error}")
        
        # Try to send error update
        try:
            if 'generation_id' in locals():
                await send_progress_update(generation_id, "error", "failed", 0, f"Error: {str(e)}")
                await close_progress_queue(generation_id)
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate story: {str(e)}"
        )

