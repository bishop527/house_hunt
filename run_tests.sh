#!/bin/bash
# Test runner script for House Hunt project
# Usage: ./run_tests.sh [options]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}House Hunt Project - Test Suite${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not found${NC}"
    echo "Install test dependencies with:"
    echo "  pip install -r requirements-test.txt"
    exit 1
fi

# Parse command line arguments
COVERAGE=true
VERBOSE=true
MARKERS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --quiet)
            VERBOSE=false
            shift
            ;;
        --unit)
            MARKERS="-m unit"
            shift
            ;;
        --integration)
            MARKERS="-m integration"
            shift
            ;;
        --fast)
            MARKERS="-m 'not slow'"
            shift
            ;;
        --help)
            echo "Usage: ./run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  --no-coverage    Skip coverage reporting"
            echo "  --quiet          Less verbose output"
            echo "  --unit           Run only unit tests"
            echo "  --integration    Run only integration tests"
            echo "  --fast           Skip slow tests"
            echo "  --help           Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build pytest command
CMD="pytest"

if [ "$VERBOSE" = true ]; then
    CMD="$CMD -v"
else
    CMD="$CMD -q"
fi

if [ "$COVERAGE" = true ]; then
    CMD="$CMD --cov=. --cov-report=term-missing --cov-report=html"
fi

if [ -n "$MARKERS" ]; then
    CMD="$CMD $MARKERS"
fi

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
echo "Command: $CMD"
echo ""

if $CMD; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}All tests passed!${NC}"
    echo -e "${GREEN}========================================${NC}"

    if [ "$COVERAGE" = true ]; then
        echo ""
        echo -e "${YELLOW}Coverage report saved to: htmlcov/index.html${NC}"
    fi

    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}Tests failed!${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi