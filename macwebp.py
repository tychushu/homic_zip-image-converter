import os
import shutil
import subprocess
import sys
import time
import asyncio
import gc
from pathlib import Path
from tqdm import tqdm

# ======= 配置 =======
QUALITY = 95  # WebP 质量
THREADS = 9  # 并发进程数
WORKING_DIR = Path("/Users/tycushu/ramdisk/extemp")  # 默认解压目录（≤ 900MB）
LARGE_WORKING_DIR = Path("/Users/tycushu/ssd/temp")  # 大文件解压目录（> 900MB）
CURRENT_DIR = Path.cwd()
TMPFS_THRESHOLD = 495 * 1024 * 1024  # 495MB
LARGE_FILE_THRESHOLD = 800 * 1024 * 1024  # 800MB
ZIP_MOVE_THRESHOLD = 950 * 1024 * 1024  # 950MB
FAILED_FLAG = WORKING_DIR / "webp_conversion_failed.log"
ERROR_LOG = CURRENT_DIR / "unzip_error.log"

# ======= 记录错误日志 =======
def log_error(message):
    with ERROR_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

# ======= 检测 ZIP 文件 =======
if len(sys.argv) > 1:
    ZIP_FILES = [Path(sys.argv[1])]
else:
    ZIP_FILES = list(CURRENT_DIR.glob("*.zip"))

if not ZIP_FILES:
    print("❌ 当前目录无 ZIP 文件，退出。")
    sys.exit(1)

# ======= 统计信息 =======
total_zip_count = len(ZIP_FILES)
processed_zip_count = 0
total_processing_time = 0
total_original_size = 0
total_converted_size = 0

# ======= 总进度条 =======
total_progress = tqdm(
    ZIP_FILES,
    desc="总进度",
    unit="ZIP",
    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
    colour="GREEN"
)

# ======= 预检查逻辑 =======
def should_skip_zip(zip_file):
    """检查是否跳过该 ZIP 文件"""
    # 检查错误日志中是否已有体积未减小的记录
    if ERROR_LOG.exists():
        with ERROR_LOG.open("r", encoding="utf-8") as log_file:
            for line in log_file:
                if f"⚠️ WebP 转换后大小未减少: {zip_file}" in line:
                    total_progress.write(f"⚠️ 跳过 {zip_file}，已记录转换后体积未减小")
                    return True

    # 检查 ZIP 文件内容
    list_result = subprocess.run(
        ["7zz", "l", str(zip_file)],
        capture_output=True, text=True
    )
    if list_result.returncode != 0:
        total_progress.write(f"❌ 无法列出 {zip_file} 内容，跳过")
        return True

    file_list = list_result.stdout.lower().splitlines()
    has_image = any(line.strip().endswith((".jpg", ".png")) for line in file_list if line.strip())
    has_gif = any(line.strip().endswith(".gif") for line in file_list if line.strip())

    if not has_image:
        total_progress.write(f"⚠️ {zip_file} 内无 JPG/PNG 图片，跳过")
        return True
    if has_gif:
        total_progress.write(f"⚠️ {zip_file} 内有 GIF 文件，跳过")
        return True

    return False

# ======= 主循环 =======
for zip_file in total_progress:
    start_time = time.time()
    working_dir = None
    try:
        total_progress.set_postfix_str(f"正在处理 {zip_file.name}", refresh=False)
        zip_file = zip_file.resolve()

        # **选择解压路径**
        zip_size = zip_file.stat().st_size
        working_dir = WORKING_DIR if zip_size <= LARGE_FILE_THRESHOLD else LARGE_WORKING_DIR

        # **清空解压目录**
        shutil.rmtree(working_dir, ignore_errors=True)
        working_dir.mkdir(parents=True, exist_ok=True)

        # **预检查：决定是否跳过该 ZIP 文件**
        if should_skip_zip(zip_file):
            continue

        # **解压操作**
        total_progress.write(f"📦 解压中: '{zip_file}' -> {working_dir}")
        unzip_start = time.time()
        unzip_result = subprocess.run(
            ["7zz", "e", str(zip_file), f"-o{working_dir}", "-y"],
            capture_output=True, text=True
        )
        unzip_time = time.time() - unzip_start

        if unzip_result.returncode != 0:
            log_error(f"❌ 解压失败: {zip_file}\n错误代码: {unzip_result.returncode}\n{unzip_result.stderr}")
            total_progress.write(f"❌ 解压失败，跳过: {zip_file}，详情记录在 unzip_error.log")
            continue

        total_progress.write(f"⏱️ 解压耗时: {unzip_time:.2f} 秒")

        # **计算解压后文件大小**
        total_size = sum(f.stat().st_size for f in working_dir.glob("**/*") if f.is_file())
        total_original_size += total_size
        total_progress.write(f"📊 解压后文件总大小: {total_size / 1024 / 1024:.2f} MB")

        # **获取待转换的图片文件**
        images = list(working_dir.glob("*.jpg")) + list(working_dir.glob("*.png"))
        if not images:
            total_progress.write("⚠️ 没有可转换的图片，跳过。")
            continue

        # **执行 WebP 转换**
        concurrency = min(THREADS, 9)
        FAILED_FLAG.unlink(missing_ok=True)
        total_progress.write(f"🎨 转换图片 - 质量: {QUALITY} - 并发进程: {concurrency}")

        # **图片转换进度条**
        conversion_progress = tqdm(
            total=len(images),
            desc="图片转换",
            unit="img",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            colour="BLUE"
        )

        conversion_start = time.time()

        async def convert_image(image):
            output_file = image.with_suffix(".webp")
            process = await asyncio.create_subprocess_exec(
                "cwebp",
                "-q", str(QUALITY),
                "-m", "6",
                "-af",
                str(image),
                "-o", str(output_file),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            await process.wait()

            if process.returncode != 0:
                return image
            else:
                image.unlink(missing_ok=True)
                return None

        async def convert_image_with_progress(image, sem, progress):
            async with sem:
                result = await convert_image(image)
                progress.update(1)  # 每完成一个图片转换，实时更新进度条
                return result

        async def convert_images_async():
            sem = asyncio.Semaphore(concurrency)
            tasks = []
            for img in images:
                task = asyncio.create_task(convert_image_with_progress(img, sem, conversion_progress))
                tasks.append(task)
            results = await asyncio.gather(*tasks)
            return results

        failed_images = asyncio.run(convert_images_async())

        failed_images = [img for img in failed_images if img is not None]
        if failed_images:
            with FAILED_FLAG.open("a") as f:
                for image in failed_images:
                    f.write(f"{image}\n")

        conversion_time = time.time() - conversion_start
        conversion_progress.close()
        total_progress.write(f"⏱️ 图片转换耗时: {conversion_time:.2f} 秒")

        if FAILED_FLAG.exists():
            total_progress.write("❌ 部分图片转换失败，跳过打包。")
            shutil.rmtree(working_dir, ignore_errors=True)
            continue

        # **计算转换后文件大小**
        new_zip_size = sum(f.stat().st_size for f in working_dir.glob("*.webp"))
        total_converted_size += new_zip_size

        if new_zip_size >= total_size * 0.95:
            total_progress.write(f"⚠️ WebP 转换后 {new_zip_size / 1024 / 1024:.2f} MB 大小未减少（原大小: {total_size / 1024 / 1024:.2f} MB)，跳过打包。")
            log_error(f"⚠️ WebP 转换后大小未减少: {zip_file}")
            shutil.rmtree(working_dir, ignore_errors=True)
            continue
        else:
            total_progress.write(f"⚠️ WebP 转换后 {new_zip_size / 1024 / 1024:.2f} MB")

        # **选择 ZIP 存放路径**
        if zip_size <= LARGE_FILE_THRESHOLD:
            if new_zip_size <= TMPFS_THRESHOLD:
                zip_output_dir = WORKING_DIR
            else:
                zip_output_dir = CURRENT_DIR
        else:
            if new_zip_size < ZIP_MOVE_THRESHOLD:
                zip_output_dir = WORKING_DIR
            else:
                zip_output_dir = LARGE_WORKING_DIR

        total_progress.write(f"📦 转换后 ZIP 存放于: {zip_output_dir}")
        new_zip_file = zip_output_dir / f"{zip_file.stem}_converted.zip"

        # **重新打包 ZIP**
        total_progress.write(f"📦 重新打包 ZIP: {new_zip_file}")
        webp_files = list(working_dir.glob("*.webp"))

        if webp_files:
            zip_start = time.time()
            subprocess.run(
                ["7zz", "a", "-mx=0", "-tzip", str(new_zip_file)] + [str(f) for f in webp_files],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            zip_time = time.time() - zip_start
            total_progress.write(f"⏱️ 打包耗时: {zip_time:.2f} 秒")
        else:
            total_progress.write("⚠️ 没有可压缩的 WebP 文件，跳过。")
            continue

        # **计算最终 ZIP 文件大小**
        final_zip_size = new_zip_file.stat().st_size
        total_progress.write(f"📦 压缩包转换后大小: {final_zip_size / 1024 / 1024:.2f} MB")

        # **优化 ZIP 替换逻辑**
        total_progress.write(f"🔄 替换 ZIP 文件: {zip_file}")
        zip_file.unlink()
        shutil.move(str(new_zip_file), str(zip_file))

        # **记录处理时间**
        processing_time = time.time() - start_time
        total_processing_time += processing_time
        processed_zip_count += 1
        total_progress.write(f"⏱️ 任务完成: {zip_file} | 总耗时: {processing_time:.2f} 秒")

    except Exception as e:
        total_progress.write(f"❌ 错误: {str(e)}")
        log_error(f"❌ 处理 ZIP 文件时发生错误: {zip_file}\n{str(e)}")

    finally:
        if working_dir and working_dir.exists():
            shutil.rmtree(working_dir, ignore_errors=True)
        gc.collect()

total_progress.close()

# ======= 输出统计信息 =======
if processed_zip_count > 0:
    average_processing_time = total_processing_time / processed_zip_count
    size_reduction_percentage = ((total_original_size - total_converted_size) / total_original_size) * 100 if total_original_size > 0 else 0
    print(f"📊 统计信息：")
    print(f"  - 处理的 ZIP 文件数：{processed_zip_count}")
    print(f"  - 平均处理时间：{average_processing_time:.2f} 秒")
    print(f"  - 总原始大小：{total_original_size / 1024 / 1024:.2f} MB")
    print(f"  - 总转换后大小：{total_converted_size / 1024 / 1024:.2f} MB")
    print(f"  - 大小减少百分比：{size_reduction_percentage:.2f}%")
else:
    print("📊 统计信息：无 ZIP 文件被处理。")
