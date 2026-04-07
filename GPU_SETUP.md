# FireSing GPU 服务器连接指南

在部署 Web 服务后，需要连接 AutoDL GPU 服务器。

## 步骤

1. **AutoDL 实例** 确保实例正在运行
2. **端口转发**: AutoDL 控制台 → 自定义服务 → 开启端口 → 获取公网访问地址
3. **启动 GPU 服务**: 在 AutoDL 实例上运行:
   ```bash
   cd gpu_server && python server.py --port 8001
   ```
4. **配置 .env**: 设置 GPU 服务器地址
   ```bash
   GPU_SERVER_URL=https://your-instance.autodl.pro
   ```
5. **重启后端**: `docker compose restart backend`

## 验证

```bash
# 在服务器上测试 GPU 连接
curl https://your-instance.autodl.pro/health
# 应该返回: {"status": "ok", "gpu": "NVIDIA RTX 4090D", ...}
```
