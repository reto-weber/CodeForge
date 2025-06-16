# Tabbed File Editor Feature

## Overview
The online code compiler now supports a tabbed file editor interface that allows users to work with multiple files simultaneously. This is particularly useful for multi-file projects.

## Features

### File Management
- **Multiple Files**: Create and manage multiple code files in tabs
- **File Types**: Automatic language detection based on file extension
- **Tab Navigation**: Click on tabs to switch between files
- **Add Files**: Click the `+` button to create new files
- **Close Files**: Click the `×` button on any tab to close that file

### File Operations
- **Rename Files**: Double-click on a tab name to rename the file
- **Keyboard Shortcuts**:
  - `Ctrl+N` (or `Cmd+N` on Mac): Create new file
  - `Ctrl+W` (or `Cmd+W` on Mac): Close current file

### Language Detection
The system automatically detects the programming language based on file extensions:
- `.py` → Python
- `.c`, `.h` → C
- `.cpp`, `.hpp`, `.cc`, `.cxx`, `.c++` → C++
- `.java` → Java
- `.js`, `.jsx`, `.ts`, `.tsx` → JavaScript
- `.e`, `.ecf` → Eiffel
- `.txt`, `.md`, no extension → Python (default)

### Backend Integration
- **Multi-file Compilation**: The backend now supports receiving multiple files
- **Main File**: The system identifies which file should be used as the main entry point
- **Legacy Support**: Single-file mode is still supported for backwards compatibility

## Usage

1. **Creating Files**: Click the `+` button next to the tabs
2. **Switching Files**: Click on any tab to switch to that file
3. **Editing**: CodeMirror syntax highlighting adapts to the file type
4. **Renaming**: Double-click on a tab name to rename the file
5. **Closing**: Click the `×` on a tab to close the file (at least one file must remain open)
6. **Compilation/Execution**: Works with the currently active file or all files for multi-file projects

## Technical Implementation

### Frontend
- `FileManager` class handles all file operations
- Tab UI with CSS styling for professional appearance
- Event delegation for efficient tab management
- Integration with existing `CodeEditorManager`

### Backend
- Updated endpoints support both JSON (multi-file) and Form (legacy) requests
- `MultiFileRequest` model for structured multi-file data
- Automatic main file detection for execution

### Responsive Design
- Tabs adapt to smaller screens
- Mobile-friendly tab sizes and interactions

## File Structure
The tabbed editor maintains a map of files with the following structure:
```javascript
{
  id: 'unique_file_id',
  name: 'filename.ext',
  content: 'file_content',
  extension: 'ext',
  language: 'detected_language'
}
```

This feature enhances the coding experience by allowing developers to work with realistic multi-file projects directly in the web interface.
