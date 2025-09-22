#!/usr/bin/env python3
"""
Python Terminal Server - WebContainer Compatible Version
A simplified terminal emulator backend compatible with WebContainer's Python environment.
"""

import os
import json
import shutil
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

class TerminalSession:
    """Manages terminal session state"""
    
    def __init__(self):
        self.current_directory = os.getcwd()
        self.environment = os.environ.copy()
        self.command_history = []
        
    def change_directory(self, path):
        """Change current directory"""
        try:
            if path == "~":
                path = os.path.expanduser("~")
            elif path.startswith("~/"):
                path = os.path.expanduser(path)
            elif not os.path.isabs(path):
                path = os.path.join(self.current_directory, path)
            
            path = os.path.abspath(path)
            if os.path.exists(path) and os.path.isdir(path):
                self.current_directory = path
                os.chdir(path)
                return True, f"Changed to {path}"
            else:
                return False, f"Directory not found: {path}"
        except Exception as e:
            return False, f"Error changing directory: {str(e)}"

class CommandProcessor:
    """Processes and executes terminal commands"""
    
    def __init__(self, session):
        self.session = session
        self.builtin_commands = {
            'cd': self.cmd_cd,
            'pwd': self.cmd_pwd,
            'ls': self.cmd_ls,
            'mkdir': self.cmd_mkdir,
            'rm': self.cmd_rm,
            'cp': self.cmd_cp,
            'mv': self.cmd_mv,
            'cat': self.cmd_cat,
            'echo': self.cmd_echo,
            'touch': self.cmd_touch,
            'clear': self.cmd_clear,
            'help': self.cmd_help,
            'whoami': self.cmd_whoami,
            'date': self.cmd_date,
            'ps': self.cmd_ps,
            'df': self.cmd_df,
            'uptime': self.cmd_uptime,
            'ai': self.cmd_ai
        }
    
    def execute_command(self, command_line):
        """Execute a command and return result"""
        if not command_line.strip():
            return "", False
        
        # Add to history
        self.session.command_history.append({
            'command': command_line,
            'timestamp': datetime.now().isoformat(),
            'directory': self.session.current_directory
        })
        
        # Parse command
        parts = command_line.strip().split()
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        try:
            # Check for builtin commands
            if command in self.builtin_commands:
                return self.builtin_commands[command](args)
            else:
                return f"Command not found: {command}", True
        except Exception as e:
            return f"Error executing command: {str(e)}", True
    
    # Builtin command implementations
    def cmd_cd(self, args):
        """Change directory"""
        target = args[0] if args else os.path.expanduser("~")
        success, message = self.session.change_directory(target)
        return message, not success
    
    def cmd_pwd(self, args):
        """Print working directory"""
        return self.session.current_directory, False
    
    def cmd_ls(self, args):
        """List directory contents"""
        try:
            path = args[0] if args else '.'
            if not os.path.isabs(path):
                path = os.path.join(self.session.current_directory, path)
            
            items = []
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append(f"📁 {item}/")
                else:
                    try:
                        size = os.path.getsize(item_path)
                        items.append(f"📄 {item} ({self.format_size(size)})")
                    except:
                        items.append(f"📄 {item}")
            
            return "\n".join(items) or "Directory is empty", False
        except Exception as e:
            return f"ls: {str(e)}", True
    
    def cmd_mkdir(self, args):
        """Create directory"""
        if not args:
            return "mkdir: missing directory name", True
        
        try:
            for dirname in args:
                if not os.path.isabs(dirname):
                    dirname = os.path.join(self.session.current_directory, dirname)
                os.makedirs(dirname, exist_ok=True)
            return f"Created directories: {', '.join(args)}", False
        except Exception as e:
            return f"mkdir: {str(e)}", True
    
    def cmd_rm(self, args):
        """Remove files/directories"""
        if not args:
            return "rm: missing file or directory", True
        
        try:
            for item in args:
                if not os.path.isabs(item):
                    item = os.path.join(self.session.current_directory, item)
                
                if os.path.isdir(item):
                    shutil.rmtree(item)
                else:
                    os.remove(item)
            return f"Removed: {', '.join(args)}", False
        except Exception as e:
            return f"rm: {str(e)}", True
    
    def cmd_cp(self, args):
        """Copy files"""
        if len(args) < 2:
            return "cp: missing source or destination", True
        
        try:
            source, dest = args[0], args[1]
            if not os.path.isabs(source):
                source = os.path.join(self.session.current_directory, source)
            if not os.path.isabs(dest):
                dest = os.path.join(self.session.current_directory, dest)
            
            if os.path.isdir(source):
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)
            return f"Copied {args[0]} to {args[1]}", False
        except Exception as e:
            return f"cp: {str(e)}", True
    
    def cmd_mv(self, args):
        """Move/rename files"""
        if len(args) < 2:
            return "mv: missing source or destination", True
        
        try:
            source, dest = args[0], args[1]
            if not os.path.isabs(source):
                source = os.path.join(self.session.current_directory, source)
            if not os.path.isabs(dest):
                dest = os.path.join(self.session.current_directory, dest)
            
            shutil.move(source, dest)
            return f"Moved {args[0]} to {args[1]}", False
        except Exception as e:
            return f"mv: {str(e)}", True
    
    def cmd_cat(self, args):
        """Display file contents"""
        if not args:
            return "cat: missing filename", True
        
        try:
            filepath = args[0]
            if not os.path.isabs(filepath):
                filepath = os.path.join(self.session.current_directory, filepath)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read(), False
        except Exception as e:
            return f"cat: {str(e)}", True
    
    def cmd_echo(self, args):
        """Echo text"""
        return ' '.join(args), False
    
    def cmd_touch(self, args):
        """Create empty files"""
        if not args:
            return "touch: missing filename", True
        
        try:
            for filename in args:
                if not os.path.isabs(filename):
                    filename = os.path.join(self.session.current_directory, filename)
                
                with open(filename, 'a'):
                    pass
            return f"Created files: {', '.join(args)}", False
        except Exception as e:
            return f"touch: {str(e)}", True
    
    def cmd_clear(self, args):
        """Clear terminal"""
        return "CLEAR_TERMINAL", False
    
    def cmd_help(self, args):
        """Show help information"""
        help_text = """
PyTerminal Command Reference:

📁 File Operations:
  ls [dir]          - List directory contents
  cd <dir>          - Change directory
  pwd               - Print working directory
  mkdir <dir>       - Create directory
  rm <file/dir>     - Remove files/directories
  cp <src> <dest>   - Copy files
  mv <src> <dest>   - Move/rename files
  cat <file>        - Display file contents
  touch <file>      - Create empty file

🔧 Utilities:
  echo <text>       - Print text
  date              - Show current date/time
  whoami            - Show current user
  clear             - Clear terminal
  help              - Show this help

🤖 AI Commands:
  ai "<request>"    - Natural language command interpretation
                     Example: ai "create a folder called test"

💡 Tips:
  - Use ↑/↓ arrows for command history
  - Commands are executed in a Python environment
        """
        return help_text.strip(), False
    
    def cmd_whoami(self, args):
        """Show current user"""
        try:
            return os.getlogin()
        except:
            return 'user', False
    
    def cmd_date(self, args):
        """Show current date/time"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S"), False
    
    def cmd_ps(self, args):
        """Show running processes (simplified)"""
        return "Process monitoring not available in this environment", False
    
    def cmd_df(self, args):
        """Show disk usage (simplified)"""
        try:
            total, used, free = shutil.disk_usage('/')
            return f"""Disk Usage:
Total: {self.format_size(total)}
Used:  {self.format_size(used)} ({used/total*100:.1f}%)
Free:  {self.format_size(free)}""", False
        except Exception as e:
            return f"df: {str(e)}", True
    
    def cmd_uptime(self, args):
        """Show system uptime (simplified)"""
        return "System uptime information not available in this environment", False
    
    def cmd_ai(self, args):
        """AI-powered natural language command interpretation"""
        if not args:
            return "ai: Please provide a natural language request in quotes", True
        
        request = ' '.join(args).strip('"\'')
        
        # Simple AI-like interpretation using pattern matching
        import re
        
        ai_patterns = [
            (r'create.*folder.*called\s+(\w+)', lambda m: f"mkdir {m.group(1)}"),
            (r'make.*directory.*called\s+(\w+)', lambda m: f"mkdir {m.group(1)}"),
            (r'list.*files', lambda m: "ls"),
            (r'what.*time', lambda m: "date"),
            (r'who.*am.*i', lambda m: "whoami"),
            (r'where.*am.*i', lambda m: "pwd"),
            (r'create.*file.*called\s+(\w+)', lambda m: f"touch {m.group(1)}"),
            (r'remove.*file.*called\s+(\w+)', lambda m: f"rm {m.group(1)}"),
            (r'delete.*file.*called\s+(\w+)', lambda m: f"rm {m.group(1)}"),
            (r'copy.*(\w+).*to.*(\w+)', lambda m: f"cp {m.group(1)} {m.group(2)}"),
            (r'move.*(\w+).*to.*(\w+)', lambda m: f"mv {m.group(1)} {m.group(2)}"),
            (r'go.*to.*directory.*(\w+)', lambda m: f"cd {m.group(1)}"),
            (r'change.*directory.*to.*(\w+)', lambda m: f"cd {m.group(1)}"),
        ]
        
        for pattern, command_generator in ai_patterns:
            match = re.search(pattern, request.lower())
            if match:
                interpreted_command = command_generator(match)
                result, error = self.execute_command(interpreted_command)
                return f"🤖 Interpreted as: {interpreted_command}\n\n{result}", error
        
        return f"🤖 I couldn't interpret the request: '{request}'\n\nTry rephrasing or use one of these patterns:\n- 'create a folder called [name]'\n- 'list files'\n- 'copy [file1] to [file2]'\n- 'go to directory [name]'", False
    
    def format_size(self, bytes):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.1f}{unit}"
            bytes /= 1024.0
        return f"{bytes:.1f}PB"

class TerminalHandler(BaseHTTPRequestHandler):
    """HTTP request handler for terminal server"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        
        elif self.path == '/system-info':
            try:
                system_info = {
                    'cpu_usage': 0,
                    'memory_usage': 0,
                    'disk_usage': 0,
                    'current_directory': self.server.session.current_directory
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(system_info).encode())
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/execute':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                command = data.get('command', '')
                output, error = self.server.processor.execute_command(command)
                
                response = {
                    'output': output,
                    'error': error,
                    'current_directory': self.server.session.current_directory
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                error_response = {
                    'output': f'Server error: {str(e)}',
                    'error': True,
                    'current_directory': self.server.session.current_directory
                }
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(error_response).encode())
        else:
            self.send_error(404)

class TerminalServer(HTTPServer):
    """Custom HTTP server with terminal session"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = TerminalSession()
        self.processor = CommandProcessor(self.session)

def main():
    """Main function to start the terminal server"""
    print("🐍 PyTerminal Server Starting...")
    print("📡 Server will run on http://localhost:8001")
    print("🌐 Open the web interface to start using the terminal")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    server = TerminalServer(('localhost', 8001), TerminalHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
    finally:
        server.server_close()

if __name__ == '__main__':
    main()