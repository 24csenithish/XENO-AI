# app/models/model_config.py
from pydantic import BaseModel
from typing import Optional

class LLMOptions(BaseModel):
    num_ctx: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 40
    repeat_penalty: Optional[float] = 1.1
    num_predict: Optional[int] = -1  # unlimited/default
