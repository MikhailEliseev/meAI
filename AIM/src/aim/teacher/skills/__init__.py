"""
Teacher Agent - Skills Layer.

Components for extracting and teaching skills from GitHub repositories.
"""

from aim.teacher.skills.skill_extractor import (
    SkillExtractor,
    ExtractedImplementation,
)
from aim.teacher.skills.skill_comparator import (
    SkillComparator,
    ComparisonResult,
)

__all__ = [
    "SkillExtractor",
    "ExtractedImplementation",
    "SkillComparator",
    "ComparisonResult",
]
