# Contributing to AI Document Repository

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## How to Contribute

### Reporting Bugs

1. Check if the bug already exists in Issues
2. Create a new issue with:
   - Clear title describing the bug
   - Detailed description of the behavior
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment info (OS, Python version, etc.)

### Suggesting Enhancements

1. Check if feature already exists in Issues
2. Create an issue with title starting with "[FEATURE]"
3. Provide clear description of the enhancement
4. Explain why this enhancement would be useful

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test your changes locally
5. Commit with clear messages: `git commit -m 'Add feature X'`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Create Pull Request with:
   - Clear title
   - Description of changes
   - Link to related issues
   - Testing information

## Adding New Tools

1. Create file in `tools/` directory
2. Use `@tool` decorator from LangChain
3. Include clear docstring
4. Handle errors gracefully
5. Return structured output

Example:
```python
from langchain.tools import tool

@tool
def my_tool(input) -> str:
    """Clear description of what this tool does."""
    try:
        # Implementation
        return result
    except Exception as e:
        return f"Error: {str(e)}"
```

## Code Style

- Follow PEP 8
- Use meaningful variable names
- Add comments for complex logic
- Keep functions small and focused

## Testing

Before submitting PR:
```bash
# Run locally
python main.py

# Test with sample queries
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions
- Include usage examples

## Questions?

- Open a GitHub Discussion
- Check existing Issues and Discussions
- Contact maintainer

Thank you for contributing! 🙏
