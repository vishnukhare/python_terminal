import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Send, Cpu, HardDrive, Activity } from 'lucide-react';

interface Command {
  input: string;
  output: string;
  timestamp: Date;
  error?: boolean;
}

interface SystemInfo {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  current_directory: string;
}

function App() {
  const [commands, setCommands] = useState<Command[]>([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [systemInfo, setSystemInfo] = useState<SystemInfo>({
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0,
    current_directory: '/home/project'
  });
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [serverRunning, setServerRunning] = useState(false);

  const terminalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Check if Python server is running
  const checkServer = async () => {
    try {
      const response = await fetch('http://localhost:8001/health');
      setServerRunning(response.ok);
    } catch {
      setServerRunning(false);
    }
  };

  // Get system information
  const getSystemInfo = async () => {
    try {
      const response = await fetch('http://localhost:8001/system-info');
      if (response.ok) {
        const info = await response.json();
        setSystemInfo(info);
      }
    } catch (error) {
      console.error('Failed to get system info:', error);
    }
  };

  // Execute command
  const executeCommand = async (command: string) => {
    if (!command.trim()) return;

    setIsLoading(true);
    const newCommand: Command = {
      input: command,
      output: '',
      timestamp: new Date(),
      error: false
    };

    try {
      const response = await fetch('http://localhost:8001/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: command.trim() })
      });

      const result = await response.json();
      newCommand.output = result.output;
      newCommand.error = result.error;

      if (result.current_directory) {
        setSystemInfo(prev => ({ ...prev, current_directory: result.current_directory }));
      }
    } catch (error) {
      newCommand.output = `Error: Could not connect to terminal server. Make sure the Python backend is running.`;
      newCommand.error = true;
    }

    setCommands(prev => [...prev, newCommand]);
    setCommandHistory(prev => {
      const newHistory = [command, ...prev.filter(cmd => cmd !== command)].slice(0, 100);
      return newHistory;
    });
    setCurrentInput('');
    setHistoryIndex(-1);
    setIsLoading(false);
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      executeCommand(currentInput);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (historyIndex < commandHistory.length - 1) {
        const newIndex = historyIndex + 1;
        setHistoryIndex(newIndex);
        setCurrentInput(commandHistory[newIndex] || '');
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        setCurrentInput(commandHistory[newIndex] || '');
      } else if (historyIndex === 0) {
        setHistoryIndex(-1);
        setCurrentInput('');
      }
    }
  };

  // Auto-scroll to bottom
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [commands]);

  // Focus input on mount and clicks
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Check server status and get system info
  useEffect(() => {
    checkServer();
    const interval = setInterval(() => {
      checkServer();
      if (serverRunning) {
        getSystemInfo();
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [serverRunning]);

  // Welcome message
  useEffect(() => {
    setCommands([{
      input: 'system',
      output: `Welcome to PyTerminal v1.0
Python-based Command Terminal

Available commands:
• File operations: ls, cd, pwd, mkdir, rm, cp, mv, cat, touch
• System monitoring: ps, top, df, free, uptime
• Utilities: echo, clear, help, whoami, date
• AI commands: ai "natural language request"

Type 'help' for detailed command information.
Type 'clear' to clear the terminal.
Use ↑/↓ arrows to navigate command history.`,
      timestamp: new Date()
    }]);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-green-400 font-mono">
      {/* Header */}
      <div className="border-b border-gray-700 bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-full mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Terminal className="w-6 h-6 text-green-400" />
              <h1 className="text-xl font-bold text-white">PyTerminal</h1>
              <div className={`px-2 py-1 rounded-full text-xs ${serverRunning ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                {serverRunning ? 'Connected' : 'Disconnected'}
              </div>
            </div>
            
            {/* System Info */}
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-1">
                <Cpu className="w-4 h-4" />
                <span>{systemInfo.cpu_usage.toFixed(1)}%</span>
              </div>
              <div className="flex items-center space-x-1">
                <Activity className="w-4 h-4" />
                <span>{systemInfo.memory_usage.toFixed(1)}%</span>
              </div>
              <div className="flex items-center space-x-1">
                <HardDrive className="w-4 h-4" />
                <span>{systemInfo.disk_usage.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Terminal */}
      <div className="max-w-full mx-auto p-6">
        <div className="bg-black/80 backdrop-blur-sm rounded-lg border border-gray-700 shadow-2xl">
          {/* Terminal Header */}
          <div className="flex items-center justify-between px-4 py-2 bg-gray-800/50 rounded-t-lg border-b border-gray-700">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            </div>
            <span className="text-gray-400 text-sm">Terminal</span>
          </div>

          {/* Terminal Content */}
          <div 
            ref={terminalRef}
            className="h-96 overflow-y-auto p-4 space-y-2"
            onClick={() => inputRef.current?.focus()}
          >
            {commands.map((command, index) => (
              <div key={index} className="space-y-1">
                {command.input !== 'system' && (
                  <div className="flex items-center space-x-2">
                    <span className="text-blue-400">user@pyterminal</span>
                    <span className="text-gray-500">:</span>
                    <span className="text-purple-400">{systemInfo.current_directory}</span>
                    <span className="text-gray-500">$</span>
                    <span className="text-white">{command.input}</span>
                  </div>
                )}
                {command.output && (
                  <pre className={`whitespace-pre-wrap ${command.error ? 'text-red-400' : 'text-green-300'} leading-relaxed`}>
                    {command.output}
                  </pre>
                )}
              </div>
            ))}

            {/* Current Input Line */}
            <div className="flex items-center space-x-2">
              <span className="text-blue-400">user@pyterminal</span>
              <span className="text-gray-500">:</span>
              <span className="text-purple-400">{systemInfo.current_directory}</span>
              <span className="text-gray-500">$</span>
              <input
                ref={inputRef}
                type="text"
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                onKeyDown={handleKeyPress}
                className="flex-1 bg-transparent text-white outline-none"
                placeholder={isLoading ? "Processing..." : "Type a command..."}
                disabled={isLoading || !serverRunning}
                autoFocus
              />
              {isLoading && (
                <div className="animate-spin w-4 h-4 border-2 border-green-400 border-t-transparent rounded-full"></div>
              )}
            </div>
          </div>
        </div>

        {/* Help Text */}
        <div className="mt-4 text-center text-gray-400 text-sm">
          {!serverRunning ? (
            <p>⚠️ Python terminal server not running. Please start the backend server.</p>
          ) : (
            <p>Terminal ready. Type 'help' for available commands or 'clear' to clear the screen.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;