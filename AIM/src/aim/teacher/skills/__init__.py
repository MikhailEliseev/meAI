"""
Teacher Agent - Skills Layer.

Components for extracting and teaching skills from GitHub repositories.
"""

from AIM.src.aim.teacher.skills.skill_extractor import (
    SkillExtractor,
    SkillType,
    ExtractedSkill,
)

__all__ = [
    "SkillExtractor",
    "SkillType",
    "ExtractedSkill",
]
