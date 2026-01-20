# Installation Guide

## Resolving Dependency Conflicts

### CrewAI and LangChain Compatibility

CrewAI 0.28.8 requires `langchain>=0.1.10,<0.2.0`. If you encounter dependency conflicts:

1. **Recommended**: Let pip resolve dependencies automatically:
   ```bash
   pip install crewai==0.28.8
   pip install -r requirements.txt
   ```

2. **Or install in order**:
   ```bash
   pip install langchain>=0.1.10,<0.2.0
   pip install crewai==0.28.8
   pip install -r requirements.txt
   ```

3. **If conflicts persist**, use a fresh virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Common Issues

#### Issue: langchain version conflict
**Error**: `crewai 0.28.8 depends on langchain<0.2.0 and >=0.1.10`

**Solution**: Remove any pinned `langchain==0.1.0` and use `langchain>=0.1.10,<0.2.0`

#### Issue: pydantic version conflict
**Error**: Version conflicts with pydantic

**Solution**: CrewAI works with pydantic 2.x. Ensure `pydantic>=2.0.0`

#### Issue: ModuleNotFoundError: No module named 'pkg_resources'
**Error**: `ModuleNotFoundError: No module named 'pkg_resources'`

**Solution**: Install setuptools which provides pkg_resources:
```bash
pip install setuptools>=65.0.0
```

This is required for CrewAI's telemetry module. It's included in requirements.txt.

#### Issue: ImportError: cannot import name 'BaseTool' from 'crewai.tools'
**Error**: `ImportError: cannot import name 'BaseTool' from 'crewai.tools'`

**Solution**: `BaseTool` is not available in CrewAI 0.28.8. The code has been updated to:
- Make tool imports optional
- Use direct method calls instead of CrewAI tool wrappers
- Handle missing CrewAI components gracefully

This is already fixed in the codebase. The agents use a functional approach with direct method calls rather than requiring CrewAI tool wrappers.

### Verification

After installation, verify versions:
```bash
pip show crewai langchain pydantic
```

Expected output should show:
- `crewai`: 0.28.8
- `langchain`: >=0.1.10, <0.2.0
- `pydantic`: >=2.0.0

### Alternative: Let CrewAI Handle Dependencies

If you want CrewAI to manage its dependencies automatically:

```bash
# Install only CrewAI first
pip install crewai==0.28.8

# Then install other requirements (excluding langchain/pydantic)
pip install -r requirements.txt --no-deps
pip install crewai==0.28.8  # Reinstall to ensure compatibility
```

This ensures CrewAI's dependency resolver sets compatible versions.

