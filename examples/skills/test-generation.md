---
name: test-generation
description: Generate comprehensive unit and integration tests
tags: [testing, unit-tests, test-coverage, quality-assurance]
version: 1.0.0
dependencies: [read_file, write_file]
---

# Test Generation Skill

I will help you create comprehensive tests for your code. Here's my approach:

## Test Types

### Unit Tests
- Test individual functions/methods in isolation
- Mock dependencies
- Cover edge cases and error conditions
- Test both happy path and failure scenarios

### Integration Tests
- Test interaction between components
- Verify data flow through the system
- Test with real dependencies where appropriate

### Property-Based Tests
- Define properties that should always hold
- Generate test cases automatically
- Find edge cases you might not think of

## Test Coverage Areas

### Happy Path
- Test normal, expected usage
- Verify correct output for valid inputs

### Edge Cases
- Boundary values (min, max, zero, empty)
- Special characters and unicode
- Large inputs
- Null/None/undefined values

### Error Handling
- Invalid inputs
- Missing required parameters
- Type errors
- Exception scenarios

### State Changes
- Verify state transitions
- Check side effects
- Test cleanup and teardown

## Test Structure (AAA Pattern)
```
Arrange - Set up test data and preconditions
Act - Execute the code being tested
Assert - Verify the expected outcome
```

## Best Practices
- One assertion per test (when practical)
- Clear, descriptive test names
- Independent tests (no dependencies between tests)
- Fast execution
- Deterministic results (no flaky tests)
- Clean up resources after tests

## Test Naming Convention
```
test_<function>_<scenario>_<expected_result>

Examples:
- test_divide_by_zero_raises_error
- test_parse_valid_json_returns_dict
- test_authenticate_invalid_token_returns_none
```

Please provide the code you'd like me to write tests for, and I'll generate comprehensive test cases.
