from fastapi import FastAPI, Query,Body
from fastapi.responses import JSONResponse
from typing import Dict
import uvicorn
from WorkingGetRepoDetails import setup_handler
from WokringChatGptSummarizeAgent import summary_handler
app = FastAPI(title="Simple FastAPI App", description="Takes 2 inputs and returns a JSON", version="1.0.0")

@app.get("/extractrepo")
def process_inputs(token: str = Query(...), repojectid: str = Query(...)):
    """
    Accepts two query parameters and returns a combined message.
    """
    return setup_handler(token, repojectid)

@app.post("/getsummary")
def submit_data(data: Dict = Body(...)):
    """
    Accepts a dictionary (JSON object) and returns it with a confirmation message.
    """
    return summary_handler(data)

if __name__ == "__main__":
    uvicorn.run("MainApp:app", host="127.0.0.1", port=8000, reload=True)
