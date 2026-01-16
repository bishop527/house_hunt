#!/bin/bash
# run_tests.sh
# Test runner script for House Hunt project
#
# Usage:
#   ./run_tests.sh              # Run all tests with coverage
#   ./run_tests.sh --no-cov     # Run tests without coverage
#   ./run_tests.sh --unit       # Run only unit tests
#   ./run_tests.sh --fast       # Run tests, skip slow ones
#   ./run_tests.sh --clean      # Clean coverage data before running

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
COVERAGE=true
TEST_MARKER=""
CLEAN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cov|--no-coverage)
            COVERAGE=false
            shift
            ;;
        --unit)
            TEST_MARKER="-m unit"
            shift
            ;;
        --fast)
            TEST_MARKER="-m 'not slow'"
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./run_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-cov        Run tests without coverage"
            echo "  --unit          Run only unit tests"
            echo "  --fast          Skip slow tests"
            echo "  --clean         Clean coverage data before running"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh              # Full test suite with coverage"
            echo "  ./run_tests.sh --no-cov     # Tests only, no coverage"
            echo "  ./run_tests.sh --clean      # Clean and run tests"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Header
echo -e "${BLUE}========================================"
echo "House Hunt Project - Test Suite"
echo -e "========================================${NC}\n"

# Clean coverage data if requested
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}Cleaning old coverage data...${NC}"
    if [ -f "Tests/.coverage" ]; then
        rm Tests/.coverage
        echo -e "${GREEN}✓ Removed Tests/.coverage${NC}"
    fi
    if [ -d "Tests/htmlcov" ]; then
        rm -rf Tests/htmlcov
        echo -e "${GREEN}✓ Removed Tests/htmlcov/${NC}"
    fi
    if [ -d "Tests/.pytest_cache" ]; then
        rm -rf Tests/.pytest_cache
        echo -e "${GREEN}✓ Removed Tests/.pytest_cache/${NC}"
    fi
    echo ""
fi

# Set coverage data file location
export COVERAGE_FILE=Tests/.coverage

# Build pytest command
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="pytest $TEST_MARKER --cov=. --cov-report=html:Tests/htmlcov --cov-report=term-missing -v"
else
    PYTEST_CMD="pytest $TEST_MARKER --no-cov -v"
fi

# Run tests
echo -e "${BLUE}Running tests...${NC}"
echo "Command: $PYTEST_CMD"
echo "Coverage data file: $COVERAGE_FILE"
echo ""

if $PYTEST_CMD; then
    # Tests passed
    echo ""
    echo -e "${GREEN}========================================"
    echo "All tests passed!"
    echo -e "========================================${NC}\n"

    if [ "$COVERAGE" = true ]; then
        echo -e "${BLUE}Coverage report saved to: Tests/htmlcov/index.html${NC}"
        echo ""

        # Offer to open coverage report
        read -p "Open coverage report in browser? [y/N] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [ -f "Tests/htmlcov/index.html" ]; then
                # Try different commands based on OS
                if command -v open &> /dev/null; then
                    # macOS
                    open Tests/htmlcov/index.html
                elif command -v xdg-open &> /dev/null; then
                    # Linux
                    xdg-open Tests/htmlcov/index.html
                elif command -v start &> /dev/null; then
                    # Windows (Git Bash)
                    start Tests/htmlcov/index.html
                else
                    echo -e "${YELLOW}Could not open browser automatically.${NC}"
                    echo "Please open: Tests/htmlcov/index.html"
                fi
            else
                echo -e "${RED}Coverage report not found at Tests/htmlcov/index.html${NC}"
            fi
        fi
    fi

    exit 0
else
    # Tests failed
    echo ""
    echo -e "${RED}========================================"
    echo "Tests failed!"
    echo -e "========================================${NC}\n"

    if [ "$COVERAGE" = true ]; then
        echo -e "${YELLOW}Coverage report may still be available at: Tests/htmlcov/index.html${NC}"
    fi

    exit 1
fi