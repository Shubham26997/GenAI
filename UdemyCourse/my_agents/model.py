from typing import Optional
from pydantic import BaseModel, Field

class PromptOutput(BaseModel):

    step: str = Field(..., description="The particular step of the LLM structure")
    content: Optional[str] = Field(None, description="The Main content output from LLM for that particular step")
    tool: Optional[str] = Field(None, description="The tool used in case required to solve user query")
    input: Optional[str] = Field(None, description="Input to the tool used if it require")
