import os
import shutil
import uuid
import requests  
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles 
import edge_tts
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MOUNT STATIC FILES ---
app.mount("/static", StaticFiles(directory="."), name="static")

# --- SERVE HTML ---
@app.get("/")
async def read_root():
    return FileResponse("index.html")

# --- LANGCHAIN SETUP ---
llm = ChatGroq(
    temperature=0, 
    model_name="llama-3.1-8b-instant", 
    groq_api_key=GROQ_API_KEY
)

# --- PROMPT  ---
judge_template = """
You are the Story Engine for a children's interactive story about The Honest Woodcutter.
The current situation: The Goddess asked "Is this Golden Axe yours?" and we asked the child "What should Tim say?".

The child said: "{user_input}"

Task:
1. If the child implies "No", "It's not mine", "Tell the truth":
   - Output a VERY HAPPY, WARM response.
   - Say: "Wonderful! You are so honest! The Goddess smiled brightly. Because Tim told the truth, she gave him the Golden Axe AND his old iron axe as a reward! Honesty always wins!"
   - End with "The End."

2. If the child implies "Yes", "Take it", "Lie":
   - Output a GENTLE lesson.
   - Say: "Oh no... The Goddess knew that was a lie. Her face turned sad and she disappeared into the water. Tim went home with nothing. Remember, we must always tell the truth."
   - End with "The End."

3. If the input is unrelated/gibberish:
   - Say: "I didn't quite catch that. But remember, honesty is magic! Let's try the story again later."
   - End with "The End."

Constraints:
- Keep the response simple and child-friendly.
"""

prompt = ChatPromptTemplate.from_template(judge_template)
output_parser = StrOutputParser()
story_chain = prompt | llm | output_parser

# --- STORY AGENT ---
class StoryAgent:
    def __init__(self):
        self.step = 0
        
    def get_next_response(self, user_input=None):
        # STEP 1: Tell story and ask question
        if self.step == 0:
            # Added "What should Tim say?" at the end
            text = "Hi! I am Zippy. Once, a woodcutter named Tim lived in a village. He was very honest. One day he dropped his iron axe into the river... Splash! Suddenly, a River Goddess appeared! She held up a Shiny Golden Axe and asked... Is this Golden Axe yours? ... What should Tim say?"
            self.step += 1
            return text, False
            
        # STEP 2: Judge answer using LangChain
        elif self.step == 1:
            print(f"Invoking LangChain with input: {user_input}")
            response = story_chain.invoke({"user_input": user_input})
            self.step += 1
            return response, True
        else:
            return "The story is over. Refresh to play again!", True

agent = StoryAgent()

async def generate_audio(text: str, filename: str):
    # Using a slightly faster speaking rate (+10%) for energy
    communicate = edge_tts.Communicate(text, "en-US-AnaNeural", rate="+10%")
    await communicate.save(filename)
    return filename

# --- ENDPOINTS ---

@app.post("/start")
async def start_adventure():
    global agent
    agent = StoryAgent() 
    text, is_finished = agent.get_next_response()
    audio_file = f"response_{uuid.uuid4()}.mp3"
    await generate_audio(text, audio_file)
    return JSONResponse({
        "text": text, 
        "audio_url": f"/static/{audio_file}", 
        "is_finished": is_finished
    })


# ---- Main Pipeline ---

@app.post("/process_audio")
async def process_audio(file: UploadFile = File(...)):
    temp_filename = f"temp_{uuid.uuid4()}.webm"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        # --- DIRECT API CALL  ---
        url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&language=en-IN"
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "audio/*" # Accepts any audio format
        }
        
        with open(temp_filename, "rb") as audio:
            response = requests.post(url, headers=headers, data=audio)
        
        response_data = response.json()
        
        # Check if transcription worked
        if 'results' in response_data:
            user_transcript = response_data['results']['channels'][0]['alternatives'][0]['transcript']
        else:
            user_transcript = "..."
            
        print(f"User said: {user_transcript}")
        
        bot_text, is_finished = agent.get_next_response(user_input=user_transcript)
        audio_file = f"response_{uuid.uuid4()}.mp3"
        await generate_audio(bot_text, audio_file)

        return JSONResponse({
            "user_said": user_transcript,
            "text": bot_text,
            "audio_url": f"/static/{audio_file}",
            "is_finished": is_finished
        })
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)