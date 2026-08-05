from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SkillInput(BaseModel):
    name: str = Field(..., description="Name of the input parameter")
    type: str = Field(..., description="Data type of the input (e.g., 'string', 'integer', 'boolean')")
    description: Optional[str] = Field(None, description="Description of the input parameter")
    required: bool = Field(True, description="Whether the input parameter is required")

class SkillOutput(BaseModel):
    name: str = Field(..., description="Name of the output parameter")
    type: str = Field(..., description="Data type of the output")
    description: Optional[str] = Field(None, description="Description of the output parameter")

class SkillDefinition(BaseModel):
    skill_id: str = Field(..., description="Unique identifier for the skill")
    name: str = Field(..., description="Human-readable name of the skill")
    description: str = Field(..., description="Detailed description of what the skill does")
    version: str = Field("1.0", description="Version of the skill")
    author: str = Field(..., description="Author of the skill")
    required_capabilities: List[str] = Field([], description="List of agent capabilities required to execute this skill")
    input_schema: List[SkillInput] = Field([], description="Schema defining the required inputs for the skill")
    output_schema: List[SkillOutput] = Field([], description="Schema defining the outputs produced by the skill")
    underlying_workflow: Dict[str, Any] = Field(..., description="The Task DAG or reference to a workflow definition for this skill")

class SkillExecutionRequest(BaseModel):
    skill_id: str = Field(..., description="ID of the skill to execute")
    inputs: Dict[str, Any] = Field({}, description="Input parameters for the skill")

class SkillExecutionResult(BaseModel):
    skill_id: str = Field(..., description="ID of the executed skill")
    status: str = Field(..., description="Status of the skill execution (e.g., 'SUCCESS', 'FAILED', 'RUNNING')")
    output: Optional[Dict[str, Any]] = Field(None, description="Output produced by the skill")
    task_id: Optional[str] = Field(None, description="Root TaskID of the workflow initiated by the skill")
