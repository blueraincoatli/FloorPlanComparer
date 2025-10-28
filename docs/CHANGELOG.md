# 更新日志

## 2025-10-28

### 新增功能
- 集成AutoCAD进行DWG到PDF的高质量转换
- 实现基于图像处理的PDF差异比较功能
- 添加增强版API端点(/api/enhanced)支持新的处理流程
- 前端添加增强模式切换功能

### 技术改进
- 使用AutoCAD COM接口直接导出PDF，提高转换质量
- 采用pdf2image + OpenCV进行像素级图像差异检测
- 实现颜色编码的差异可视化（新增=绿色，删除=红色，修改=黄色）
- 添加详细的差异统计报告

### 文件添加
- `scripts/BatchExportPDF.lsp` - AutoCAD批处理导出脚本
- `scripts/autocad_export.py` - Python调用AutoCAD的脚本
- `scripts/pdf_diff.py` - PDF图像差异比较脚本
- `scripts/test_pdf_diff.py` - PDF差异比较测试脚本
- `backend/app/modules/dwg_to_pdf/converter.py` - 更新的DWG到PDF转换器
- `backend/app/services/pdf_comparison.py` - PDF比较服务
- `backend/app/tasks/enhanced_jobs.py` - 增强版任务处理
- `backend/app/api/routes/enhanced.py` - 增强版API路由
- `frontend/src/components/EnhancedUploadForm.tsx` - 增强版上传表单

### 配置更新
- `backend/pyproject.toml` - 添加新的Python依赖(pywin32, pdf2image, opencv-python, scikit-image)
- `IMPROVEMENT_PLAN.md` - 更新改进计划文档
- `docs/test_workflow.md` - 添加测试流程文档

### 使用说明
1. 确保安装了AutoCAD
2. 安装新的Python依赖: `pip install pdf2image opencv-python scikit-image PyMuPDF pywin32`
3. 在前端界面切换到增强模式使用新功能
4. 上传两个DWG文件进行比较