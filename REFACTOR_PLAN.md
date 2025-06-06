# File Structure Refactor Plan

## Current Issues
1. Duplicate container manager files
2. Scripts scattered in root directory
3. Mixed application and deployment concerns
4. Python cache files in version control

## Proposed New Structure
```
ap_online/
├── README.md
├── requirements.txt
├── .gitignore
├── .vscode/
├── .github/
├── .git/
├── src/                          # Application source code
│   ├── __init__.py
│   ├── main.py                   # FastAPI application
│   ├── container_manager.py      # Docker container management
│   ├── config/
│   │   └── compiler_config.json
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── favicon.svg
│       ├── css/
│       │   └── styles.css
│       └── js/
│           └── script.js
├── scripts/                      # Setup and deployment scripts
│   ├── setup.sh
│   ├── setup-docker.sh
│   ├── start.sh
│   └── test_setup.py
├── docker/                       # Docker-related files
│   ├── Dockerfile
│   ├── Dockerfile.execution
│   └── docker-compose.yml
├── examples/                     # Code examples
│   ├── examples_index.json
│   ├── python/
│   ├── c/
│   ├── cpp/
│   └── java/
└── venv/                        # Virtual environment (git-ignored)
```

## Benefits
1. Clear separation of concerns
2. Better organization for maintenance
3. Easier to understand for new developers
4. Follows Python project conventions
5. Cleaner root directory
