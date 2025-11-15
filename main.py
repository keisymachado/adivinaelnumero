from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random
import uuid
from datetime import datetime
import uvicorn
import os

app = FastAPI(
    title="Adivina el Número API - Keisy",
    description="API para adivinar números entre 1 y 100 - Desarrollado por Keisy",
    version="1.0.0"
)

# Almacenamiento en memoria - una única partida activa
current_game = None

class GameSession:
    def __init__(self):
        self.game_id = str(uuid.uuid4())[:8]
        self.secret_number = random.randint(1, 100)
        self.attempts = 0
        self.created_at = datetime.now()
        self.completed = False
        self.guess_history = []

class StartResponse(BaseModel):
    message: str
    game_id: str
    range: str = "1-100"
    student: str = "Keisy"

class GuessResponse(BaseModel):
    result: str
    guess: int
    attempts: int
    student: str = "Keisy"

class StatusResponse(BaseModel):
    game_active: bool
    attempts_used: int
    range: str = "1-100"
    last_guess: int = None
    game_completed: bool
    student: str = "Keisy"

@app.get("/start", response_model=StartResponse)
async def start_game():
    """Inicia una nueva partida generando un número aleatorio"""
    global current_game
    
    current_game = GameSession()
    
    return StartResponse(
        message="Nueva partida iniciada. ¡Adivina el número entre 1 y 100!",
        game_id=current_game.game_id
    )

@app.get("/guess", response_model=GuessResponse)
async def make_guess(number: int):
    """Responde si el número es alto, bajo o correcto"""
    global current_game
    
    if not current_game:
        raise HTTPException(
            status_code=400, 
            detail="No hay partida activa. Inicia una con POST /start"
        )
    
    if current_game.completed:
        raise HTTPException(
            status_code=400, 
            detail="Esta partida ya fue completada. Inicia una nueva con POST /start"
        )
    
    if number < 1 or number > 100:
        raise HTTPException(
            status_code=400, 
            detail="El número debe estar entre 1 y 100"
        )
    
    current_game.attempts += 1
    current_game.guess_history.append(number)
    
    if number < current_game.secret_number:
        result = "bajo"
    elif number > current_game.secret_number:
        result = "alto"
    else:
        result = "correcto"
        current_game.completed = True
    
    return GuessResponse(
        result=result,
        guess=number,
        attempts=current_game.attempts
    )

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Muestra el estado actual de la partida"""
    global current_game
    
    if not current_game:
        return StatusResponse(
            game_active=False,
            attempts_used=0,
            game_completed=False
        )
    
    last_guess = current_game.guess_history[-1] if current_game.guess_history else None
    
    return StatusResponse(
        game_active=True,
        attempts_used=current_game.attempts,
        last_guess=last_guess,
        game_completed=current_game.completed
    )

@app.get("/")
async def root():
    return {
        "message": "🎯 Adivina el Número API", 
        "student": "Keisy",
        "description": "Adivina el número secreto entre 1 y 100",
        "endpoints": {
            "start": "POST /start - Inicia nueva partida",
            "guess": "GET /guess?number=X - Adivina el número", 
            "status": "GET /status - Estado de la partida",
            "docs": "GET /docs - Documentación interactiva"
        }
    }

@app.get("/debug")
async def debug_info():
    """Endpoint de debug (solo para desarrollo)"""
    global current_game
    if current_game:
        return {
            "secret_number": current_game.secret_number,
            "attempts": current_game.attempts,
            "completed": current_game.completed,
            "history": current_game.guess_history
        }
    return {"message": "No hay partida activa"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)