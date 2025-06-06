<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Code Compiler and Runner Project

This is a Python FastAPI web application for compiling and running code in multiple programming languages. The application provides:

- A web interface with a code editor
- Support for multiple programming languages (Python, C, C++, Java)
- Configurable compilation commands via JSON configuration
- Verbose output display
- Real-time compilation and execution

## Key Features

- **Language Support**: Configured through `config/compiler_config.json`
- **Secure Execution**: Uses temporary files and subprocess isolation
- **Configurable Commands**: Both compilation and execution commands can be customized
- **Verbose Output**: Displays detailed compilation and runtime information
- **Modern UI**: Clean, responsive web interface

## Architecture

- **Backend**: FastAPI with Jinja2 templates
- **Frontend**: Vanilla JavaScript with responsive CSS
- **Configuration**: JSON-based compiler configuration
- **Security**: Temporary file handling and process isolation

When working with this codebase:
- Follow FastAPI best practices
- Maintain security when handling user input and code execution
- Keep the configuration system flexible and extensible
- Ensure proper error handling and verbose output
