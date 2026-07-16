# Prompt Generator API Reference

> Generate agent-specific prompts

## Overview

**Prompt Generator** — компонент для генерации промптов агентов. Создаёт промпты на основе типа агента (operator/subagent) с учётом роли и vault path.

## Class: `PromptGenerator`

### Methods

```python
from meai.agents.prompt_generator import PromptGenerator

generator = PromptGenerator()

# Generate prompt
prompt = generator.generate_prompt(
    agent_id="seo-agent",
    agent_type="subagent",
    department="seo",
    role="SEO specialist for medical marketing",
    vault_path="./obsidian/agents/seo-agent"
)

print(prompt)
```

## Prompt Structure

### Operator Prompt

```
You are {agent_id}, an operator agent managing the {department} department.

Role: {role}

Your vault: {vault_path}

Responsibilities:
- Manage subagents
- Coordinate workflows
- Make strategic decisions
- Monitor performance

Communication:
- Use Event Bus for messaging
- Log events to Event Store
- Write to your vault for memory

Safety:
- Respect loop detection limits
- Handle timeouts gracefully
- Monitor context usage
```

### Subagent Prompt

```
You are {agent_id}, a subagent in the {department} department.

Role: {role}

Your vault: {vault_path}

Responsibilities:
- Execute assigned tasks
- Report to operator
- Log progress
- Maintain memory

Communication:
- Receive tasks via Event Bus
- Send updates to operator
- Write to your vault

Safety:
- Respect timeouts
- Handle errors gracefully
```

## Customization

```python
# Add custom instructions
prompt = generator.generate_prompt(
    agent_id="seo-agent",
    agent_type="subagent",
    department="seo",
    role="SEO specialist",
    vault_path="./vault",
    custom_instructions="""
Additional guidelines:
- Focus on medical terminology
- Follow HIPAA compliance
- Use data-driven approach
"""
)
```

## Best Practices

- Keep roles descriptive but concise
- Include domain-specific guidelines in custom_instructions
- Test prompts with actual agents
- Update prompts as system evolves

## See Also

- [Agent Factory API](agent-factory.md)
- [Tutorial: Creating First Agent](../tutorials/01-first-agent.md)
