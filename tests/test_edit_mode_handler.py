"""
Tests for EditModeHandler
"""
import pytest
from thonnycontrib.thonny_codemate.edit_mode_handler import EditModeHandler


class TestEditModeHandler:
    def setup_method(self):
        """Set up test fixtures"""
        self.handler = EditModeHandler(llm_client=None)
    
    def test_extract_code_block_simple(self):
        """Test simple code block extraction"""
        response = """Here's the updated code:
```python
def hello():
    print("Hello, world!")
```
"""
        result = self.handler.extract_code_block(response)
        assert result == 'def hello():\n    print("Hello, world!")'
    
    def test_extract_code_block_with_multiline_string(self):
        """Test code block extraction with multiline strings containing backticks"""
        response = """Here's the updated code:
```python
def get_help():
    '''
    This function returns help text.
    
    Usage example:
    ```
    result = get_help()
    print(result)
    ```
    '''
    return "Help text"
```
"""
        result = self.handler.extract_code_block(response)
        expected = '''def get_help():
    \'\'\'
    This function returns help text.
    
    Usage example:
    ```
    result = get_help()
    print(result)
    ```
    \'\'\'
    return "Help text"'''
        assert result == expected
    
    def test_extract_code_block_with_triple_quotes(self):
        """Test code block extraction with triple quotes"""
        response = '''Here's the code:
```python
def format_code():
    """Format code with markdown."""
    template = """
    ```python
    # Your code here
    ```
    """
    return template
```
'''
        result = self.handler.extract_code_block(response)
        assert 'def format_code():' in result
        assert 'template = """' in result
        assert '# Your code here' in result
    
    def test_extract_code_block_no_language(self):
        """Test code block without language specifier"""
        response = """Updated:
```
x = 10
y = 20
```
"""
        result = self.handler.extract_code_block(response)
        assert result == 'x = 10\ny = 20'
    
    def test_extract_code_block_no_backticks(self):
        """Test extraction when no code block markers present"""
        response = """def calculate(x, y):
    return x + y

result = calculate(5, 3)"""
        result = self.handler.extract_code_block(response)
        assert result == response.strip()
    
    def test_build_edit_prompt(self):
        """Test edit prompt building"""
        prompt = self.handler.build_edit_prompt(
            user_prompt="Add error handling",
            filename="test.py",
            content="def divide(a, b):\n    return a / b",
            selection=None
        )
        assert "Add error handling" in prompt
        assert "test.py" in prompt
        assert "def divide(a, b):" in prompt
    
    def test_expand_existing_code_markers(self):
        """Test expanding ...existing code... markers"""
        original = """def func1():
    pass

def func2():
    pass

def func3():
    pass"""
        
        modified = """def func1():
    pass

# ...existing code...

def func3():
    print("Modified")"""
        
        result = self.handler.expand_existing_code_markers(modified, original)
        assert "def func2():" in result
        assert 'print("Modified")' in result