import logging
from typing import List, Optional
from jarvis.core.models import Skill
from jarvis.core.categories import get_category_by_name

logger = logging.getLogger(__name__)


class SkillRegistry:
    def __init__(self):
        self._skills: List[Skill] = [
            Skill(name="coding_skill", installed=False, description="Write and edit code"),
            Skill(name="browser_skill", installed=False, description="Web browsing and automation"),
            Skill(name="gmail_skill", installed=False, description="Gmail integration and email automation"),
            Skill(name="canva_skill", installed=False, description="Canva design automation"),
            Skill(name="terminal_skill", installed=False, description="Terminal command execution"),
            Skill(name="file_skill", installed=False, description="File system operations"),
            Skill(name="computer_control_skill", installed=False, description="Desktop computer control"),
            Skill(name="mouse_skill", installed=False, description="Mouse control"),
            Skill(name="keyboard_skill", installed=False, description="Keyboard control"),
        ]

    def get_all_skills(self) -> List[Skill]:
        return self._skills

    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        for skill in self._skills:
            if skill.name == name:
                return skill
        return None

    def recommend_skills(self, category: str, goal: str) -> List[Skill]:
        recommendations: List[Skill] = []
        
        # Use category definitions for base recommendations
        category_def = get_category_by_name(category)
        if category_def:
            for skill_name in category_def.required_skills:
                skill = self.get_skill_by_name(skill_name)
                if skill and skill not in recommendations:
                    recommendations.append(skill)
        
        # Fallback for backward compatibility
        category_lower = category.lower()
        goal_lower = goal.lower()
        
        if category_lower in ["design"] and not recommendations:
            canva = self.get_skill_by_name("canva_skill")
            if canva:
                recommendations.append(canva)
            browser = self.get_skill_by_name("browser_skill")
            if browser:
                recommendations.append(browser)
        
        if category_lower in ["software_development"] and not recommendations:
            coding = self.get_skill_by_name("coding_skill")
            if coding:
                recommendations.append(coding)
            file = self.get_skill_by_name("file_skill")
            if file:
                recommendations.append(file)
            terminal = self.get_skill_by_name("terminal_skill")
            if terminal:
                recommendations.append(terminal)
        
        if category_lower in ["communication"] and not recommendations:
            gmail = self.get_skill_by_name("gmail_skill")
            if gmail:
                recommendations.append(gmail)
        
        if category_lower in ["system_operations"] and not recommendations:
            terminal = self.get_skill_by_name("terminal_skill")
            if terminal:
                recommendations.append(terminal)
        
        if category_lower in ["business"] and not recommendations:
            gmail = self.get_skill_by_name("gmail_skill")
            if gmail:
                recommendations.append(gmail)
            browser = self.get_skill_by_name("browser_skill")
            if browser:
                recommendations.append(browser)
        
        if category_lower in ["research"] and not recommendations:
            browser = self.get_skill_by_name("browser_skill")
            if browser:
                recommendations.append(browser)
        
        return recommendations


skill_registry = SkillRegistry()
