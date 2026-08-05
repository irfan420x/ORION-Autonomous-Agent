#!/bin/bash
# ORION Stability Check Script
# Run this at the end of every coding session.

echo "====================================="
echo "   ORION STABILITY CHECK INITIATED   "
echo "====================================="

# 1. Check Python syntax
echo "[1/4] Checking Python syntax..."
find ./orion -name "*.py" -exec python3 -m py_compile {} \;
if [ $? -eq 0 ]; then
    echo "✅ Python syntax OK."
else
    echo "❌ Python syntax errors found!"
    exit 1
fi

# 2. Check TOML/YAML configs
echo "[2/4] Checking configuration files..."
# Basic check to ensure files exist
if [ -f "pyproject.toml" ] && [ -d "config" ]; then
    echo "✅ Config files present."
else
    echo "❌ Config files missing!"
    exit 1
fi

# 3. Run Pytest (if available)
echo "[3/4] Running unit tests..."
if command -v pytest &> /dev/null; then
    pytest tests/ --maxfail=1 --disable-warnings -q
    if [ $? -eq 0 ] || [ $? -eq 5 ]; then # 5 means no tests collected, which is fine initially
        echo "✅ Tests passed (or no tests yet)."
    else
        echo "❌ Tests failed!"
        exit 1
    fi
else
    echo "⚠️ pytest not installed. Skipping test execution."
fi

# 4. Check Rust compilation (if cargo is available and Rust code exists)
echo "[4/4] Checking Rust compilation..."
if [ -d "orion-rs" ] && command -v cargo &> /dev/null; then
    cd orion-rs && cargo check
    if [ $? -eq 0 ]; then
        echo "✅ Rust code compiles."
    else
        echo "❌ Rust compilation failed!"
        exit 1
    fi
    cd ..
else
    echo "⚠️ Rust environment not found or no Rust code yet. Skipping."
fi

echo "====================================="
echo "   STABILITY CHECK PASSED! 🚀        "
echo "====================================="
exit 0
