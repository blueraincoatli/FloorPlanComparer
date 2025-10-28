# Floor Plan Comparer 测试流程

## 1. 安装依赖
```bash
# 运行安装脚本
scripts\install_deps.bat
```

## 2. 准备测试数据
将两个DWG文件放入测试目录：
- samples/original.dwg (原始图纸)
- samples/modified.dwg (修改后的图纸)

## 3. 使用AutoCAD导出PDF
```bash
# 使用AutoCAD脚本导出PDF
python scripts\autocad_export.py samples\original.dwg temp\original.pdf
python scripts\autocad_export.py samples\modified.dwg temp\modified.pdf
```

## 4. 比较PDF差异
```bash
# 比较两个PDF文件
python scripts\pdf_diff.py temp\original.pdf temp\modified.pdf temp\diff_result.png
```

## 5. 查看结果
- temp\original.pdf (原始PDF)
- temp\modified.pdf (修改后PDF)
- temp\diff_result.png (差异标记图像)

## 6. 集成到现有系统（可选）
将新功能集成到现有的FastAPI后端中：
1. 更新转换器模块以使用AutoCAD脚本
2. 添加新的PDF比较端点
3. 更新前端以显示差异图像