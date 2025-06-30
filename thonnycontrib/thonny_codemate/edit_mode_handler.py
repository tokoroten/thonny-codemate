"""
Edit mode handler for single file editing
Inspired by VSCode Copilot Chat's edit functionality
"""
import re
import tkinter as tk
from typing import Optional, Tuple, List
from pathlib import Path
import difflib
import logging

from thonny import get_workbench
from .i18n import tr

logger = logging.getLogger(__name__)


class EditModeHandler:
    """Handles edit mode functionality for modifying code in the current file"""
    
    # Prompt template for edit mode
    EDIT_PROMPT_TEMPLATE = """You are an AI programming assistant specialized in modifying code.

Instructions:
1. Provide the complete modified code
2. Use '# ...existing code...' to represent unchanged regions (this saves tokens)
3. Preserve the original indentation and coding style
4. Focus only on the requested changes
5. Include helpful comments for significant changes

Current file: {filename}
Language: {language}

Current code:
```{language}
{content}
```

{selection_info}

User request: {user_prompt}

Please provide the modified code. Start your response with a code block containing the updated code:
"""

    SELECTION_TEMPLATE = """Selected region (lines {start_line}-{end_line}):
```{language}
{selected_text}
```

Focus your changes primarily on the selected region, but you may modify other parts if necessary.
"""

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.workbench = get_workbench()
        
    def build_edit_prompt(self, user_prompt: str, filename: str, content: str, 
                         selection: Optional[Tuple[str, int, int]] = None) -> str:
        """Build the prompt for edit mode"""
        # Detect language from filename
        language = self._detect_language(filename)
        
        # Handle selection if provided
        selection_info = ""
        if selection:
            selected_text, start_line, end_line = selection
            selection_info = self.SELECTION_TEMPLATE.format(
                language=language,
                selected_text=selected_text,
                start_line=start_line,
                end_line=end_line
            )
        
        return self.EDIT_PROMPT_TEMPLATE.format(
            filename=filename or "Untitled",
            language=language,
            content=content,
            selection_info=selection_info,
            user_prompt=user_prompt
        )
    
    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename"""
        if not filename:
            return "python"
            
        ext = Path(filename).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.sh': 'bash',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.xml': 'xml'
        }
        return language_map.get(ext, 'text')
    
    def extract_code_block(self, response: str) -> Optional[str]:
        """Extract the first code block from LLM response"""
        # Pattern to match code blocks with optional language specifier
        pattern = r'```(?:\w+)?\s*\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no code block found, check if the entire response might be code
        # (sometimes LLMs return code without backticks)
        lines = response.strip().split('\n')
        if len(lines) > 3 and any(line.strip().startswith(('def ', 'class ', 'import ', 'from ')) for line in lines):
            return response.strip()
            
        return None
    
    def expand_existing_code_markers(self, modified_code: str, original_code: str) -> str:
        """Expand '# ...existing code...' markers with actual code"""
        if '# ...existing code...' not in modified_code:
            return modified_code
            
        original_lines = original_code.split('\n')
        modified_lines = modified_code.split('\n')
        result_lines = []
        
        original_idx = 0
        
        for line in modified_lines:
            if '# ...existing code...' in line.strip():
                # Skip this marker
                indent = len(line) - len(line.lstrip())
                
                # Find the next matching line in modified code
                next_modified_idx = modified_lines.index(line) + 1
                next_modified_line = None
                while next_modified_idx < len(modified_lines):
                    next_line = modified_lines[next_modified_idx]
                    if next_line.strip() and '# ...existing code...' not in next_line:
                        next_modified_line = next_line.strip()
                        break
                    next_modified_idx += 1
                
                # Copy original lines until we find the next modified line
                while original_idx < len(original_lines):
                    orig_line = original_lines[original_idx]
                    if next_modified_line and orig_line.strip() == next_modified_line:
                        break
                    result_lines.append(orig_line)
                    original_idx += 1
            else:
                result_lines.append(line)
                # Advance original_idx if this line matches
                if original_idx < len(original_lines) and line.strip() == original_lines[original_idx].strip():
                    original_idx += 1
        
        return '\n'.join(result_lines)
    
    def create_diff(self, original: str, modified: str) -> List[str]:
        """Create a unified diff between original and modified code"""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = list(difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile='Original',
            tofile='Modified',
            lineterm=''
        ))
        
        return diff
    
    def apply_edit(self, editor, new_code: str) -> bool:
        """Apply the edit to the editor"""
        try:
            text_widget = editor.get_text_widget()
            
            # Save cursor position
            cursor_pos = text_widget.index("insert")
            
            # Replace content
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", new_code)
            
            # Restore cursor position if possible
            try:
                text_widget.mark_set("insert", cursor_pos)
            except:
                pass
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply edit: {e}")
            return False
    
    def get_selection_info(self, editor) -> Optional[Tuple[str, int, int]]:
        """Get selected text and line numbers if any"""
        text_widget = editor.get_text_widget()
        
        if text_widget.tag_ranges("sel"):
            selected_text = text_widget.get("sel.first", "sel.last")
            start_line = int(text_widget.index("sel.first").split(".")[0])
            end_line = int(text_widget.index("sel.last").split(".")[0])
            return (selected_text, start_line, end_line)
            
        return None