# Copy and Insert Button Implementation

This document describes the simplified implementation of Copy and Insert buttons for code blocks in the HTML chat view.

## Overview

The implementation provides Copy and Insert buttons for each code block using standard web technologies. Copy uses the browser's Clipboard API, while Insert uses URL navigation to communicate with Python.

## Implementation Details

### 1. HTML Structure (markdown_renderer.py)

Each code block includes:
- Copy and Insert buttons in the header
- Hidden textarea containing the raw code

```html
<div class="code-block" id="code-block-1">
    <div class="code-header">
        <span class="code-language">python</span>
        <div class="code-buttons">
            <button class="code-button copy-button" onclick="copyCode('code-block-1')">
                Copy
            </button>
            <button class="code-button insert-button" onclick="insertCode('code-block-1')">
                Insert
            </button>
        </div>
    </div>
    <div class="code-content">
        <!-- Syntax highlighted code here -->
    </div>
    <textarea class="code-source" style="display: none;" id="code-block-1-source">
        <!-- Raw code stored here -->
    </textarea>
</div>
```

### 2. JavaScript Functions (markdown_renderer.py)

Simple, straightforward implementations:

#### Copy Function
```javascript
function copyCode(blockId) {
    var sourceElement = document.getElementById(blockId + '-source');
    var code = sourceElement.value;
    
    navigator.clipboard.writeText(code).then(function() {
        showCopySuccess();
    }).catch(function(error) {
        showNotification('Failed to copy', 'error');
    });
}
```

#### Insert Function
```javascript
function insertCode(blockId) {
    var sourceElement = document.getElementById(blockId + '-source');
    var code = sourceElement.value;
    
    // Send to Python via URL
    window.location.href = 'thonny:insert:' + encodeURIComponent(code);
}
```

### 3. URL Handling (chat_view_html.py)

Python intercepts the custom URL scheme:

```python
def _handle_url_change(self, url):
    if url.startswith("thonny:insert:"):
        code = urllib.parse.unquote(url[14:])
        
        editor = get_workbench().get_editor_notebook().get_current_editor()
        if editor:
            text_widget = editor.get_text_widget()
            text_widget.insert("insert", code)
            text_widget.focus_set()
```

## Requirements

- Basic tkinterweb installation: `pip install tkinterweb`
- No additional dependencies needed

## User Experience

1. **Copy Button**: 
   - Uses browser's Clipboard API
   - Shows "Code copied!" notification
   - Simple and reliable

2. **Insert Button**:
   - Inserts code directly into Thonny editor
   - Shows success notification
   - Falls back gracefully if no editor is open