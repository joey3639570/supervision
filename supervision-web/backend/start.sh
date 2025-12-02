#!/bin/bash
# 启动脚本 - 设置正确的 Python 路径以支持 SAM3

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# SAM3 路径（根据实际位置调整）
SAM3_PATH="/root/joey/supervision/sam3"
if [ ! -d "$SAM3_PATH" ]; then
    # 尝试其他可能的位置
    SAM3_PATH="$PROJECT_ROOT/../sam3"
fi

# 检查并使用虚拟环境（如果存在）
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "Using virtual environment: $SCRIPT_DIR/venv"
    source "$SCRIPT_DIR/venv/bin/activate"
    PYTHON_CMD="$SCRIPT_DIR/venv/bin/python3"
    UVICORN_CMD="$SCRIPT_DIR/venv/bin/uvicorn"
else
    echo "No virtual environment found, using system Python"
    PYTHON_CMD="python3"
    UVICORN_CMD="uvicorn"
fi

# 设置 Python 路径，包含 SAM3 目录
export PYTHONPATH="$SAM3_PATH:$SCRIPT_DIR:$PYTHONPATH"

echo "Starting server with PYTHONPATH=$PYTHONPATH"
echo "SAM3 path: $SAM3_PATH"
echo "Python: $PYTHON_CMD"

# 启动 uvicorn
cd "$SCRIPT_DIR"
$UVICORN_CMD app.main:app --reload --port 8001
