# Floor Plan Comparer 增强版功能测试指南

## 概述

本文档介绍了如何测试Floor Plan Comparer的增强版功能，包括AutoCAD集成的DWG到PDF转换和基于图像处理的PDF差异比较。

## 测试前准备

### 1. 环境要求
- AutoCAD 2018或更高版本（用于DWG转换）
- Python 3.11或更高版本
- Windows操作系统（用于AutoCAD COM接口）

### 2. 依赖安装
```bash
# 在项目根目录运行
cd D:\FloorPlanComparer
uv run --project backend pip install pdf2image opencv-python scikit-image PyMuPDF pywin32
```

### 3. 测试数据准备
准备两个DWG文件用于测试：
- `samples/original.dwg` (原始图纸)
- `samples/modified.dwg` (修改后的图纸)

## 功能测试

### 1. 依赖检查
```bash
cd D:\FloorPlanComparer
uv run --project backend python scripts\check_deps.py
```

预期输出：
```
✓ win32com.client imported successfully
✓ cv2 imported successfully
✓ numpy imported successfully
✓ pdf2image imported successfully
✓ skimage imported successfully
✓ PyMuPDF imported successfully

Dependency check completed
```

### 2. AutoCAD转换器测试
```bash
cd D:\FloorPlanComparer
uv run --project backend python -c "from app.modules.dwg_to_pdf.converter import DWGToPDFConverter; print('AutoCAD转换器导入成功')"
```

### 3. PDF比较功能测试
```bash
cd D:\FloorPlanComparer
uv run --project backend python -c "from app.services.pdf_comparison import PDFComparator; print('PDF比较器导入成功')"
```

## 端到端测试

### 1. 启动后端服务
```bash
cd D:\FloorPlanComparer\backend
uv run uvicorn app.main:app --reload --port 8000
```

### 2. 启动前端应用
```bash
cd D:\FloorPlanComparer\frontend
npm run dev
```

### 3. 使用增强功能
1. 打开浏览器访问 http://localhost:5173
2. 点击"切换到增强模式"按钮
3. 上传两个DWG文件
4. 等待处理完成
5. 查看差异结果

## API测试

### 1. 增强版API端点
- POST `/api/enhanced/process-dwg` - 处理DWG文件
- GET `/api/enhanced/job/{job_id}` - 获取任务状态

### 2. 使用curl测试
```bash
# 上传文件
curl -X POST "http://localhost:8000/api/enhanced/process-dwg" \
  -F "origin_file=@samples/original.dwg" \
  -F "target_file=@samples/modified.dwg"

# 获取任务状态
curl "http://localhost:8000/api/enhanced/job/{job_id}"
```

## 故障排除

### 1. AutoCAD相关问题
- 确保AutoCAD已正确安装
- 确保AutoCAD支持COM接口
- 检查AutoCAD是否在后台运行

### 2. 依赖问题
- 确保所有Python依赖已正确安装
- 检查Python版本兼容性

### 3. 权限问题
- 确保应用有读写文件的权限
- 确保AutoCAD可以访问指定的文件路径

## 预期结果

### 1. DWG到PDF转换
- 高质量的PDF输出
- 保持原始DWG的图形精度
- 正确的页面尺寸和布局

### 2. PDF差异比较
- 准确的差异检测
- 颜色编码的差异可视化
  - 新增内容：绿色标记
  - 删除内容：红色标记
  - 修改内容：黄色标记
- 详细的差异统计报告

## 性能指标

### 1. 转换时间
- 单个DWG文件转换时间：< 30秒
- 批量转换时间：取决于文件数量和复杂度

### 2. 比较时间
- PDF图像比较时间：< 10秒（取决于图像分辨率）

### 3. 内存使用
- 峰值内存使用：< 500MB（取决于文件大小）