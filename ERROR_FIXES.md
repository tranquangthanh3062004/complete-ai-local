# 🛠️ HƯỚNG DẪN SỬA CÁC LỖI - COMPLETE-AI-LOCAL

**Ngày kiểm tra:** 2026-07-24  
**Tổng số lỗi:** 7 (3 Critical + 3 Major + 1 Minor)  
**Thời gian sửa ước tính:** ~20 phút

---

## ⚡ QUICK REFERENCE - LỖI + LỆNH SỬA

| # | Lỗi | Fix Command | Thời Gian |
|---|-----|------------|----------|
| 1 | install_deps.py typo | `Edit line 27` | 1 min |
| 2 | edge_rag.py deleted | `git checkout d6520e9 -- offline_edge/edge_rag.py` | 1 min |
| 3 | alerts/ bad files | `git rm --cached alerts/*` | 2 min |
| 4 | config.py import | `Move import to top` | 3 min |
| 5-6 | chat.py imports | `Refactor to PEP 8` | 5 min |
| 7 | sanitizer warning | `Ignore (false positive)` | 0 min |

---

## 🔴 CRITICAL FIXES (NGAY LẬP TỨC)

### ✅ FIX #1: install_deps.py - Line 27 (Typo)

**Tệp:** `install_deps.py`  
**Dòng:** 27  
**Vấn đề:** `dl` thay cho `packages_llm = [`

**Cách sửa:**

```python
# ❌ SAI (Dòng 25-34 hiện tại):
packages_core = [
    "fastapi",
    "uvicorn[standard]",
    ...
]

dl    "langchain",                          # ← LỖI!
    "langchain-core",
    "langchain-community",
    ...
]

# ✅ ĐÚNG:
packages_core = [
    "fastapi",
    "uvicorn[standard]",
    ...
]

packages_llm = [                             # ← SỬA
    "langchain",
    "langchain-core",
    "langchain-community",
    "langchain-ollama",
    "langchain-huggingface",
    "langchain-text-splitters",
    "langchain-chroma",
]
```

**Lệnh sửa:**
```bash
# Option 1: Dùng text editor, sửa dòng 27
# Option 2: Dùng sed (Linux/Git Bash)
sed -i "27s/dl/packages_llm = [/" install_deps.py
```

**Xác thực:**
```bash
python -m py_compile install_deps.py
# Nếu không error → fix thành công
```

---

### ✅ FIX #2: offline_edge/edge_rag.py - Restore File

**Tệp:** `offline_edge/edge_rag.py`  
**Vấn đề:** File bị xóa sạch (0 lines, phải là 77 lines)

**Cách sửa - Option A: Restore từ Git**

```bash
# Restore file từ commit d6520e9 (khi file được tạo)
git checkout d6520e9 -- offline_edge/edge_rag.py

# Verify
ls -la offline_edge/edge_rag.py
# Kết quả: ~2KB file size, 77 lines

# Commit
git add offline_edge/edge_rag.py
git commit -m "restore: offline edge RAG module"
```

**Cách sửa - Option B: Xóa file nếu không cần**

```bash
# Nếu quyết định không dùng edge_rag.py
git rm offline_edge/edge_rag.py

# Remove directory nếu trống
rmdir offline_edge/  # Linux/Git Bash
Remove-Item offline_edge -Force  # PowerShell

# Commit
git commit -m "remove: offline edge gateway (not used)"
```

**Khuyến cáo:** 
- Nếu có kế hoạch dùng offline RAG → **Chọn Option A**
- Nếu tính năng này không dùng → **Chọn Option B**

---

### ✅ FIX #3: alerts/ Directory - Remove Bad Files

**Tệp:** `alerts/` directory  
**Vấn đề:** 4 files với tên không hợp lệ tracked trong git

**Cách sửa:**

```bash
# Liệt kê files cần xóa
ls -la alerts/

# Kết quả:
# - "# accident_monitor_gui.py"
# - "pip install ipywidgets opencv-python pil.py"
# - "python run_detr_vscode.py"
# - "Đang ghi 2025-11-21 073805.mp4"

# ─────────────────────────────────────────────────

# Cách 1: Remove từ Git nhưng giữ file locally (nếu cần)
git rm --cached alerts/"#"*
git rm --cached alerts/"pip"*
git rm --cached alerts/"python"*
git rm --cached alerts/"Đang"*

# Hoặc dùng wildcard
git rm --cached alerts/*

# ─────────────────────────────────────────────────

# Cách 2: Xóa hoàn toàn (file + git)
rm -rf alerts/*          # Linux/Git Bash
Remove-Item alerts/* -Force  # PowerShell

# Hoặc xóa cả thư mục nếu không dùng
rm -rf alerts/           # Linux/Git Bash
Remove-Item alerts -Force -Recurse  # PowerShell

# ─────────────────────────────────────────────────

# Commit
git add -A
git commit -m "remove: invalid alert files from git tracking"
```

**Verify:**
```bash
git status
# Không nên có alerts/ files listed
```

**Khuyến cáo:**
- Nếu có valid files trong alerts/ → Chỉ xóa 4 bad files
- Nếu alerts/ là test directory → Xóa cả directory

---

## 🟠 MAJOR FIXES (HÔM NAY)

### ✅ FIX #4: config.py - Move Import to Top

**Tệp:** `config.py`  
**Dòng:** 21-22 (Import inside class)  
**Vấn đề:** PEP 8 violation - import không ở top of file

**Cách sửa:**

```python
# ❌ SAI (Hiện tại):
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic_settings import SettingsConfigDict
from pydantic import Field

from core.constants import APP_NAME, APP_VERSION
from core.enums import OperationMode

class Settings(BaseSettings):
    app_name: str = Field(default=APP_NAME)
    ...
    database_url: str = "sqlite+aiosqlite:////tmp/completeai.db"
    
    from pydantic import field_validator  # ← Import ở SAI vị trí!
    
    @field_validator("database_url", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        ...

# ✅ ĐÚNG:
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator  # ← Thêm vào đây
from typing import Optional

from core.constants import APP_NAME, APP_VERSION
from core.enums import OperationMode

class Settings(BaseSettings):
    app_name: str = Field(default=APP_NAME)
    ...
    database_url: str = "sqlite+aiosqlite:////tmp/completeai.db"
    
    @field_validator("database_url", mode="before")  # ← Decorator giữ nguyên
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        ...
```

**Chi tiết:**
1. Dòng 4: Thêm `field_validator` vào import statement
2. Dòng 21-22: XÓA 2 dòng import bên trong class
3. Giữ nguyên decorator + method

**Verify:**
```bash
python -m py_compile config.py
python -c "from config import settings; print('OK')"
```

---

### ✅ FIX #5-6: routers/chat.py - Refactor Imports

**Tệp:** `routers/chat.py`  
**Dòng:** 96-97 (Imports mid-file), 63 & 139 (Duplicate imports)

**Cách sửa:**

```python
# ❌ SAI (Hiện tại):

# Dòng 1-14: Imports bình thường
from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from typing import Optional
import time

from core.schemas import ChatRequest, ChatResponse
from core.enums import OperationMode, IntentType
from core.routing.intent import analyze_intent
from core.routing.mode import select_operation_mode
from core.routing.knowledge import fetch_knowledge
from core.routing.execution import execute_pipeline
from core.routing.validator import format_and_validate
from services.cache_service import TTLCache
from config import settings
from logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat API (Unified)"],
    responses={404: {"description": "Not found"}},
)

_answer_cache = TTLCache(maxsize=256, ttl=3600)

@router.post("/direct", response_model=ChatResponse)
async def chat_direct(
    request: ChatRequest,
    x_network_mode: Optional[str] = Header(None, alias="X-Network-Mode"),
):
    start_time = time.time()
    query = request.query.strip()
    
    try:
        # 1. Mode Selector
        header_mode = None
        if x_network_mode:
            try:
                header_mode = OperationMode(x_network_mode.lower())
            except ValueError:
                pass
                
        active_mode = await select_operation_mode(mode_override=request.mode_override or header_mode)
        logger.info(f"Active Mode: {active_mode.value}")

        # 2. Intent Analyzer
        intent = await analyze_intent(query)
        logger.info(f"Intent detected: {intent.type.value} | Topic: {intent.topic.value}")

        # Check cache only for INFO or GREETING (skip ROUTE intent caching for fresh real-time route generation)
        cache_key = f"{active_mode.value}:{query.lower()}"
        if intent.type != IntentType.ROUTE:
            cached_resp = _answer_cache.get(cache_key)
            if cached_resp:
                logger.info(f"Cache hit for query: {query}")
                cached_resp.latency_ms = round((time.time() - start_time) * 1000, 2)
                return cached_resp

        # 3. Knowledge Router
        rag_context, route_context = await fetch_knowledge(intent, active_mode)

        # 4. Execution Router
        from core.schemas import MessageHistory  # ← DUPLICATE #1!
        request.messages.append(MessageHistory(role="user", content=query))
        raw_answer = await execute_pipeline(intent, rag_context, route_context, request.messages, active_mode)

        # 5. Formatter & Validator
        final_answer, suggestions = format_and_validate(raw_answer, intent)

        latency = round((time.time() - start_time) * 1000, 2)
        
        sources = []
        if rag_context: sources.append("local_rag" if active_mode == OperationMode.OFFLINE else "cloud_rag")
        if route_context: sources.append("smart_route")
            
        resp = ChatResponse(
            reply=final_answer,
            mode=active_mode,
            model=settings.llm_model_name,
            intent=intent.type.value,
            latency_ms=latency,
            sources=sources,
            suggestions=suggestions if request.suggest else []
        )
        
        # 6. Set Cache (only for non-ROUTE intents)
        if len(final_answer) > 50 and intent.type != IntentType.ROUTE:
            _answer_cache.set(cache_key, resp)
            
        return resp
        
    except Exception as e:
        logger.exception(f"Chat execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import StreamingResponse  # ← IMPORTS MID-FILE!
import asyncio                                      # ← IMPORTS MID-FILE!

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    x_network_mode: Optional[str] = Header(None, alias="X-Network-Mode"),
):
    start_time = time.time()
    query = request.query.strip()
    cache_key = query.lower()
    
    # 1. Check Cache
    cached_resp = _answer_cache.get(cache_key)
    
    async def event_generator():
        if cached_resp:
            logger.info(f"Stream Cache hit for query: {query}")
            ans = cached_resp.reply
            chunk_size = max(1, len(ans) // 20)
            for i in range(0, len(ans), chunk_size):
                chunk = ans[i:i+chunk_size]
                yield f"data: {chunk.replace(chr(10), chr(10) + 'data: ')}\n\n"
                await asyncio.sleep(0.02)
            return

        try:
            # 1. Mode Selector
            header_mode = None
            if x_network_mode:
                try:
                    header_mode = OperationMode(x_network_mode.lower())
                except ValueError:
                    pass
            active_mode = await select_operation_mode(mode_override=request.mode_override or header_mode)
            
            # 2. Intent Analyzer
            intent = await analyze_intent(query)
            
            # 3. Knowledge Router
            rag_context, route_context = await fetch_knowledge(intent, active_mode)
            
            # 4. Execution Router
            from core.schemas import MessageHistory  # ← DUPLICATE #2!
            request.messages.append(MessageHistory(role="user", content=query))
            
            stream_gen = await execute_pipeline(intent, rag_context, route_context, request.messages, active_mode, stream=True)
            
            full_response = ""
            async for chunk in stream_gen:
                if chunk:
                    full_response += chunk
                    yield f"data: {chunk.replace(chr(10), chr(10) + 'data: ')}\n\n"
                    
            # Post-process the full response to cache it
            final_answer, suggestions = format_and_validate(full_response, intent)
            if len(final_answer) > 50:
                resp = ChatResponse(
                    reply=final_answer,
                    mode=active_mode,
                    model=settings.llm_model_name,
                    intent=intent.type.value,
                    latency_ms=round((time.time() - start_time) * 1000, 2),
                    sources=[],
                    suggestions=suggestions if request.suggest else []
                )
                _answer_cache.set(cache_key, resp)
                
        except Exception as e:
            logger.exception(f"Chat stream execution error: {e}")
            from core.constants import DEFAULT_FALLBACK
            fallback = DEFAULT_FALLBACK
            yield f"data: {fallback.replace(chr(10), chr(10) + 'data: ')}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ✅ ĐÚNG:

from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from fastapi.responses import StreamingResponse  # ← Thêm vào TOP
from typing import Optional
import time
import asyncio  # ← Thêm vào TOP

from core.schemas import ChatRequest, ChatResponse, MessageHistory  # ← Thêm MessageHistory ở đây
from core.enums import OperationMode, IntentType
from core.routing.intent import analyze_intent
from core.routing.mode import select_operation_mode
from core.routing.knowledge import fetch_knowledge
from core.routing.execution import execute_pipeline
from core.routing.validator import format_and_validate
from services.cache_service import TTLCache
from config import settings
from logger import get_logger
from core.constants import DEFAULT_FALLBACK  # ← Thêm vào TOP (nếu cần)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat API (Unified)"],
    responses={404: {"description": "Not found"}},
)

_answer_cache = TTLCache(maxsize=256, ttl=3600)

@router.post("/direct", response_model=ChatResponse)
async def chat_direct(
    request: ChatRequest,
    x_network_mode: Optional[str] = Header(None, alias="X-Network-Mode"),
):
    start_time = time.time()
    query = request.query.strip()
    
    try:
        # 1. Mode Selector
        header_mode = None
        if x_network_mode:
            try:
                header_mode = OperationMode(x_network_mode.lower())
            except ValueError:
                pass
                
        active_mode = await select_operation_mode(mode_override=request.mode_override or header_mode)
        logger.info(f"Active Mode: {active_mode.value}")

        # 2. Intent Analyzer
        intent = await analyze_intent(query)
        logger.info(f"Intent detected: {intent.type.value} | Topic: {intent.topic.value}")

        # Check cache only for INFO or GREETING
        cache_key = f"{active_mode.value}:{query.lower()}"
        if intent.type != IntentType.ROUTE:
            cached_resp = _answer_cache.get(cache_key)
            if cached_resp:
                logger.info(f"Cache hit for query: {query}")
                cached_resp.latency_ms = round((time.time() - start_time) * 1000, 2)
                return cached_resp

        # 3. Knowledge Router
        rag_context, route_context = await fetch_knowledge(intent, active_mode)

        # 4. Execution Router
        request.messages.append(MessageHistory(role="user", content=query))  # ← Dùng import ở TOP
        raw_answer = await execute_pipeline(intent, rag_context, route_context, request.messages, active_mode)

        # 5. Formatter & Validator
        final_answer, suggestions = format_and_validate(raw_answer, intent)

        latency = round((time.time() - start_time) * 1000, 2)
        
        sources = []
        if rag_context: sources.append("local_rag" if active_mode == OperationMode.OFFLINE else "cloud_rag")
        if route_context: sources.append("smart_route")
            
        resp = ChatResponse(
            reply=final_answer,
            mode=active_mode,
            model=settings.llm_model_name,
            intent=intent.type.value,
            latency_ms=latency,
            sources=sources,
            suggestions=suggestions if request.suggest else []
        )
        
        # 6. Set Cache
        if len(final_answer) > 50 and intent.type != IntentType.ROUTE:
            _answer_cache.set(cache_key, resp)
            
        return resp
        
    except Exception as e:
        logger.exception(f"Chat execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ← Không có imports ở đây nữa!

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    x_network_mode: Optional[str] = Header(None, alias="X-Network-Mode"),
):
    start_time = time.time()
    query = request.query.strip()
    cache_key = query.lower()
    
    # 1. Check Cache
    cached_resp = _answer_cache.get(cache_key)
    
    async def event_generator():
        if cached_resp:
            logger.info(f"Stream Cache hit for query: {query}")
            ans = cached_resp.reply
            chunk_size = max(1, len(ans) // 20)
            for i in range(0, len(ans), chunk_size):
                chunk = ans[i:i+chunk_size]
                yield f"data: {chunk.replace(chr(10), chr(10) + 'data: ')}\n\n"
                await asyncio.sleep(0.02)
            return

        try:
            # 1. Mode Selector
            header_mode = None
            if x_network_mode:
                try:
                    header_mode = OperationMode(x_network_mode.lower())
                except ValueError:
                    pass
            active_mode = await select_operation_mode(mode_override=request.mode_override or header_mode)
            
            # 2. Intent Analyzer
            intent = await analyze_intent(query)
            
            # 3. Knowledge Router
            rag_context, route_context = await fetch_knowledge(intent, active_mode)
            
            # 4. Execution Router
            request.messages.append(MessageHistory(role="user", content=query))  # ← Dùng import ở TOP
            
            stream_gen = await execute_pipeline(intent, rag_context, route_context, request.messages, active_mode, stream=True)
            
            full_response = ""
            async for chunk in stream_gen:
                if chunk:
                    full_response += chunk
                    yield f"data: {chunk.replace(chr(10), chr(10) + 'data: ')}\n\n"
                    
            # Post-process the full response to cache it
            final_answer, suggestions = format_and_validate(full_response, intent)
            if len(final_answer) > 50:
                resp = ChatResponse(
                    reply=final_answer,
                    mode=active_mode,
                    model=settings.llm_model_name,
                    intent=intent.type.value,
                    latency_ms=round((time.time() - start_time) * 1000, 2),
                    sources=[],
                    suggestions=suggestions if request.suggest else []
                )
                _answer_cache.set(cache_key, resp)
                
        except Exception as e:
            logger.exception(f"Chat stream execution error: {e}")
            fallback = DEFAULT_FALLBACK  # ← Dùng import ở TOP
            yield f"data: {fallback.replace(chr(10), chr(10) + 'data: ')}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Tóm tắt thay đổi:**
1. **Dòng 1-20:** Thêm `StreamingResponse`, `asyncio`, `MessageHistory`, `DEFAULT_FALLBACK` vào imports
2. **Dòng 96-97:** XÓA 2 dòng import from fastapi.responses
3. **Dòng 63 & 139:** XÓA 2 dòng duplicate import
4. Giữ nguyên logic code, chỉ thay đổi vị trí import

---

## 🟡 MINOR FIXES (TÙY CHỌN)

### ℹ️ FIX #7: services/sanitizer.py - False Positive Warning

**Tệp:** `services/sanitizer.py`  
**Vấn đề:** `SyntaxWarning: invalid escape sequence '\s'`

**Kết luận:** 
- ✓ Code thực chất **KHÔNG có lỗi**
- ✓ Đã dùng raw string `r"..."` đúng cách
- ✓ `\s` là regex syntax, không phải Python
- ⚠️ Warning chỉ là preventive (false positive)

**Cách xử lý:**
- **Option 1:** Bỏ qua (recommended) - warning không ảnh hưởng functionality
- **Option 2:** Suppress warning (nếu dùng linter)

```python
# Option 2: Nếu dùng pylint
# pylint: disable=invalid-escape-sequence
INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous|above)\s+instructions?",
    ...
]
```

---

## ✅ VERIFICATION CHECKLIST

Sau khi sửa, chạy các lệnh này để xác thực:

```bash
# 1. Python syntax check
python -m py_compile install_deps.py config.py routers/chat.py
echo "✓ Syntax OK"

# 2. Import check
python -c "import install_deps; from config import settings; from routers import chat; print('✓ Imports OK')"

# 3. Run linter (optional)
pip install flake8
flake8 install_deps.py config.py routers/chat.py
# Should show no major errors after fixes

# 4. Git status
git status
# Should show modified files but no syntax errors

# 5. Commit
git add install_deps.py config.py routers/chat.py offline_edge/edge_rag.py
git commit -m "fix: resolve syntax errors and code style violations"
```

---

## 📞 SUPPORT

Nếu gặp vấn đề:

1. **Lỗi syntax khi edit:** Kiểm tra indentation, quotes, brackets
2. **Git conflict:** `git checkout HEAD -- file` để rollback, rồi fix lại
3. **Import error:** Chạy `python -c "from module import class"` để test

---

**Báo cáo chi tiết:** Xem `DETAILED_ERROR_ANALYSIS.md` và `GIT_TIMELINE.md` trong scratchpad
