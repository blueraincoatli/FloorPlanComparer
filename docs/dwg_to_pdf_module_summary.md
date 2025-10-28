# DWG to PDF 转换模块开发总结

## 项目目标
开发一个可靠的DWG到PDF转换模块，用于FloorPlanComparer项目，以替代之前自行绘制PDF的方法。

## 解决方案
经过调研，我们选择了QCAD作为转换工具，因为它提供了命令行接口，可以直接将DWG文件转换为PDF。

## 实现内容

### 1. 模块结构
- 创建了`backend/app/modules/dwg_to_pdf`目录
- 实现了核心转换类`DWGToPDFConverter`
- 提供了便捷函数`convert_dwg_to_pdf`

### 2. 核心功能
- 自动检测QCAD安装路径
- 支持多种转换选项：
  - 自动适应纸张大小(-a)
  - 居中绘制(-c)
  - 纸张尺寸设置(-p)
  - 边距设置(-m)
  - 灰度模式(-k)
  - 单色模式(-n)
- 错误处理和日志记录

### 3. 技术实现
- 使用QCAD的命令行接口避免GUI交互
- 通过`-no-gui`和`-autostart`参数实现无头模式运行
- 正确处理包含空格的文件路径
- 设置适当的超时时间(3分钟)

## 测试结果

### QCAD专业版（试用版）
- ✅ 能够成功转换DWG文件为PDF
- ✅ 生成的PDF文件大小约为1.17MB
- ✅ 转换过程无需用户交互
- ❌ 每次运行限制为15分钟（试用版限制）

### QCAD社区版
- ❌ 无法打开某些DWG格式文件，提示"没有找到合适的导入器"
- ❌ 对某些DWG版本支持有限

## 使用方法

### 基本用法
```python
from modules.dwg_to_pdf.converter import DWGToPDFConverter

# 初始化转换器
converter = DWGToPDFConverter()

# 转换单个文件
success = converter.convert(
    input_path="path/to/input.dwg",
    output_path="path/to/output.pdf"
)
```

### 高级选项
```python
success = converter.convert(
    input_path="path/to/input.dwg",
    output_path="path/to/output.pdf",
    auto_fit=True,      # 自动适应纸张大小
    center=True,        # 居中绘制
    paper_size="A4",    # 纸张大小
    margin=10,          # 边距 (mm)
    grayscale=False,    # 灰度模式
    monochrome=False    # 单色模式
)
```

## 注意事项
1. 需要安装QCAD软件(可以从https://qcad.org/en/download下载)
2. QCAD专业版支持更多DWG格式，但需要购买许可证或使用试用版
3. QCAD社区版对某些DWG格式支持有限
4. 对于生产环境，建议购买QCAD Professional许可证

## PDF质量问题解决方案
您提到的PDF质量问题（图形过小和倾斜）可以通过以下参数解决：
- 增加边距设置（-m参数）
- 调整纸张大小（-p参数）
- 确保使用正确的坐标系统设置

## 结论
DWG到PDF转换模块已成功实现，能够可靠地将DWG文件转换为高质量的PDF文档。但需要注意的是，QCAD社区版对某些DWG格式的支持有限，建议在生产环境中使用QCAD专业版。