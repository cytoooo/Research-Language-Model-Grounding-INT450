from pydantic import BaseModel, Field
from typing import List, Optional
class GroundedNode(BaseModel):
    value: str
    source_quote: str
class HumanClarification(BaseModel):
    missing_entity: str
    question_for_human: str
class BusinessContextGraph(BaseModel):
    product: Optional[GroundedNode] = None
    persona: Optional[GroundedNode] = None
    operating_context: Optional[GroundedNode] = None
    stakeholder: Optional[GroundedNode] = None
    journeys: List[GroundedNode] = Field(default_factory=list)
    journey_steps: List[GroundedNode] = Field(default_factory=list)
    needs: List[GroundedNode] = Field(default_factory=list)
    requirements: List[GroundedNode] = Field(default_factory=list)
    # The escape valve for the agent
    human_questions: List[HumanClarification] = Field(default_factory=list)