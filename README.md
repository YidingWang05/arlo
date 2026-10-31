# Arlo — Multimodal Everyday Living Assistant for Older Adults
> **Google DeepMind / Gemini Hackathon**  
> **Track 2 — Multimodal & Human-Centric AI**  
> **Core Foundation Engine: Powered by Gemini 4 Argon (`gemini-4-argon`)**

---

## 📖 Executive Summary & Mission

As digital services grow increasingly complex, older adults frequently encounter high friction barriers: unreadable miniature fonts (5–6pt), convoluted medical and bureaucratic jargon, complex smartphone navigation, and digital isolation.

**Arlo** transforms everyday assistance into an ambient, zero-learning-curve **Smart Photo Frame** form factor. Built specifically for independent seniors, Arlo replaces tedious smartphone operations with natural **Camera Vision**, **Expressive Conversational Speech**, and **Family Household Memory**.

Instead of asking an older adult to navigate apps or type search queries, Arlo operates on three human-centric principles:
1. **Camera as the Eye**: Point a medicine box or utility bill to the frame, and Arlo explains it in plain language with large fonts.
2. **Memory as the Brain**: Say *"buy the blue bottle my daughter bought"*, and Arlo pulls candidate images for single-decision confirmation.
3. **Voice as the Companion**: Browse vintage family photos while conversing with Gemini 4 Argon in full-duplex live audio with natural barge-in interruption.

---

## 🏛️ System Architecture

Arlo adopts a decoupled **"One Foundation Model + Four Specialized Tool Modules"** architecture. All inter-module communication is strictly enforced via **Pydantic v2 schemas** in `app/schemas/` to guarantee zero contract drift.

```text
                               ┌────────────────────────────────────────────────────────┐
                               │           Gemini 4 Argon Foundation Engine             │
                               │          (1M Context, Native Thinking Control)         │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
                    ┌──────────────────┬──────────────────┴──────────────────┬──────────────────┐
                    ▼                  ▼                                     ▼                  ▼
             [Module 1: Vision] [Module 2: Memory Buy]                [Module 3: Live Voice] [Module 4: Frame Hub]
             POST /vision/explain POST /memory/buy                    WS /live/ws            GET/POST /frame/*
                    │                  │                                     │                  │
                    ▼                  ▼                                     ▼                  ▼
             Medicine & Bills   Fuzzy Speech -> Two High-Res          Full-Duplex Companion  Ambient Photo Album
             Plain English +    A/B Candidate Comparison Cards        Photo Storytelling &   & Family Remote Push
             Large-Print (48px) for Single-Decision Confirmation     Barge-in Interruption  State Synchronization
