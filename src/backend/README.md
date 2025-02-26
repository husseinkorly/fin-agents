# Backend Service for fin-agents

This project implements a multi-agent system using Microsoft AutoGen with a FastAPI backend.

## Prerequisites

- Python 3.12 or higher
- UV package manager

## What is UV?

UV is a modern Python package manager and resolver, written in Rust. It's designed to be a faster, more reliable alternative to pip and other traditional Python package management tools. UV offers:

- Faster dependency resolution and installation
- Improved caching mechanisms
- Better compatibility handling
- Lock file support for reproducible environments

## Installation

### 1. [Install UV](https://docs.astral.sh/uv/getting-started/installation/#installation-methods)

```bash
# Using pip
pip install uv
```

### 2. Activate enviroment and install dependencies

```bash
# Create virtual environment
uv venv

# Activate on Windows
.venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

### 3. Run the application

```bash
# run FastAPI server
uv run app.py
```