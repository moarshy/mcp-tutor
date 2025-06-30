"""
Course Management Module for MCP Educational Tutor Server

Simple local course content processor for structured course directories.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class StepContent(BaseModel):
    """Individual step content within a module"""
    step_type: str                      # intro, main, conclusion, assessments, summary
    title: str                          # Step title
    content: str                        # Full markdown content
    file_path: str                      # Source file path


class ModuleStructure(BaseModel):
    """Course module with its steps"""
    module_id: str                      # module_01, module_02, etc.
    title: str                          # Module title
    steps: Dict[str, StepContent]       # Steps in this module
    order: int = 0                      # Module order in course


class CourseStructure(BaseModel):
    """Complete course structure with metadata"""
    level: str                          # beginner, intermediate, advanced
    title: str                          # Course title
    description: str                    # Course description
    modules: List[ModuleStructure]      # Course modules
    welcome_content: str = ""           # Welcome content
    conclusion_content: str = ""        # Conclusion content


class CourseContentProcessor:
    """Process course content from local directory"""
    
    def __init__(self, course_directory: str = "nbs/course_output"):
        self.course_directory = Path(course_directory)
        self.courses: Dict[str, CourseStructure] = {}
    
    def scan_courses(self):
        """Scan and process all courses in the directory"""
        self.courses.clear()
        
        if not self.course_directory.exists():
            logger.warning(f"Course directory does not exist: {self.course_directory}")
            return
        
        # Process each course level directory (docs_beginner, docs_intermediate, etc.)
        for level_dir in self.course_directory.iterdir():
            if level_dir.is_dir() and level_dir.name.startswith('docs_'):
                level = level_dir.name.replace('docs_', '')
                course = self._process_course_level(level_dir, level)
                if course:
                    self.courses[level] = course
        
        logger.info(f"Loaded {len(self.courses)} courses")
    
    def _process_course_level(self, level_dir: Path, level: str) -> Optional[CourseStructure]:
        """Process individual course level"""
        try:
            # Read course metadata
            course_info_file = level_dir / "course_info.json"
            if not course_info_file.exists():
                logger.warning(f"No course_info.json found in {level_dir}")
                return None
                
            with open(course_info_file, 'r', encoding='utf-8') as f:
                course_info = json.load(f)
            
            # Read welcome and conclusion
            welcome_content = ""
            conclusion_content = ""
            
            welcome_file = level_dir / "00_welcome.md"
            if welcome_file.exists():
                welcome_content = welcome_file.read_text(encoding='utf-8')
            
            conclusion_file = level_dir / "99_conclusion.md"
            if conclusion_file.exists():
                conclusion_content = conclusion_file.read_text(encoding='utf-8')
            
            # Process modules
            modules = []
            module_infos = course_info.get('modules', [])
            
            for i, module_info in enumerate(module_infos):
                module_id = module_info.get('module_id', f'module_{i+1:02d}')
                module_dir = level_dir / module_id
                
                if module_dir.exists():
                    module = self._process_module(module_dir, module_id, i)
                    if module:
                        modules.append(module)
            
            # Create course structure
            course = CourseStructure(
                level=level,
                title=course_info.get('title', f'Course: {level.title()}'),
                description=course_info.get('description', ''),
                modules=modules,
                welcome_content=welcome_content,
                conclusion_content=conclusion_content
            )
            
            return course
            
        except Exception as e:
            logger.error(f"Failed to process course level {level_dir}: {e}")
            return None
    
    def _process_module(self, module_dir: Path, module_id: str, order: int) -> Optional[ModuleStructure]:
        """Process individual module"""
        try:
            steps = {}
            step_files = {
                'intro': '01_intro.md',
                'main': '02_main.md',
                'conclusion': '03_conclusion.md',
                'assessments': '04_assessments.md',
                'summary': '05_summary.md'
            }
            
            module_title = module_id.replace('_', ' ').title()
            
            for step_type, filename in step_files.items():
                file_path = module_dir / filename
                if file_path.exists():
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        title = self._extract_title_from_content(content) or step_type.title()
                        
                        # Use main content title for module title
                        if step_type == 'main' and title != 'Main':
                            module_title = title
                        
                        step = StepContent(
                            step_type=step_type,
                            title=title,
                            content=content,
                            file_path=str(file_path.relative_to(self.course_directory))
                        )
                        steps[step_type] = step
                        
                    except Exception as e:
                        logger.warning(f"Failed to process {filename}: {e}")
            
            if not steps:
                return None
            
            return ModuleStructure(
                module_id=module_id,
                title=module_title,
                steps=steps,
                order=order
            )
            
        except Exception as e:
            logger.error(f"Failed to process module {module_dir}: {e}")
            return None
    
    def _extract_title_from_content(self, content: str) -> Optional[str]:
        """Extract title from first heading in markdown"""
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return None
    
    def get_course(self, level: str) -> Optional[CourseStructure]:
        """Get course by level"""
        return self.courses.get(level)
    
    def list_courses(self) -> Dict[str, str]:
        """List all available courses"""
        return {level: course.title for level, course in self.courses.items()}
    
    def get_all_courses(self) -> List[CourseStructure]:
        """Get all courses"""
        return list(self.courses.values())


# Example usage
def main():
    """Example usage"""
    processor = CourseContentProcessor("nbs/course_output")
    processor.scan_courses()
    
    print(f"Available courses: {processor.list_courses()}")
    
    # Get beginner course
    beginner = processor.get_course("beginner")
    if beginner:
        print(f"Beginner course: {beginner.title}")
        print(f"Modules: {len(beginner.modules)}")


if __name__ == "__main__":
    main() 