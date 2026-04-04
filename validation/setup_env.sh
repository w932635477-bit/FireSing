#!/bin/bash
# FireSing 技术验证环境安装脚本
# 运行环境: AutoDL RTX 4090D (Ubuntu + CUDA)
# 用法: bash validation/setup_env.sh

set -euo pipefail

echo "=== FireSing Validation Environment Setup ==="
echo "GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo 'Not detected')"
echo "Python: $(python3 --version)"
echo "CUDA: $(nvcc --version 2>/dev/null | grep release || echo 'N/A')"
echo ""

# 1. 创建工作目录
echo "[1/6] Creating directories..."
mkdir -p test-data/models
mkdir -p test-data/output
mkdir -p validation/results

# 2. 安装 Python 依赖
echo "[2/6] Installing Python packages..."
pip install --upgrade pip

# 核心依赖
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# 人声分离
pip install audio-separator

# Whisper (openai-whisper 或 faster-whisper)
pip install openai-whisper

# 也可以用 faster-whisper (更快, 推荐)
pip install faster-whisper

# 音频处理
pip install pydub librosa soundfile noisereduce

# Silero VAD
pip install torch torchvision torchaudio

# 视频相关
pip install ass

# 工具
pip install tqdm rich

# 3. 下载 UVR5 模型
echo "[3/6] Downloading UVR5 model (MDX-Net)..."
python3 -c "
from audio_separator import Separator
sep = Separator()
# 首次运行会自动下载模型
print('UVR5 model will be downloaded on first use')
"

# 4. 下载 Whisper 模型
echo "[4/6] Downloading Whisper large-v3 model..."
python3 -c "
import whisper
print('Downloading whisper large-v3...')
model = whisper.load_model('large-v3')
print('Whisper model ready')
" || echo "Whisper download failed, will download on first use"

# 5. 检查 RVC
echo "[5/6] Setting up RVC..."
if [ ! -d "RVC" ]; then
    echo "Cloning RVC repository..."
    git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git RVC
    cd RVC
    pip install -r requirements.txt
    cd ..
fi

# 6. 验证安装
echo "[6/6] Verifying installation..."
python3 << 'PYEOF'
import sys
results = {}

checks = [
    ("torch", lambda: __import__("torch").__version__),
    ("torch.cuda", lambda: str(__import__("torch").cuda.is_available())),
    ("torchaudio", lambda: __import__("torchaudio").__version__),
    ("whisper", lambda: __import__("whisper").__version__),
    ("pydub", lambda: __import__("pydub").__version__),
    ("librosa", lambda: __import__("librosa").__version__),
    ("soundfile", lambda: __import__("soundfile").__version__),
]

print("\n--- Installation Check ---")
for name, check_fn in checks:
    try:
        version = check_fn()
        print(f"  [OK] {name}: {version}")
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")

# GPU check
import torch
if torch.cuda.is_available():
    print(f"\n  [GPU] {torch.cuda.get_device_name(0)}")
    print(f"  [VRAM] {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB")
else:
    print("\n  [WARNING] No CUDA GPU detected!")

print("\n--- Setup Complete ---")
PYEOF

echo ""
echo "=== Setup Complete ==="
echo "Next: Place test audio in test-data/ and run validation scripts"
echo "  test-data/song.mp3   — 测试歌曲"
echo "  test-data/lyrics.lrc — 歌词文件 (LRC 格式)"
echo "  test-data/models/    — RVC 音色模型 (.pth + .index)"
