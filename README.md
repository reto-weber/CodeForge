# Code Compiler and Runner

A modern web-based code compiler and runner built with FastAPI that supports multiple programming languages with advanced features like execution cancellation and timeout handling.

## 🚀 Features

- **Multi-language Support**: Python, C, C++, Java
- **Real-time Execution**: Non-blocking code execution with live status updates
- **Execution Control**: Cancel running processes and configurable timeouts (5-300 seconds)
- **Modern UI**: Clean, responsive web interface with syntax highlighting
- **Configurable**: JSON-based compiler configuration system
- **Example Library**: Built-in code examples for all supported languages
- **Secure**: Temporary file handling and process isolation
- **Verbose Output**: Detailed compilation and runtime information

## 🏗️ Architecture

- **Backend**: FastAPI with Jinja2 templates
- **Frontend**: Vanilla JavaScript with responsive CSS
- **Process Management**: Background threading with real-time status polling
- **Configuration**: JSON-based compiler settings
- **Security**: Sandboxed execution with timeout protection

## 📋 Requirements

- Python 3.7+
- GCC (for C/C++ compilation)
- Java JDK (for Java compilation)
- Modern web browser
- Linux/WSL/macOS (Windows supported via WSL)

## 🔧 Installation

### Quick Setup (Linux/WSL)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ap_online
   ```

2. **Run automated setup**:
   ```bash
   ./scripts/setup.sh
   ```

3. **Start the application**:
   ```bash
   ./run.sh
   # or
   ./scripts/start.sh
   ```

### Manual Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ap_online
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install development tools** (Ubuntu/Debian):
   ```bash
   sudo apt update
   sudo apt install build-essential default-jdk
   ```

### Docker Setup (Optional)

For containerized execution:
```bash
./setup-docker.sh
```

## 📜 Available Scripts

- `./setup.sh` - Complete project setup with dependencies
- `./start.sh` - Quick start (handles venv activation and starts server)
- `./setup-docker.sh` - Docker environment setup

## 🚀 Usage

### Quick Start
```bash
./start.sh
```

### Manual Start
1. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Start the server**:
   ```bash
   python3 main.py
   # or
   ./start.sh
   ```

3. **Open your browser** and navigate to:
   ```
   http://localhost:8000
   ```

4. **Write or select code**:
   - Choose a programming language
   - Write code in the editor or select from examples
   - Set execution timeout (5-300 seconds, default: 30s)

5. **Run and control execution**:
   - Click "Run Code" to execute
   - Use "Cancel" button to stop long-running processes
   - View real-time execution status and output

## ⚙️ Configuration

The compiler settings are stored in `config/compiler_config.json`:

```json
{
    "compilers": {
        "python": {
            "compile_cmd": "",
            "run_cmd": "python {file}"
        },
        "c": {
            "compile_cmd": "gcc {file} -o {output}",
            "run_cmd": "{output}"
        },
        "cpp": {
            "compile_cmd": "g++ {file} -o {output}",
            "run_cmd": "{output}"
        },
        "java": {
            "compile_cmd": "javac {file}",
            "run_cmd": "java {classname}"
        }
    },
    "default_language": "python"
}
```

## 📁 Project Structure

```
ap_online/
├── README.md                # Project documentation
├── REFACTOR_PLAN.md        # File structure refactor documentation
├── requirements.txt        # Python dependencies
├── run.sh                  # Convenience script to start server
├── .gitignore             # Git ignore patterns
├── .vscode/               # VS Code configuration
├── src/                   # Application source code
│   ├── __init__.py        # Python package init
│   ├── main.py            # FastAPI application
│   ├── container_manager.py # Docker container management
│   ├── config/
│   │   └── compiler_config.json # Compiler configuration
│   ├── static/            # Static web assets
│   │   ├── favicon.svg    # Application favicon
│   │   ├── css/
│   │   │   └── styles.css # Application styling
│   │   └── js/
│   │       └── script.js  # Frontend JavaScript
│   └── templates/
│       └── index.html     # Main HTML template
├── scripts/               # Setup and utility scripts
│   ├── setup.sh          # Project setup script
│   ├── setup-docker.sh   # Docker setup script
│   ├── start.sh          # Server startup script
│   └── test_setup.py     # Setup testing script
├── docker/               # Docker configuration
│   ├── Dockerfile        # Main application container
│   ├── Dockerfile.execution # Code execution container
│   └── docker-compose.yml # Docker compose configuration
├── examples/             # Code examples organized by language
│   ├── examples_index.json # Example metadata
│   ├── python/           # Python examples
│   │   ├── hello_world.py
│   │   ├── calculator.py
│   │   ├── fibonacci.py
│   │   └── infinite_loop.py
│   ├── c/               # C examples
│   │   ├── hello_world.c
│   │   ├── calculator.c
│   │   └── infinite_loop.c
│   ├── cpp/             # C++ examples
│   │   ├── hello_world.cpp
│   │   └── calculator.cpp
│   └── java/            # Java examples
│       ├── HelloWorld.java
│       └── Calculator.java
└── venv/                # Virtual environment (git-ignored)
```

## 🔒 Security Features

- **Process Isolation**: Each execution runs in a separate subprocess
- **Timeout Protection**: Configurable execution timeouts prevent infinite loops
- **Temporary Files**: Automatic cleanup of generated files
- **Graceful Termination**: Proper process cleanup with fallback to force kill
- **Input Validation**: Sanitized file paths and commands

## 🛠️ API Endpoints

- `GET /` - Main application interface
- `POST /run` - Execute code (returns execution_id immediately)
- `POST /cancel` - Cancel running execution
- `GET /status/{execution_id}` - Get execution status
- `POST /compile` - Compile code (for compiled languages)
- `GET /config` - Get compiler configuration
- `POST /config` - Update compiler configuration
- `GET /examples` - List available examples
- `GET /examples/{language}/{filename}` - Get example code

## 🔧 Advanced Features

### Execution Control

- **Non-blocking execution**: Run code without freezing the UI
- **Real-time status**: Live updates on execution progress
- **Cancellation**: Stop long-running or infinite loop processes
- **Timeout handling**: Automatic termination after specified duration

### Process Management

- **Background threading**: Executions run in separate threads
- **Process tracking**: Active process monitoring and cleanup
- **Graceful termination**: SIGTERM followed by SIGKILL if needed
- **Resource cleanup**: Automatic temporary file removal

## 🐛 Troubleshooting

### Common Issues

1. **Compilation errors**: Ensure required compilers are installed and in PATH
2. **Permission errors**: Check file system permissions for temporary directories
3. **Process hanging**: Use the cancel button or check timeout settings
4. **Port conflicts**: Change the port in `main.py` if 8000 is occupied

### Debug Mode

Run with debug logging:

```bash
python main.py --debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is open source. Please check the license file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- The open source community for compiler tools
- Contributors and testers

## Features

- **Multi-language Support**: Python, C, C++, Java (easily extensible)
- **Web-based Editor**: Clean, responsive textarea for code input
- **Configurable Compilation**: Customize compilation commands via JSON configuration
- **Verbose Output**: Detailed compilation and execution feedback
- **Real-time Execution**: Compile and run code with immediate feedback
- **Configuration Management**: Built-in config editor for customizing compiler settings

## Prerequisites

- Python 3.7+
- Compilers for desired languages:
  - `gcc` for C
  - `g++` for C++
  - `javac` and `java` for Java
  - Python (for Python code execution)

## Installation

1. Clone or download this project
2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python main.py
```

4. Open your browser and navigate to `http://localhost:8000`

## Usage

### Writing and Running Code

1. Select your programming language from the dropdown
2. **Load Examples**: Use the examples dropdown to load pre-built code examples for learning and testing
3. Write your code in the textarea (or load an example)
4. Use the action buttons:
   - **Compile**: Compile the code (for compiled languages)
   - **Run**: Execute the code directly
   - **Compile & Run**: Compile then execute (recommended for compiled languages)

### Available Examples

The application includes example programs for each supported language:

**Python Examples:**

- Hello World: Basic syntax, variables, and print statements
- Simple Calculator: Functions, parameters, and arithmetic operations
- Fibonacci Sequence: Loops, lists, and mathematical calculations

**C Examples:**

- Hello World: Basic C syntax and printf statements
- Simple Calculator: Functions and modular programming

**C++ Examples:**

- Hello World: Basic C++ syntax, iostream, and STL containers  
- OOP Calculator: Classes, objects, and object-oriented programming

**Java Examples:**

- Hello World: Basic Java syntax, arrays, and string operations
- OOP Calculator: Classes, objects, and object-oriented programming

### Configuration

The application uses a JSON configuration file at `config/compiler_config.json` to define:

- Compilation commands for each language
- Execution commands for each language
- Default language selection

#### Default Configuration

```json
{
    "compilers": {
        "python": {
            "compile_cmd": "",
            "run_cmd": "python {file}"
        },
        "c": {
            "compile_cmd": "gcc {file} -o {output} -Wall",
            "run_cmd": "{output}"
        },
        "cpp": {
            "compile_cmd": "g++ {file} -o {output} -Wall -std=c++14",
            "run_cmd": "{output}"
        },
        "java": {
            "compile_cmd": "javac {file}",
            "run_cmd": "java -cp {file%/*} {classname}"
        }
    },
    "default_language": "python"
}
```

#### Configuration Variables

- `{file}`: Path to the source code file
- `{output}`: Path to the compiled executable
- `{classname}`: Java class name (extracted from code)

### Adding New Languages

To add support for a new language:

1. Edit `config/compiler_config.json`
2. Add a new entry under `compilers` with appropriate compile and run commands
3. Restart the application

Example for adding Go support:

```json
"go": {
    "compile_cmd": "go build -o {output} {file}",
    "run_cmd": "{output}"
}
```

## API Endpoints

- `GET /`: Main application interface
- `POST /compile`: Compile code
- `POST /run`: Execute code
- `GET /config`: Get current configuration
- `POST /config`: Update configuration

## Project Structure

```
├── main.py                     # FastAPI application
├── requirements.txt            # Python dependencies
├── config/
│   └── compiler_config.json    # Compiler configuration
├── app/
│   ├── templates/
│   │   └── index.html          # Main HTML template
│   └── static/
│       ├── css/
│       │   └── styles.css      # Application styles
│       └── js/
│           └── script.js       # Frontend JavaScript
└── .github/
    └── copilot-instructions.md # Copilot instructions
```

## Security Considerations

- Code execution uses temporary files that are cleaned up after use
- Subprocess execution is isolated
- Consider running in a containerized environment for production use
- Be cautious with user input validation in production environments

## Development

To run in development mode with auto-reload:

```bash
uvicorn main:app --reload
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.
