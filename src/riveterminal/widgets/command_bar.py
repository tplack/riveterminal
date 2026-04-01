"""Bloomberg-style command bar widget."""

from textual.widgets import Input
from textual.message import Message
from textual import events
from rich.text import Text


class CommandBar(Input):
    """Bloomberg-style command bar for navigation."""
    
    DEFAULT_CSS = """
    CommandBar {
        dock: top;
        height: 3;
        border: solid yellow;
        background: black;
        color: yellow;
    }
    
    CommandBar:focus {
        border: solid #FFFF00;
        background: #111111;
    }
    """
    
    class CommandEntered(Message):
        """Message sent when a command is entered."""
        
        def __init__(self, command: str) -> None:
            self.command = command.strip().upper()
            super().__init__()
    
    def __init__(self, **kwargs):
        super().__init__(placeholder="Enter command (e.g., AAPL, DASHBOARD, NEWS) and press ENTER", **kwargs)
        self.command_history = []
        self.history_index = -1
    
    async def on_key(self, event: events.Key) -> None:
        """Handle key events."""
        if event.key == "enter":
            command = self.value.strip()
            if command:
                # Add to history
                if command not in self.command_history:
                    self.command_history.append(command)
                    # Keep only last 50 commands
                    self.command_history = self.command_history[-50:]
                
                self.history_index = -1
                
                # Send command message
                await self.emit(self.CommandEntered(command))
                
                # Clear input
                self.value = ""
            
        elif event.key == "up":
            # Navigate command history up
            if self.command_history and self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.value = self.command_history[-(self.history_index + 1)]
                self.cursor_position = len(self.value)
            event.prevent_default()
            
        elif event.key == "down":
            # Navigate command history down
            if self.history_index > 0:
                self.history_index -= 1
                self.value = self.command_history[-(self.history_index + 1)]
                self.cursor_position = len(self.value)
            elif self.history_index == 0:
                self.history_index = -1
                self.value = ""
            event.prevent_default()
            
        else:
            await super().on_key(event)
    
    def set_command(self, command: str):
        """Set command value programmatically."""
        self.value = command
        self.cursor_position = len(command)