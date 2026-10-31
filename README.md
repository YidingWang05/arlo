# Arlo — Multimodal Everyday Living Assistant for Older Adults
> **Track 2 — Multimodal & Human-Centric AI**

统一 Gemini 2.0 基层模型 + 4 个专项工具模块，接口通过 Pydantic 强类型严格对齐。

## 👥 团队分工
- **Xiyu Chen**: AI 基层大脑与 M1 视觉解读 (`app/core/base_model.py`, `app/modules/m1_vision_tool.py`)
- **Yiding Wang**: M2 记忆代购与后端网关 (`app/modules/m2_memory_tool.py`, `app/api/routes.py`)
- **Kaiyu Feng**: M4 适老化大字相框前端 (前端客户端 / Web 页面)
- **Weihang You**: M3 实时伴聊与路演 Presentation (`app/modules/m3_live_tool.py`, Demo & Pitch PPT)
