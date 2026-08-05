"""# CLAUDE.md - Skill System

## 1. Overview
ORION's Skill System allows the agent to execute high-level, predefined workflows that encapsulate complex tasks. These skills are modular, reusable, and can be dynamically discovered and executed, enabling ORION to perform sophisticated operations with a single command.

## 2. Components
- **SkillManager (`skill_manager.py`):** Discovers, loads, and manages available skills. It validates skill definitions and provides an interface for skill execution.
- **SkillExecutor (`skill_executor.py`):** Responsible for initiating the execution of a skill's underlying workflow (Task DAG) via the Workflow Engine.

## 3. Interfaces (Contracts)
Skill-related data structures are defined in `orion/contracts/skill_contracts.py`.

### 3.1 SkillManager Interface
- `async load_skills(path: str)`: Discovers and loads skill definitions from a specified directory.
- `async get_available_skills() -> List[SkillDefinition]`: Returns a list of all loaded skills.
- `async execute_skill(skill_id: str, inputs: Dict[str, Any]) -> TaskID`: Initiates the execution of a skill and returns the root TaskID.

## 4. Dependencies
- **Internal:** `orion.contracts.skill_contracts`, `orion.contracts.agent_contracts`, `orion.core.communication.event_bus`, `orion.intelligence.planning.planning_engine`
- **External:** `asyncio`, `pyyaml` (for skill definition files).

## 5. Build Order & Verification (Phase 4 - M4.2)
1. Define skill-related Pydantic models in `orion/contracts/skill_contracts.py`.
2. Implement `SkillManager` to load skills from YAML files and manage their lifecycle.
3. Implement `SkillExecutor` to trigger `PlanningEngine` with a skill's workflow.
4. Create a sample skill definition file (`skills/sample_skill.yaml`).
5. Create a demo script (`examples/skill_system_demo.py`) to demonstrate loading and executing a skill.
6. Ensure unit tests for `SkillManager` and `SkillExecutor` pass.
"""
