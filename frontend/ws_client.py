import websocket
import json
from typing import Generator


class WebSocketClient:
    def __init__(self, url: str):
        self.url = url
        self.ws = None
    
    def connect(self):
        """Connect to WebSocket."""
        # Set very short timeout for real-time streaming
        self.ws = websocket.WebSocket()
        self.ws.settimeout(5)  # Shorter timeout for faster updates
        self.ws.connect(self.url)
    
    def send_question(self, question: str):
        """Send question to server."""
        message = {
            "question": question
        }
        self.ws.send(json.dumps(message))
    
    def receive_stream(self) -> Generator[dict, None, None]:
        """Receive streaming messages with minimal buffering for real-time display."""
        buffer = ""
        while True:
            try:
                # Receive data immediately without buffering
                raw_data = self.ws.recv()
                if not raw_data:
                    break
                
                # Handle partial JSON data
                buffer += raw_data if isinstance(raw_data, str) else raw_data.decode('utf-8')
                
                # Try to parse complete JSON messages
                try:
                    data = json.loads(buffer)
                    buffer = ""  # Clear buffer on successful parse
                    yield data
                    
                    if data.get("type") in ["done", "error"]:
                        break
                except json.JSONDecodeError:
                    # Incomplete JSON, wait for more data
                    continue
                    
            except websocket.WebSocketTimeoutException:
                # Timeout is normal for streaming, just continue
                continue
            except Exception as e:
                yield {"type": "error", "content": str(e)}
                break
    
    def close(self):
        """Close WebSocket connection."""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass


# Legacy class for backward compatibility
class WSClient(WebSocketClient):
    pass
