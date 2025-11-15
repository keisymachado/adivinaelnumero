from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random
import uuid
from datetime import datetime
import uvicorn

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

# 🔥 NUEVO: Función para auto-inicializar el juego
def initialize_game():
    global current_game
    if not current_game:
        current_game = GameSession()
    return current_game

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

@app.post("/start", response_model=StartResponse)
async def start_game():
    """Inicia una nueva partida generando un número aleatorio"""
    global current_game
    
    current_game = GameSession()
    
    return StartResponse(
        message="Nueva partida iniciada. ¡Adivina el número entre 1 y 100!",
        game_id=current_game.game_id
    )

@app.get("/start", response_model=StartResponse)
async def start_game_get():
    """Inicia una nueva partida (GET para navegador)"""
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
    
    # 🔥 NUEVO: Si no hay partida, crea una automáticamente
    if not current_game:
        current_game = GameSession()
    
    if current_game.completed:
        raise HTTPException(
            status_code=400, 
            detail="Esta partida ya fue completada. Inicia una nueva con /start o /new"
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

# 🔥 NUEVO: Endpoint para reiniciar fácilmente
@app.get("/new")
async def new_game():
    """Inicia una nueva partida (fácil desde navegador)"""
    global current_game
    current_game = GameSession()
    
    return {
        "message": "🎯 ¡Nueva partida iniciada!",
        "instruction": "Adivina el número entre 1 y 100 usando: /guess?number=TU_NUMERO",
        "student": "Keisy"
    }

@app.get("/")
async def root():
    """Página principal con instrucciones para jugar"""
    global current_game
    
    # Auto-inicializar si no hay juego
    if not current_game:
        current_game = GameSession()
    
    return {
        "message": "🎯 Adivina el Número API - Keisy", 
        "student": "Keisy",
        "current_game": {
            "active": True,
            "attempts": current_game.attempts,
            "completed": current_game.completed
        },
        "instructions": {
            "jugar_ahora": "Ve a /guess?number=50 para empezar a adivinar",
            "iniciar_nueva": "Ve a /new para nueva partida", 
            "ver_estado": "Ve a /status para ver progreso",
            "adivinar": "Usa /guess?number=X donde X es tu número"
        },
        "ejemplos": [
            "https://adivinaelnumero-production.up.railway.app/guess?number=50",
            "https://adivinaelnumero-production.up.railway.app/guess?number=25",
            "https://adivinaelnumero-production.up.railway.app/status"
        ]
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
    uvicorn.run(app, host="0.0.0.0", port=8000)