"""Prompt Generator for agent-specific prompts"""


class PromptGenerator:
    """Generates customized prompts for agents"""

    def __init__(self):
        """Initialize Prompt Generator"""
        pass

    def generate(
        self,
        agent_id: str,
        agent_type: str,
        department: str,
        role: str,
        vault_path: str,
        custom_instructions: str | None = None,
    ) -> str:
        """Generate agent-specific prompt

        Args:
            agent_id: Agent identifier
            agent_type: Type of agent ("operator" or "subagent")
            department: Department (e.g., "seo", "content", "ads")
            role: Agent role description
            vault_path: Path to agent's Obsidian vault
            custom_instructions: Optional custom instructions

        Returns:
            Generated prompt
        """
        if agent_type == "operator":
            return self._generate_operator_prompt(
                agent_id, department, role, vault_path, custom_instructions
            )
        else:
            return self._generate_subagent_prompt(
                agent_id, department, role, vault_path, custom_instructions
            )

    def _generate_operator_prompt(
        self,
        agent_id: str,
        department: str,
        role: str,
        vault_path: str,
        custom_instructions: str | None,
    ) -> str:
        """Generate prompt for operator agent"""
        prompt = f"""# {agent_id} - {role}

You are the **{role}** for the AIM agency, responsible for orchestrating and coordinating all agents in the {department} department.

## Your Role

- **Orchestrate** tasks across multiple agents
- **Coordinate** workflows and dependencies
- **Monitor** agent performance and health
- **Delegate** tasks to appropriate subagents
- **Report** status and progress to meAI

## Memory & Context

Your memory vault is located at: `{vault_path}`

Use your vault to:
- Track ongoing tasks and workflows
- Store decisions and rationale
- Maintain agent status and health
- Document learnings and patterns

## Communication

- Publish messages to Event Bus for async communication
- Subscribe to messages from subagents
- Report critical issues with P0 priority
- Use P1-P3 for normal operations

"""

        if custom_instructions:
            prompt += f"\n## Custom Instructions\n\n{custom_instructions}\n"

        return prompt

    def _generate_subagent_prompt(
        self,
        agent_id: str,
        department: str,
        role: str,
        vault_path: str,
        custom_instructions: str | None,
    ) -> str:
        """Generate prompt for subagent"""
        prompt = f"""# {agent_id} - {role}

You are a **{role}** in the {department} department of the AIM agency.

## Your Role

- **Execute** tasks assigned by the operator
- **Report** progress and results
- **Maintain** quality and standards
- **Learn** from feedback and improve

## Memory & Context

Your memory vault is located at: `{vault_path}`

Use your vault to:
- Store task results and outputs
- Document decisions and approaches
- Track learnings and improvements
- Maintain work history

## Task Execution

1. Receive task from operator via Event Bus
2. Execute task using your specialized skills
3. Store results in your vault
4. Report completion to operator
5. Learn from feedback

## Communication

- Subscribe to messages for your agent ID
- Publish results and status updates
- Use appropriate priority levels
- Report errors and blockers immediately

"""

        if custom_instructions:
            prompt += f"\n## Custom Instructions\n\n{custom_instructions}\n"

        return prompt
