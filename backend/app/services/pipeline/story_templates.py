"""
Story templates for multi-stage narrative generation.
Each template defines a proven storytelling structure that can be applied to different types of advertisements.
"""

from typing import Dict, List, Any

# Template definitions
STORY_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "aida": {
        "template_id": "aida",
        "name": "AIDA Framework",
        "description": "Classic advertising structure—captures attention, builds interest, creates desire, prompts action",
        "structure": {
            "scenes": 4,
            "beats": [
                {
                    "name": "Attention",
                    "duration_range": [3, 4],
                    "goal": "Hook with striking visual or bold statement",
                    "visual_style": "Bold, eye-catching, dynamic"
                },
                {
                    "name": "Interest",
                    "duration_range": [3, 4],
                    "goal": "Show product and what makes it interesting",
                    "visual_style": "Focus on product details, engaging presentation"
                },
                {
                    "name": "Desire",
                    "duration_range": [4, 5],
                    "goal": "Demonstrate benefits, create emotional want",
                    "visual_style": "Aspirational, lifestyle-focused, emotional"
                },
                {
                    "name": "Action",
                    "duration_range": [2, 3],
                    "goal": "Brand moment, call to action, confident close",
                    "visual_style": "Strong brand presence, clear, confident"
                }
            ]
        },
        "best_for": [
            "Product launches",
            "Brand awareness campaigns",
            "E-commerce ads",
            "General purpose advertising"
        ],
        "keywords": ["product", "launch", "new", "buy", "shop", "discover", "get", "available"],
        "emotional_tone": "Energetic, aspirational, confident",
        "narrative_guidance": "Start with a hook that stops the scroll. Build curiosity about the product. Show why they need it. End with clear branding and implicit call to action."
    },
    
    "problem-agitate-solve": {
        "template_id": "problem-agitate-solve",
        "name": "Problem-Agitate-Solve",
        "description": "Identify pain point, amplify frustration, introduce solution",
        "structure": {
            "scenes": 4,
            "beats": [
                {
                    "name": "Problem",
                    "duration_range": [2, 3],
                    "goal": "Show relatable problem clearly",
                    "visual_style": "Relatable, slightly frustrating, empathetic"
                },
                {
                    "name": "Agitate",
                    "duration_range": [3, 4],
                    "goal": "Make pain visceral—show consequences",
                    "visual_style": "Heightened tension, contrast, dramatic"
                },
                {
                    "name": "Solve",
                    "duration_range": [4, 5],
                    "goal": "Introduce product as hero solution",
                    "visual_style": "Product reveal, hopeful, solution-focused"
                },
                {
                    "name": "Relief",
                    "duration_range": [3, 4],
                    "goal": "Show satisfied resolution, life improved",
                    "visual_style": "Peaceful, satisfied, problem gone"
                }
            ]
        },
        "best_for": [
            "Problem-solving products",
            "Health & wellness",
            "Productivity tools",
            "Insurance/security products"
        ],
        "keywords": ["problem", "struggle", "fix", "solve", "help", "better", "tired of", "frustrated", "issue"],
        "emotional_tone": "Empathetic, relieving, reassuring",
        "narrative_guidance": "Make the audience feel the pain point viscerally. Show consequences of not solving it. Position product as the hero that saves the day. End with relief and satisfaction."
    },
    
    "before-after-bridge": {
        "template_id": "before-after-bridge",
        "name": "Before-After-Bridge",
        "description": "Contrast life without and with product, explain transformation",
        "structure": {
            "scenes": 4,
            "beats": [
                {
                    "name": "Before",
                    "duration_range": [3, 4],
                    "goal": "Life without product—mundane or struggling",
                    "visual_style": "Muted colors, ordinary, lacking energy"
                },
                {
                    "name": "After",
                    "duration_range": [3, 4],
                    "goal": "Life with product—vibrant, successful",
                    "visual_style": "Vibrant colors, energetic, elevated"
                },
                {
                    "name": "Bridge",
                    "duration_range": [4, 5],
                    "goal": "How product creates transformation",
                    "visual_style": "Product-focused, explanatory, transition"
                },
                {
                    "name": "Celebration",
                    "duration_range": [2, 3],
                    "goal": "Enjoy the new reality, brand confidence",
                    "visual_style": "Joyful, confident, brand-forward"
                }
            ]
        },
        "best_for": [
            "Transformation products",
            "Fitness & beauty",
            "Lifestyle upgrades",
            "Education/skills"
        ],
        "keywords": ["transform", "change", "upgrade", "improve", "before", "after", "better", "evolution"],
        "emotional_tone": "Inspirational, transformative, uplifting",
        "narrative_guidance": "Show stark contrast between before and after. Make the transformation feel achievable and desirable. Explain how the product bridges the gap. Celebrate the new life."
    },
    
    "hero-journey": {
        "template_id": "hero-journey",
        "name": "Hero's Journey",
        "description": "Simplified hero's journey—ordinary world, challenge, transformation, triumph",
        "structure": {
            "scenes": 4,
            "beats": [
                {
                    "name": "Ordinary World",
                    "duration_range": [2, 3],
                    "goal": "Hero in normal state, relatable",
                    "visual_style": "Grounded, realistic, everyday"
                },
                {
                    "name": "Call to Adventure",
                    "duration_range": [3, 4],
                    "goal": "Challenge appears or product discovered",
                    "visual_style": "Pivotal moment, discovery, intrigue"
                },
                {
                    "name": "Transformation",
                    "duration_range": [4, 5],
                    "goal": "Hero uses product, overcomes challenge",
                    "visual_style": "Action-oriented, empowering, progress"
                },
                {
                    "name": "Return Triumphant",
                    "duration_range": [3, 4],
                    "goal": "Hero victorious, empowered, confident",
                    "visual_style": "Epic, triumphant, heroic"
                }
            ]
        },
        "best_for": [
            "Aspirational brands",
            "Sports & performance",
            "Personal empowerment",
            "Adventure/travel"
        ],
        "keywords": ["journey", "challenge", "achieve", "conquer", "win", "overcome", "quest", "adventure"],
        "emotional_tone": "Epic, empowering, heroic",
        "narrative_guidance": "Position the customer as the hero. Show them facing a challenge. Product becomes their tool/ally. End with triumph and empowerment."
    },
    
    "emotional-arc": {
        "template_id": "emotional-arc",
        "name": "Emotional Arc (Feel-Good)",
        "description": "Build emotional connection through authentic moments",
        "structure": {
            "scenes": 4,
            "beats": [
                {
                    "name": "Quiet Moment",
                    "duration_range": [3, 4],
                    "goal": "Relatable, intimate everyday scene",
                    "visual_style": "Soft, natural, intimate, warm"
                },
                {
                    "name": "Surprise/Delight",
                    "duration_range": [3, 4],
                    "goal": "Product enters naturally, pleasant surprise",
                    "visual_style": "Gentle reveal, natural integration, joy"
                },
                {
                    "name": "Joy",
                    "duration_range": [4, 5],
                    "goal": "Experience the benefit, genuine happiness",
                    "visual_style": "Warm lighting, genuine smiles, comfort"
                },
                {
                    "name": "Connection",
                    "duration_range": [2, 3],
                    "goal": "Sharing, togetherness, warmth",
                    "visual_style": "Human connection, heartfelt, authentic"
                }
            ]
        },
        "best_for": [
            "Food & beverage",
            "Family products",
            "Community brands",
            "Comfort/nostalgia"
        ],
        "keywords": ["family", "together", "love", "comfort", "moments", "memories", "heartfelt", "connection"],
        "emotional_tone": "Warm, heartfelt, authentic",
        "narrative_guidance": "Focus on real human moments. Let product integrate naturally into life. Build emotional resonance through authenticity. End with connection and warmth."
    },
    
    "teaser-reveal": {
        "template_id": "teaser-reveal",
        "name": "Teaser-Reveal",
        "description": "Build curiosity and anticipation, then dramatic reveal",
        "structure": {
            "scenes": 4,
            "beats": [
                {
                    "name": "Mystery",
                    "duration_range": [2, 3],
                    "goal": "Intriguing visuals, hide product, create curiosity",
                    "visual_style": "Dark, mysterious, partial views, shadows"
                },
                {
                    "name": "Build",
                    "duration_range": [3, 4],
                    "goal": "Partial reveals, hints, escalating interest",
                    "visual_style": "Gradual reveals, close-ups, anticipation"
                },
                {
                    "name": "Reveal",
                    "duration_range": [4, 5],
                    "goal": "Dramatic product reveal, 'aha' moment",
                    "visual_style": "Dramatic lighting, full view, stunning"
                },
                {
                    "name": "Showcase",
                    "duration_range": [3, 4],
                    "goal": "Product in full glory, brand moment",
                    "visual_style": "Luxurious, elegant, premium showcase"
                }
            ]
        },
        "best_for": [
            "Luxury products",
            "Tech reveals",
            "Limited editions",
            "High-end fashion"
        ],
        "keywords": ["reveal", "unveil", "introducing", "exclusive", "luxury", "premium", "mysterious", "sophisticated"],
        "emotional_tone": "Mysterious, sophisticated, dramatic",
        "narrative_guidance": "Build anticipation through mystery. Use partial reveals to heighten curiosity. Create a dramatic reveal moment. Showcase the product's premium qualities."
    },
    
    "social-proof": {
        "template_id": "social-proof",
        "name": "Social Proof",
        "description": "Show product in use by real people, build trust through community",
        "structure": {
            "scenes": 4,
            "beats": [
                {
                    "name": "Community",
                    "duration_range": [3, 4],
                    "goal": "Multiple people using/loving product",
                    "visual_style": "Diverse, energetic, multiple users"
                },
                {
                    "name": "Testimonial Moment",
                    "duration_range": [3, 4],
                    "goal": "Focus on one satisfied user, authentic",
                    "visual_style": "Genuine, relatable, documentary-style"
                },
                {
                    "name": "Results",
                    "duration_range": [4, 5],
                    "goal": "Show tangible benefits, proof",
                    "visual_style": "Evidence-based, credible, real results"
                },
                {
                    "name": "Join Us",
                    "duration_range": [2, 3],
                    "goal": "Invitation to be part of community",
                    "visual_style": "Inclusive, welcoming, community-focused"
                }
            ]
        },
        "best_for": [
            "Apps & platforms",
            "Community products",
            "Subscription services",
            "Crowdfunded products"
        ],
        "keywords": ["users", "community", "everyone", "join", "trusted", "reviews", "rated", "popular"],
        "emotional_tone": "Trustworthy, inclusive, credible",
        "narrative_guidance": "Show real people using and loving the product. Focus on authentic testimonials. Provide credible proof of results. Invite viewers to join the community."
    },
    
    "sensory-experience": {
        "template_id": "sensory-experience",
        "name": "Sensory Experience",
        "description": "Immersive focus on texture, sound, taste, smell—pure sensation",
        "structure": {
            "scenes": 4,
            "beats": [
                {
                    "name": "First Sense",
                    "duration_range": [3, 4],
                    "goal": "Close-up, one dominant sense (visual/tactile)",
                    "visual_style": "Macro shots, texture focus, intimate"
                },
                {
                    "name": "Second Sense",
                    "duration_range": [3, 4],
                    "goal": "Introduce another sense (sound/aroma)",
                    "visual_style": "Layered sensations, ASMR-style, immersive"
                },
                {
                    "name": "Immersion",
                    "duration_range": [4, 5],
                    "goal": "Full sensory experience, indulgence",
                    "visual_style": "Multi-sensory, indulgent, luxurious"
                },
                {
                    "name": "Satisfaction",
                    "duration_range": [2, 3],
                    "goal": "Satisfied sigh, contentment, brand",
                    "visual_style": "Peaceful satisfaction, subtle branding"
                }
            ]
        },
        "best_for": [
            "Food & beverage",
            "Cosmetics & fragrances",
            "Luxury goods",
            "ASMR-style content"
        ],
        "keywords": ["taste", "feel", "texture", "aroma", "experience", "indulge", "sensory", "smooth", "rich"],
        "emotional_tone": "Indulgent, intimate, luxurious",
        "narrative_guidance": "Focus on sensory details—texture, sound, visual beauty. Build immersive experience layer by layer. Create desire through sensory indulgence. End with satisfaction."
    }
}


def get_template(template_id: str) -> Dict[str, Any]:
    """Get a specific template by ID."""
    return STORY_TEMPLATES.get(template_id)


def get_all_templates() -> Dict[str, Dict[str, Any]]:
    """Get all available templates."""
    return STORY_TEMPLATES


def get_template_ids() -> List[str]:
    """Get list of all template IDs."""
    return list(STORY_TEMPLATES.keys())


def get_templates_summary() -> List[Dict[str, Any]]:
    """Get summary of all templates for selection."""
    return [
        {
            "template_id": template["template_id"],
            "name": template["name"],
            "description": template["description"],
            "best_for": template["best_for"],
            "keywords": template["keywords"],
            "emotional_tone": template["emotional_tone"]
        }
        for template in STORY_TEMPLATES.values()
    ]

