from pydantic import BaseModel

class HistoryPoint(BaseModel):
	time:str
	value:float
