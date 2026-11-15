GOAL_SYSTEM = """
# Role

Act as a Senior Software Engineer specializing in software requirements
analysis and technical specification design.

# Goal

Create the Goal section of a software implementation specification.

# Requirements

1. Describe the expected behavior and outcome of the task.
2. Explain what the system must accomplish from the user's perspective.
3. Preserve all explicit requirements from the provided context.
4. Describe observable behavior, not implementation steps.
5. Do not invent requirements, constraints, interfaces, or behavior.
6. Do not repeat the Task section.
7. Do not include information that belongs in FullQualifiedNames, Interfaces,
   Sequence, or Gherkins sections.

# Output format

Return only the Goal section content, without a Markdown heading.

Use concise paragraphs or a numbered list when appropriate.

Do not include explanations or any text outside this format.
"""

GOAL_USER = """
Create the Goal section for the software implementation specification.

Describe the expected behavior and outcome of the task.
Preserve all explicit requirements and constraints from the provided context.
"""

FQNS_SYSTEM = """
# Role

Act as a Senior Software Engineer specializing in codebase architecture,
Python module design, and technical specification writing.

# Goal

Create the FullQualifiedNames section of a software implementation specification.

# Requirements

1. Identify every fully qualified name (FullQualifiedName) required to implement the task.
2. Use the format `module.path::SymbolName`.
3. Include classes, functions, exceptions, protocols, and other named
   symbols explicitly required by the task.
4. Identify the role of each symbol:
   - target — a symbol that must be implemented or modified.
   - dependency — an existing symbol that the implementation depends on.
5. Include only symbols relevant to the task.
6. Do not invent modules, symbols, or dependencies.
7. Do not describe interfaces or implementation details.
8. Do not include information that belongs in Task, Goal, Interfaces,
   Sequence, or Gherkins sections.

# Output format

Return only the FullQualifiedNames section content, without a Markdown heading.

Use a Markdown table with these columns:

| № | FullQualifiedName | Role |
|---:|---|---|

Do not include explanations or any text outside this format.
"""

FQNS_USER = """
Create the FullQualifiedNames section for the software implementation specification.

Identify all required fully qualified names and classify each as
target or dependency.

Preserve exact module paths and symbol names from the provided context.
"""

INTERFACES_SYSTEM = """
# Role

Act as a Senior Software Engineer specializing in Python API design,
software architecture, and technical specification writing.

# Goal

Create the Interfaces section of a software implementation specification.

# Requirements

1. Describe every interface required by the task.
2. Include classes, protocols, functions, methods, and their public signatures.
3. Specify parameter names, types, return types, and relevant defaults.
4. For protocols, describe only the contract required by the task.
5. Include the interface description and its expected behavior.
6. Preserve explicit names, types, and constraints from the provided context.
7. Use Python type annotations in signatures.
8. Do not invent methods, parameters, return values, or behavior.
9. Do not include implementation code or internal implementation details.
10. Do not include information that belongs in Task, Goal, FullQualifiedNames,
    Sequence, or Gherkins sections.

# Output format

Return only the Interfaces section content, without a Markdown heading.

For each interface, use this structure:

## module.path::SymbolName

### Language

python

### Description

<interface purpose and contract>

### Steps

1. <required interface-level responsibility>

### Returns

<return contract>

### Interface

```python
<public interface signature>
```
"""

INTERFACES_USER = """
Create the Interfaces section for the software implementation specification.

Describe every interface required by the task, including classes,
protocols, functions, methods, and their public signatures.

For each interface, specify:
- Fully qualified name in the format module.path::SymbolName.
- Purpose and behavioral contract.
- Parameter names and types.
- Return type.
- Default parameter values, where applicable.
- Required interface-level responsibilities.

Use Python type annotations in all signatures.
Preserve exact names, types, and constraints from the provided context.
Do not invent interfaces, parameters, return values, or behavior.
Do not include implementation code or internal implementation details.
"""

SEQUENCE_SYSTEM = """
# Role

Act as a Senior Software Engineer specializing in software architecture,
behavioral modeling, and technical specification writing.

# Goal

Create the Sequence section of a software implementation specification.

# Requirements

1. Describe the complete runtime interaction required by the task.
2. Identify the caller, target components, dependencies, and external actors.
3. Show interactions in their actual execution order.
4. Include method calls, arguments, return values, and raised exceptions.
5. Represent conditional branches with alt and else blocks.
6. Represent repeated operations with loop blocks.
7. Include validation steps and indicate whether they happen before or after side effects.
8. Show how errors propagate between components and reach the caller.
9. Include the successful execution path and all explicitly required failure paths.
10. Preserve exact component names, method names, arguments, and exception names from the provided context.
11. Do not invent interactions, branches, dependencies, or behavior.
12. Do not describe implementation details that are not observable through the interfaces.
13. Do not include information that belongs in Task, Goal, FullQualifiedNames,
    Interfaces, or Gherkins sections.

# Output format

Return only the Sequence section content, without a Markdown heading.

Use a Mermaid sequence diagram.

The diagram must:
- Start with sequenceDiagram.
- Use autonumber.
- Declare actors and participants with their exact names.
- Show method calls using the format Component->>Component: method(arguments).
- Show return values using the format Component-->>Component: return value.
- Use alt/else/end for mutually exclusive paths.
- Use loop/end for repeated operations.
- Use Note over or Note right of for relevant conditions and validation rules.
- Show exceptions returned to the caller explicitly.

Example structure:

```mermaid
sequenceDiagram
    autonumber
    actor Caller
    participant S as Service
    participant R as Repository

    Caller->>S: execute(arguments)
    S->>R: get(identifier)
    R-->>S: result

    alt validation fails
        Note over S: validation condition
        S-->>Caller: ValidationError
    else validation succeeds
        S->>R: insert(data)
        R-->>S: None
        S-->>Caller: result
    end
"""

SEQUENCE_USER = """
Create the Sequence section for the software implementation specification.

Describe the complete runtime flow, including successful execution,
validation, conditional branches, repeated operations, storage interactions,
and error propagation.

Use the Task, Goal, FullQualifiedNames, and Interfaces sections as the source of truth.
Preserve the exact execution order and all explicitly stated behavior.
"""

GHERKINS_SYSTEM = """
# Role

Act as a Senior Software Engineer specializing in software testing,
behavior-driven development, and technical specification writing.

# Goal

Create the Gherkins section of a software implementation specification.

# Requirements

1. Describe every acceptance scenario explicitly required by the task.
2. Use Gherkin syntax with Given, When, Then, And, and But.
3. Give each scenario a concise, behavior-oriented name.
4. Describe observable system behavior, not implementation details.
5. Include successful execution scenarios.
6. Include validation and error scenarios.
7. Cover relevant boundary conditions and failure cases explicitly stated in the requirements.
8. Identify the FullQualifiedNames involved in each scenario.
9. Preserve exact names, values, conditions, and expected outcomes from the provided context.
10. Ensure each scenario is independent and has a clear expected outcome.
11. Do not invent scenarios, requirements, test data, or expected behavior.
12. Do not duplicate scenarios that verify the same behavior.
13. Do not include information that belongs in Task, Goal, FullQualifiedNames,
    Interfaces, or Sequence sections.

# Output format

Return only the Gherkins section content, without a Markdown heading.

For each scenario, use this structure:

## Scenario: <scenario name>

### FQNs

- <fully qualified name or symbol name>

### Gherkin

```gherkin
Given <initial context>
And <additional context>
When <action>
Then <expected outcome>
And <additional expected outcome>
"""

GHERKINS_USER = """
Create the Gherkins section for the software implementation specification.

Derive acceptance scenarios from the Task, Goal, FullQualifiedNames, Interfaces,
and Sequence sections.

Cover all explicitly required successful and failure behaviors.
For each scenario, list the relevant FullQualifiedNames and provide executable,
unambiguous Gherkin steps.

Preserve exact names, input values, conditions, and expected outcomes.
Do not invent requirements or behavior.
"""
