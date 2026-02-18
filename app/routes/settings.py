"""设置路由 - 配置管理和连接测试"""

from fastapi import APIRouter
from app.models import AllSettings, TestResult
from app.config import load_config, save_config
from app.aria2_client import Aria2Client
from app.teldrive_client import TelDriveClient
from app.task_manager import task_manager

router = APIRouter(prefix="/api/settings")


@router.get("")
async def get_settings():
    """获取当前设置"""
    config = load_config()
    return config


@router.put("")
async def update_settings(settings: AllSettings):
    """保存设置"""
    config = settings.model_dump()
    save_config(config)
    # 重新加载配置到任务管理器
    task_manager.reload_config()
    return {"success": True, "message": "设置已保存"}


@router.post("/test/aria2")
async def test_aria2():
    """测试 aria2 连接"""
    config = load_config()
    client = Aria2Client(
        rpc_url=config["aria2"]["rpc_url"],
        rpc_port=config["aria2"]["rpc_port"],
        rpc_secret=config["aria2"]["rpc_secret"]
    )
    result = await client.test_connection()
    return result


@router.post("/test/teldrive")
async def test_teldrive():
    """测试 TelDrive 连接"""
    config = load_config()
    client = TelDriveClient(
        api_host=config["teldrive"]["api_host"],
        access_token=config["teldrive"]["access_token"]
    )
    result = await client.test_connection()
    return result


@router.post("/test/path")
async def test_path_consistency():
    """测试下载目录与上传目录是否一致
    
    流程：通过 aria2 下载 1MB 测试文件到 download_dir，
    然后检查 upload_dir 中是否出现该文件，最后清理。
    """
    import asyncio
    import uuid

    config = load_config()
    download_dir = config["aria2"].get("download_dir", "./downloads")
    upload_dir = config["teldrive"].get("upload_dir", "")

    if not upload_dir:
        upload_dir = download_dir

    # 使用唯一文件名防止冲突
    test_filename = f"_path_test_{uuid.uuid4().hex[:8]}.tmp"
    test_url = "https://speed.hetzner.de/1MB.bin"

    aria2 = Aria2Client(
        rpc_url=config["aria2"]["rpc_url"],
        rpc_port=config["aria2"]["rpc_port"],
        rpc_secret=config["aria2"]["rpc_secret"]
    )

    gid = None
    try:
        # 1. 用 aria2 下载测试文件
        gid = await aria2.add_uri(test_url, {
            "dir": download_dir,
            "out": test_filename
        })

        # 2. 等待下载完成 (最多 30 秒)
        import os
        for _ in range(60):
            await asyncio.sleep(0.5)
            status = await aria2.tell_status(gid)
            s = status.get("status", "")
            if s == "complete":
                break
            if s in ("error", "removed"):
                error_msg = status.get("errorMessage", "下载失败")
                return {"success": False, "message": f"aria2 下载测试文件失败: {error_msg}"}
        else:
            # 超时
            try:
                await aria2.remove(gid)
            except Exception:
                pass
            return {"success": False, "message": "下载测试文件超时 (30秒)"}

        # 3. 检查 upload_dir 中是否存在该文件
        upload_path = os.path.join(upload_dir, test_filename)
        download_path = os.path.join(download_dir, test_filename)

        if os.path.exists(upload_path):
            # 清理
            try:
                os.remove(upload_path)
            except Exception:
                pass
            # 如果 upload_path != download_path，也尝试清理 download_path
            if os.path.normpath(upload_path) != os.path.normpath(download_path):
                try:
                    os.remove(download_path)
                except Exception:
                    pass
            return {
                "success": True,
                "message": f"✅ 路径一致！aria2 下载目录与上传文件目录指向同一位置"
            }
        else:
            # 清理 download_path
            try:
                os.remove(download_path)
            except Exception:
                pass
            return {
                "success": False,
                "message": f"❌ 路径不一致！文件已下载到 {download_dir}，但在 {upload_dir} 中找不到"
            }

    except Exception as e:
        return {"success": False, "message": f"测试失败: {str(e)}"}
    finally:
        # 从 aria2 中移除任务记录
        if gid:
            try:
                await aria2.remove(gid)
            except Exception:
                pass

