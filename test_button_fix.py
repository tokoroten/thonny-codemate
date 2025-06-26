#!/usr/bin/env python3
"""
Test script to verify that Copy and Insert buttons work during message streaming
"""

import time
import threading
from thonnycontrib.thonny_local_ollama.ui.chat_view_html import LLMChatViewHTML
import tkinter as tk


def test_streaming_buttons():
    """Test that buttons remain clickable during streaming"""
    
    # Create a simple test window
    root = tk.Tk()
    root.title("Test Streaming Buttons")
    root.geometry("800x600")
    
    # Create the chat view
    chat_view = LLMChatViewHTML(root)
    chat_view.pack(fill=tk.BOTH, expand=True)
    
    # Add a test message with code
    chat_view._add_message("user", "Show me a Python hello world example")
    
    # Simulate streaming response
    def simulate_streaming():
        # Start processing
        chat_view._processing = True
        chat_view._current_message = ""
        chat_view.send_button.config(text="Stop", state=tk.NORMAL)
        
        # Simulate streaming tokens
        response_parts = [
            "Here's a simple Python hello world example:\n\n",
            "```python\n",
            "# This is a simple Hello World program\n",
            "print('Hello, World!')\n",
            "```\n\n",
            "This code will output: `Hello, World!` when you run it."
        ]
        
        for part in response_parts:
            if not chat_view._processing:
                break
            
            # Add token to queue (simulating LLM response)
            chat_view.message_queue.put(("token", part))
            time.sleep(0.5)  # Simulate delay between tokens
        
        # Complete the message
        chat_view.message_queue.put(("complete", None))
    
    # Start streaming in a separate thread
    thread = threading.Thread(target=simulate_streaming, daemon=True)
    thread.start()
    
    # Instructions
    instruction_label = tk.Label(
        root,
        text="Try clicking the Copy/Insert buttons while the message is streaming.\n" +
             "The buttons should remain clickable throughout the streaming process.",
        font=("Arial", 10),
        pady=10
    )
    instruction_label.pack(side=tk.TOP)
    
    root.mainloop()


if __name__ == "__main__":
    print("Testing button functionality during message streaming...")
    print("The Copy and Insert buttons should remain clickable while the assistant is typing.")
    test_streaming_buttons()