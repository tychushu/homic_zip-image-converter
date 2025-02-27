# homic_zip-image-converter
一个 Python 脚本，用于批量将 ZIP 文件中的 JPG 和 PNG 图片转换为 WebP 格式，并重新打包成新的 ZIP 文件。支持并发处理和错误日志记录。 
 A Python script to batch convert JPG and PNG images in ZIP files to WebP format and repackage them into new ZIP files. Supports concurrent processing and error logging.




## 描述 / Description

### 中文
`homic_zip-image-converter` 是一个 Python 脚本，旨在帮助用户批量处理 ZIP 文件中的 JPG 和 PNG 图片，将其转换为 WebP 格式，并重新打包成新的 ZIP 文件。该脚本支持并发处理以提高效率，并提供错误日志记录以便于调试和监控。

### 英文
`homic_zip-image-converter` is a Python script designed to help users batch process JPG and PNG images in ZIP files, convert them to WebP format, and repackage them into new ZIP files. The script supports concurrent processing for improved efficiency and provides error logging for debugging and monitoring.

## 功能 / Features

- **批量处理**：自动检测并处理当前目录中的所有 ZIP 文件。  
- **图片转换**：将 ZIP 文件中的 JPG 和 PNG 图片转换为 WebP 格式。  
- **并发处理**：支持多进程并发转换图片，提高处理速度。  
- **错误日志**：记录转换过程中的错误和警告，便于排查问题。  
- **智能跳过**：自动跳过不包含 JPG/PNG 图片或包含 GIF 的 ZIP 文件，以及之前转换后体积未减小的文件。  
- **进度条**：提供直观的进度条，显示处理进度和统计信息。  

- **Batch processing**: Automatically detects and processes all ZIP files in the current directory.  
- **Image conversion**: Converts JPG and PNG images in ZIP files to WebP format.  
- **Concurrent processing**: Supports multi-process concurrent image conversion for faster processing.  
- **Error logging**: Logs errors and warnings during conversion for easy debugging.  
- **Smart skipping**: Automatically skips ZIP files without JPG/PNG images, with GIFs, or previously processed files where size didn’t reduce.  
- **Progress bar**: Provides intuitive progress bars to display processing progress and statistics.

## 安装 / Installation

### 中文
1. **依赖安装**：确保已安装 Python 3.6+，并安装以下依赖：  
   ```bash
   pip install tqdm asyncio
工具安装：需要安装 7zz（7-Zip） 和 cwebp（WebP 转换工具）：  
7zz：从 7-Zip 官网 下载并安装。  

cwebp：从 WebP 官网 下载并安装。
确保 7zz 和 cwebp 已添加到系统 PATH 中。

英文
Install dependencies: Ensure Python 3.6+ is installed and install the following dependencies:  
bash

pip install tqdm asyncio

Tool installation: Install 7zz (7-Zip) and cwebp (WebP conversion tool):  
7zz: Download and install from 7-Zip official website.  

cwebp: Download and install from WebP official website.
Ensure 7zz and cwebp are accessible in the system PATH.

用法 / Usage
中文
准备 ZIP 文件：将需要处理的 ZIP 文件放置在脚本所在目录。  

运行脚本：在终端中执行：  
bash

python zip_image_converter.py

或者指定单个 ZIP 文件：  
bash

python zip_image_converter.py path/to/your/file.zip

查看进度：脚本将显示处理进度和统计信息。  

检查日志：错误和警告将记录在 unzip_error.log 文件中。

英文
Prepare ZIP files: Place the ZIP files to be processed in the script’s directory.  

Run the script: Execute in the terminal:  
bash

python zip_image_converter.py

Or specify a single ZIP file:  
bash

python zip_image_converter.py path/to/your/file.zip

Monitor progress: The script will display processing progress and statistics.  

Check logs: Errors and warnings are logged in unzip_error.log.

配置 / Configuration
中文
脚本中的配置参数可以在脚本顶部修改：  
QUALITY：WebP 转换质量（默认 95）。  

THREADS：并发进程数（默认 9）。  

WORKING_DIR：默认解压目录（用于小文件）。  

LARGE_WORKING_DIR：大文件解压目录。  

TMPFS_THRESHOLD：TMPFS 大小阈值。  

LARGE_FILE_THRESHOLD：大文件阈值。  

ZIP_MOVE_THRESHOLD：ZIP 移动阈值。

英文
Configuration parameters can be modified at the top of the script:  
QUALITY: WebP conversion quality (default 95).  

THREADS: Number of concurrent processes (default 9).  

WORKING_DIR: Default extraction directory (for small files).  

LARGE_WORKING_DIR: Extraction directory for large files.  

TMPFS_THRESHOLD: TMPFS size threshold.  

LARGE_FILE_THRESHOLD: Large file threshold.  

ZIP_MOVE_THRESHOLD: ZIP move threshold.

注意事项 / Notes
中文
确保解压目录有足够的剩余空间。  

脚本会覆盖原始 ZIP 文件，请备份重要数据。  

转换后的 ZIP 文件将替换原始文件，原始图片将被删除。  

如果转换后文件大小未减小，脚本将跳过该文件并记录日志。

英文
Ensure sufficient free space in the extraction directories.  

The script will overwrite original ZIP files; back up important data.  

Converted ZIP files will replace the originals, and original images will be deleted.  

If the converted file size does not decrease, the script will skip the file and log the event.

许可证 / License
中文
本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。
英文
This project is licensed under the MIT License. See the LICENSE file for details.

