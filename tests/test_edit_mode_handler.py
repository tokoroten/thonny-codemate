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
    
    def test_build_edit_prompt_empty_file(self):
        """Test edit prompt building for empty file"""
        prompt = self.handler.build_edit_prompt(
            user_prompt="Create a hello world function",
            filename="test.py",
            content="",
            selection=None
        )
        assert "Create a hello world function" in prompt
        assert "test.py" in prompt
        assert "The file is currently empty" in prompt
        assert "complete code" in prompt
    
    def test_extract_code_block_with_standalone_backticks(self):
        """Test extraction when code contains standalone triple backticks"""
        response = '''Here's the code:
```python
def create_markdown():
    content = """
```
"""
    return content
```
'''
        result = self.handler.extract_code_block(response)
        assert 'def create_markdown():' in result
        assert 'content = """' in result
        # The standalone ``` should be included as part of the code
        assert '```' in result.split('content = """')[1]
    
    def test_extract_code_block_indented(self):
        """Test extraction with indented code blocks"""
        response = """The solution:
```python
def solve():
    return 42
```
"""
        result = self.handler.extract_code_block(response)
        assert result == 'def solve():\n    return 42'
    
    def test_extract_code_block_deeply_nested_backticks(self):
        """Test with deeply nested backticks in strings"""
        response = '''Updated code:
```python
def markdown_example():
    """
    Example:
    ```python
    result = process()
    ```
    """
    template = f"""
    # Title
    ```
    code here
    ```
    """
    return template
```
End of code.'''
        result = self.handler.extract_code_block(response)
        assert 'def markdown_example():' in result
        assert 'template = f"""' in result
        assert result.count('```') >= 2  # Should contain the backticks in the strings
    
    def test_extract_code_block_with_different_fence_lengths(self):
        """Test extraction with different fence lengths (VSCode style)"""
        response = '''Here's the updated code:
```python
def example():
    markdown = """
    ```python
    code example
    ```
    """
    return markdown
```
'''
        result = self.handler.extract_code_block(response)
        assert 'def example():' in result
        assert '```python' in result  # Inner fence should be preserved
        assert 'code example' in result
    
    def test_extract_code_block_with_tilde_fences(self):
        """Test extraction with tilde fences"""
        response = """Code below:
~~~python
def test():
    return True
~~~
"""
        # Tilde fences are not supported, should return None
        result = self.handler.extract_code_block(response)
        assert result is None
    
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