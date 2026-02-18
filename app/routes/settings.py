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
    
    在 download_dir 中创建测试文件，然后检查 upload_dir 中是否可见。
    """
    import os
    import uuid

    config = load_config()
    download_dir = config["aria2"].get("download_dir", "./downloads")
    upload_dir = config["teldrive"].get("upload_dir", "")

    if not upload_dir:
        upload_dir = download_dir

    test_filename = f"_path_test_{uuid.uuid4().hex[:8]}.tmp"
    download_path = os.path.join(download_dir, test_filename)
    upload_path = os.path.join(upload_dir, test_filename)

    try:
        # 确保 download_dir 存在
        os.makedirs(download_dir, exist_ok=True)

        # 在 download_dir 中创建 1MB 测试文件
        with open(download_path, "wb") as f:
            f.write(b"\x00" * (1024 * 1024))

        # 检查 upload_dir 中是否能看到
        if os.path.exists(upload_path):
            return {
                "success": True,
                "message": f"✅ 路径一致！下载目录({download_dir})与上传目录({upload_dir})指向同一位置"
            }
        else:
            return {
                "success": False,
                "message": f"❌ 路径不一致！文件创建在 {download_dir}，但在 {upload_dir} 中找不到"
            }
    except Exception as e:
        return {"success": False, "message": f"测试失败: {str(e)}"}
    finally:
        # 清理测试文件
        for p in (download_path, upload_path):
            try:
                os.remove(p)
            except Exception:
                pass


