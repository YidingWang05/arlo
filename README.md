# Arlo — Multimodal Everyday Living Assistant for Older Adults
> **Google DeepMind / Gemini Hackathon**  
> **Powered by Gemini 4 Argon**

Arlo is a human-centric, multimodal AI assistant designed for older adults. Deployed in a digital photo frame form factor, Arlo bridges the digital divide through camera vision, expressive speech, and family context memory.

---

## 🏛️ System Architecture

The project features a **Single Gemini 4 Argon Foundation Engine** driving **4 Decoupled Tool Modules**:

1. **Module 1: Vision Explainer (`/api/arlo/vision/explain`)**
   - Extracts dosage instructions from medicine boxes and complex bills into large-print text and plain-language speech.
2. **Module 2: Memory Buy (`/api/arlo/memory/buy`)**
   - Resolves vague spoken queries (e.g., *"the blue bottle my daughter bought"*) into a binary (A/B) visual comparison card.
3. **Module 3: Live Companion (`/api/arlo/live/ws`)**
   - Full-duplex WebSocket stream enabling conversational photo storytelling with natural voice barge-in interruption.
4. **Module 4: Family Hub (`/api/arlo/frame/*`)**
   - Bi-directional sync allowing adult children to remotely push photos and maintain household knowledge.

All module interfaces are strictly enforced with **Pydantic Schemas** (`app/schemas/`), ensuring zero contract drift between frontend and backend.

---

## 👥 Team Responsibilities

| Contributor | Role & Assigned Module | Core Paths |
| :--- | :--- | :--- |
| **Xiyu Chen** | **AI Engine & M1 Vision Explainer** | `app/core/base_model.py`<br>`app/modules/m1_vision_tool.py` |
| **Yiding Wang** | **M2 Memory Buy & API Gateway** | `app/modules/m2_memory_tool.py`<br>`app/api/routes.py` |
| **Kaiyu Feng** | **M4 Accessibility Frame Frontend** | Frontend client / Web view (48px+ large fonts) |
| **Weihang You** | **M3 Live Companion & Pitch Lead** | `app/modules/m3_live_tool.py`<br>Demo & Presentation |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- Google Cloud / Gemini API Key with **Gemini 4 Argon** access.

### 2. Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
