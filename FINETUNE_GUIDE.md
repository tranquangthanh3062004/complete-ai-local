# Hướng Dẫn Fine-Tune Mô Hình Cho CompleteAI

Quá trình Fine-tune sẽ biến một mô hình tổng quát (như Llama-3-8B hoặc Qwen-2.5) thành một "chuyên gia" nói giọng văn của bạn và thấm nhuần kiến thức của riêng tổ chức bạn.

## Bước 1: Trích Xuất & Chuẩn Bị Dữ Liệu (Dataset Preparation)

Bạn đang lưu các câu hỏi và câu trả lời trong bảng `LearningEvent`. Hãy xuất các bản ghi có `feedback = 1` (được người dùng đánh giá là Tốt/Chính xác).

Định dạng dữ liệu chuẩn để fine-tune (Alpaca format hoặc ChatML). Bạn có thể viết một script Python nhỏ để xuất file `dataset.json` từ SQLite:

```json
[
  {
    "instruction": "Bạn là trợ lý pháp lý chuyên nghiệp. Hãy trả lời câu hỏi sau.",
    "input": "Luật giao thông quy định thế nào về nồng độ cồn?",
    "output": "Theo quy định hiện hành tại Nghị định 100/2019/NĐ-CP (sửa đổi tại Nghị định 123/2021/NĐ-CP), nồng độ cồn..."
  }
]
```

## Bước 2: Sử Dụng Unsloth Để Fine-Tune (Tối ưu tốc độ & RAM)

Thay vì cấu hình phức tạp, hãy sử dụng **[Unsloth](https://github.com/unslothai/unsloth)** trên Google Colab (miễn phí) hoặc máy chủ có GPU để Fine-tune. Unsloth giúp tốc độ fine-tune nhanh gấp 2 lần và tốn ít VRAM hơn.

1. Lên Google Colab, mở một notebook mới và chọn Runtime là GPU (T4).
2. Cài đặt thư viện: `pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"`
3. Viết mã Fine-tune (sử dụng LoRA):

```python
from unsloth import FastLanguageModel
import torch

# 1. Tải mô hình cơ sở (Ví dụ: Llama-3.2-8B hoặc Qwen2.5)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3-8b-Instruct-bnb-4bit",
    max_seq_length = 2048,
    dtype = None,
    load_in_4bit = True,
)

# 2. Cấu hình LoRA (Chỉ train một phần nhỏ trọng số để tiết kiệm RAM)
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
)

# 3. Load dataset.json của bạn vào HuggingFace Dataset format...
# 4. Sử dụng SFTTrainer của thư viện trl để bắt đầu training
```

## Bước 3: Xuất Ra Định Dạng GGUF (Cho Ollama)

Sau khi model đã học xong (mất khoảng 1-3 tiếng tùy lượng dữ liệu), bạn cần nén nó lại định dạng `.gguf` để chạy nhẹ nhàng trên Ollama ở máy cá nhân.

Với Unsloth, việc này chỉ cần 1 dòng code ở cuối Notebook:

```python
# Lưu mô hình ở dạng Q4_K_M (chuẩn nén 4-bit, cân bằng tốt nhất giữa tốc độ và độ thông minh)
model.save_pretrained_gguf("model_v1", tokenizer, quantization_method = "q4_k_m")
```

Bạn tải file `model_v1-unsloth.Q4_K_M.gguf` về máy tính.

## Bước 4: Tích Hợp Mô Hình Mới Vào Hệ Thống (Ollama)

Tại thư mục máy cá nhân, tạo một file tên là `Modelfile` với nội dung:

```text
# Trỏ tới file GGUF bạn vừa tải về
FROM ./model_v1-unsloth.Q4_K_M.gguf

# Định nghĩa system prompt cố định
SYSTEM """Bạn là CompleteAI - Trợ lý cục bộ được tối ưu hóa đặc biệt. 
Luôn trả lời bằng tiếng Việt, súc tích và sử dụng kiến thức chính xác."""

# Thiết lập siêu tham số (temperature thấp để không bị ảo giác)
PARAMETER temperature 0.1
PARAMETER num_ctx 4096
```

Mở Terminal và chạy lệnh để Ollama đóng gói mô hình:
```bash
ollama create complete-ai-model -f Modelfile
```

Cuối cùng, vào file `config.py` của dự án và đổi:
```python
ollama_model: str = "complete-ai-model"
```

Khởi động lại hệ thống, và dự án của bạn giờ đây đang chạy mô hình AI độc quyền do chính bạn đào tạo!
