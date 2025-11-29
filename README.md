# 🪓 Zippy Voice Agent Prototype: The Honest Woodcutter

### A Low-Latency Interactive Storytelling Engine for Kids

> **Note to Zippy Team:** This is a functional prototype built to demonstrate real-time voice interaction, state management, and ethical reasoning logic using Python.

## 📖 Overview

This project is a Proof of Concept (PoC) for an AI-powered audio player. It tells an interactive story where the narrative pauses to listen to the child's input. The AI acts as a **Moral Engine**, listening to the child's response (Truth vs. Lie) and dynamically altering the story's ending based on their choice.

**The Story:** "The Honest Woodcutter"
1.  **Narrator:** Tells the story of Tim dropping his axe.
2.  **Interaction:** The Goddess appears and asks, "Is this Golden Axe yours?"
3.  **Decision:** The AI listens.
    *   *Honest Answer:* "No." -> **Win State** (Reward).
    *   *Greedy Answer:* "Yes." -> **Lose State** (Lesson learned).

## 🏗️ Architecture

The system follows a high-performance **Request-Response** architecture designed for speed.

graph TD
    %% CLIENT SIDE
    User([User Speaks]) -->|Audio| Mic[Microphone]
    Mic -->|WebM Blob| Converter[JS Converter]
    Converter -->|WAV ArrayBuffer| WSSend(WebSocket Send)
    
    %% SERVER SIDE
    subgraph Server [FastAPI Backend]
        WSSend -->|Binary| API[Server Endpoint]
        API -->|Audio| STT[Deepgram STT]
        STT -->|Transcript| Brain[Groq LLM Logic]
        Brain -->|Response Text| TTS[Edge TTS]
        TTS -->|Audio Bytes| WSResp(WebSocket Response)
    end
    
    %% SYNC LOGIC
    WSResp -->|1. Text JSON| UI[Update UI Text]
    WSResp -->|2. Audio Binary| Player[Audio Context]
    WSResp -->|3. State JSON| Queue[("Pending Action Queue")]
    
    %% THE FIX
    Player -->|Play Audio| Spk([Speaker])
    Spk -.->|Event: onEnded| Sync[Sync Handler]
    
    Sync -->|Read Queue| Queue
    Queue -->|Instruction: Listen| Mic
    Queue -->|Instruction: Finish| Reset([Show Play Again])

    style Queue fill:#f9f,stroke:#333,stroke-width:2px,color:black
    style Sync fill:#ff9a9e,stroke:#333,stroke-width:2px,color:black
    

## 🛠️ Tech Stack
I chose these specific tools to optimize for latency (speed) and accent recognition (Indian context).

Backend Framework: FastAPI (Async Python) for handling concurrent audio requests.

ASR (The Ear): Deepgram Nova-2. Chosen for its sub-300ms latency and superior handling of Indian/Hinglish accents compared to Whisper.

LLM (The Brain): Llama-3 8B running on Groq LPUs. This provides near-instant inference (500+ tokens/sec), eliminating the "awkward pause" standard GPT models have.

Orchestration: LangChain. Used to strictly structure the "System Prompt" so the AI behaves as a Story Engine, not a chatbot.

TTS (The Voice): Edge-TTS. Provides high-quality neural voices with zero cost for the prototype.

Frontend: Vanilla JavaScript + CSS Animations (Visual feedback for Listening/Speaking states).

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/273d2daf-c312-4c86-a8dd-ce016505dc72" />

---
## 🚀 Installation & Setup

### Clone the repository
```1bash
git clone https://github.com/yourusername/zippy-prototype.git
cd zippy-prototype
```
## Create a Virtual Environment
```
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```
### Install Dependencies
```
pip install -r requirements.txt
```

### Set Environment Variables
 ```
    GROQ_API_KEY="YOUR_GROQ_KEY"
    DEEPGRAM_API_KEY=your_deepgram_key
 ```
### Run the Server
```
uvicorn server:app --reload
```
Open your browser and navigate to: http://127.0.0.1:8000

---
## 🔮 Future Improvements (Roadmap to Production)

While this prototype uses HTTP/REST for stability, a production version for Zippy would implement the following architecture upgrades:

### WebSockets for Full-Duplex Streaming

Current: Records full sentence -> Uploads -> Processes.

Upgrade: Switch to WebSockets. Audio chunks are streamed to the server while the child is speaking. This reduces latency to near-zero.

### "Barge-In" (Interruption Handling)

Feature: Children often interrupt stories.

Implementation: Using VAD (Voice Activity Detection) over WebSockets. If the child speaks while the AI is talking, the server immediately sends a "Stop Audio" signal to the frontend, making the interaction feel natural.

### Redis for State Management

Current: State is stored in Python memory (self.step).

Upgrade: Use Redis to store session states (session_id: step_number). This allows the server to scale horizontally (Kubernetes) and handle thousands of concurrent users without mixing up stories.

### AWS S3 for Audio Assets

Current: Audio is saved to local disk.

Upgrade: Stream audio bytes directly to the client (no disk write) or cache common story segments in an S3 Bucket behind a CDN (CloudFront) to reduce TTS costs and load times.

### Vector Database (Long-Term Memory)

Feature: Remembering the child's name and favorite characters.

Implementation: Use Pinecone or Qdrant.

Scenario: Child says "I like dragons."

Action: Store embedding.

Next Session: AI generates a story about "Tim the Dragon Hunter" automatically.

---
## For mp.3

Download shine-magic-sound-4-sounds-190258.mp3 from pixabay.com and place it in root folder 

You can download any intro music but make sure to change in file 


## ⚖️ License

@2025 Madhan Mohan. All Rights Reserved.
This project was built as a personal portfolio piece. 
You are welcome to view and evaluate the code, but commercial use or redistribution without permission is not allowed.

---
Built with ❤️ and Python.
