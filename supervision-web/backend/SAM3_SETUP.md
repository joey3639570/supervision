# SAM3 设置指南

## 检查点配置

SAM3 需要模型检查点文件才能工作。系统会自动查找以下位置（按优先级）：

1. `/root/joey/sam3_model/sam3.pt` （默认位置）
2. `/root/joey/sam3_model/model.safetensors` （备选格式）
3. `backend/checkpoints/sam3_hiera_base.pt` （本地备份）
4. `backend/checkpoints/sam3.pt` （本地备份）

### 自定义检查点路径

如果需要使用不同的检查点文件，可以通过环境变量设置：

```bash
export SAM3_CHECKPOINT_PATH=/path/to/your/checkpoint.pt
./start.sh
```

或者在启动时直接设置：

```bash
SAM3_CHECKPOINT_PATH=/path/to/your/checkpoint.pt ./start.sh
```

## 问题排查

如果遇到 "No module named 'einops'" 或其他 SAM3 导入错误，请按以下步骤操作：

### 1. 停止当前运行的服务器

```bash
# 查找并停止正在运行的 uvicorn 进程
pkill -f "uvicorn app.main:app"
# 或
ps aux | grep uvicorn
kill <PID>
```

### 2. 确保所有依赖已安装

```bash
cd /root/joey/supervision/supervision-web/backend
pip install -r requirements.txt
```

### 3. 使用启动脚本启动服务器（推荐）

```bash
cd /root/joey/supervision/supervision-web/backend
./start.sh
```

启动脚本会自动：
- 设置正确的 PYTHONPATH
- 包含 SAM3 目录路径
- 显示调试信息

### 4. 手动启动（如果脚本不工作）

```bash
cd /root/joey/supervision/supervision-web/backend
export PYTHONPATH="/root/joey/supervision/sam3:$PWD:$PYTHONPATH"
uvicorn app.main:app --reload --port 8001
```

### 5. 验证 SAM3 是否可用

启动服务器后，检查日志中是否显示：
- ✅ "SAM3 available: True" （成功）
- ❌ "Warning: SAM3 not available" （失败）

如果失败，检查：
1. `/root/joey/supervision/sam3` 目录是否存在
2. 所有依赖是否已安装（见 requirements.txt）
3. PYTHONPATH 是否正确设置

## 常见问题

### Q: 为什么需要启动脚本？
A: SAM3 是一个本地安装的包，不在标准 Python 包路径中。启动脚本确保 Python 能找到 SAM3 模块。

### Q: 可以在不同的端口运行吗？
A: 可以，修改 `start.sh` 中的 `--port 8001` 参数即可。

### Q: 如何检查 SAM3 是否正常工作？
A: 访问 API 端点 `/api/v1/segment`，如果返回 503 错误说明 SAM3 不可用，如果返回正常响应说明 SAM3 工作正常。
