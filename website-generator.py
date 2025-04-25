import os
import socket
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import webbrowser


load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash')

class ReusableTCPServer(TCPServer):
    """Custom TCP server with port reuse capability"""
    allow_reuse_address = True  # Critical for quick port recycling
    timeout = 2  # Shutdown faster on KeyboardInterrupt

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        if self.path not in ['/robots.txt', '/favicon.ico']:
            super().log_message(format, *args)

def generate_website(prompt):
    response = model.generate_content(f"""
    Create a complete website with:
    {prompt}
    
    Requirements:
    - Modern responsive design
    - Inline CSS/JS
    - Semantic HTML5
    - Accessibility features
    - Error prevention measures
    
    Output raw HTML only without markdown.
    """)
    return response.text



def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def serve_site(port=8000):
    if is_port_in_use(port):
        print(f"⚠️  Port {port} in use, trying alternative...")
        port += 1  # Fallback to next port
    
    try:
        with ReusableTCPServer(("", port), QuietHandler) as httpd:
            print(f"🌐 Serving at http://localhost:{port}")
            webbrowser.open(f"http://localhost:{port}/generated_site")
            
            # Graceful shutdown handling
            httpd.server_activate()
            httpd.serve_forever(poll_interval=0.5)
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"🔥 Failed to start on port {port}. Try:")
            print(f"1. Wait 30 seconds for OS to release port")
            print(f"2. Run 'lsof -i :{port}' to find blocking processes")
            print(f"3. Use 'kill -9 PID' on listed processes")
        else:
            raise



def save_website(code, output_dir="generated_site"):
    """Save generated code with necessary support files"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Clean Gemini output
    clean_code = code.replace("```html", "").replace("```", "").strip()
    
    # Write main HTML
    with open(output_path / "index.html", "w") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex,nofollow">
    <link rel="icon" href="data:,">
    <title>Generated Site</title>
{clean_code}
</html>""")

    # Create placeholder files
    (output_path / "robots.txt").write_text("User-agent: *\nDisallow: /")
    (output_path / "favicon.ico").write_bytes(b"")
    
    print(f"Website generated in {output_path}")



if __name__ == "__main__":
    try:
        prompt = input("💡 Describe your website: ")
        code = generate_website(prompt)
        save_website(code)
        serve_site()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")