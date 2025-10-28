# Floor Plan Comparer 改进计划

## 当前问题分析

1. ODA File Converter生成的PDF质量不佳
2. 几何实体匹配精度不够
3. 坐标对齐算法需要优化

## 新的改进方案

### 方案一：基于AutoCAD脚本的转换流程

#### 1. AutoLISP脚本开发
```lisp
(defun c:BatchExportPDF (/ source_dir target_dir dwg_files file_count)

  ; 获取源文件夹路径
  (setq source_dir (getstring "\n选择源DWG文件夹: "))
  (setq target_dir (getstring "\n选择目标PDF文件夹: "))

  ; 获取DWG文件列表
  (setq dwg_files (getdwgfiles source_dir))

  ; 计数器
  (setq file_count 0)

  ; 遍历文件列表
  (foreach dwg_file dwg_files
    ; 打开DWG文件
    (command "_.open" dwg_file)
    
    ; 等待文档打开
    (while (= (getvar "DWGTITLED") 0)
      (grread)
    )

    ; 选择布局（这里选择模型空间）
    (setvar "CTAB" "Model")
    
    ; 导出为PDF
    (setq pdf_name (strcat target_dir "\\" (vl-filename-base dwg_file) ".pdf"))
    (command "_.pdfexport" pdf_name)
    
    ; 关闭文档（不保存）
    (command "_.close" "N")
    
    ; 更新计数器
    (setq file_count (1+ file_count))
    (princ (strcat "\n已处理文件 " (itoa file_count) ": " dwg_file))
  )

  ; 完成提示
  (princ (strcat "\n完成处理 " (itoa file_count) " 个文件"))
  (princ)
)

; 获取指定目录中的所有DWG文件
(defun getdwgfiles (dir / files)
  (setq files (findfiles (strcat dir "\\*.dwg") 1))
  files
)

; 计算文件名（不带扩展名）
(defun vl-filename-base (filename / pos)
  (setq pos (vl-string-position 46 filename)) ; 46 is ASCII for '.'
  (if pos
    (substr filename 1 pos)
    filename
  )
)
```

#### 2. 集成到Python流程
- 调用AutoCAD执行LISP脚本
- 等待转换完成
- 继续后续处理

### 方案二：PDF图像差异比较

#### 1. PDF转图像
使用pdf2image库将PDF转换为高分辨率图像：
```python
from pdf2image import convert_from_path
images = convert_from_path('file.pdf', dpi=300)
```

#### 2. 图像差异检测
使用OpenCV进行图像差异检测：
```python
import cv2
import numpy as np

# 读取图像
img1 = cv2.imread('image1.png')
img2 = cv2.imread('image2.png')

# 转换为灰度图
gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

# 计算差异
diff = cv2.absdiff(gray1, gray2)
```

#### 3. 差异可视化
- 使用不同颜色标记新增、删除、修改部分
- 生成差异标记图像

### 方案三：PDF矢量元素比较

#### 1. PDF解析
使用PyMuPDF提取矢量元素：
```python
import fitz  # PyMuPDF
doc = fitz.open("file.pdf")
page = doc[0]
paths = page.get_drawings()
```

#### 2. 元素匹配
- 比较路径、文本和图形元素
- 计算相似度和差异

## 推荐实施步骤

### 第一阶段：AutoCAD脚本开发
1. 开发AutoLISP批处理脚本
2. 实现DWG到PDF的转换
3. 测试转换质量

### 第二阶段：PDF比较实现
1. 实现PDF转图像功能
2. 开发图像差异检测算法
3. 添加差异可视化

### 第三阶段：集成优化
1. 集成到现有系统
2. 优化性能和准确性
3. 添加配置选项

## 技术选型

### AutoCAD集成
- AutoLISP脚本
- COM接口调用

### PDF处理
- pdf2image (PDF转图像)
- PyMuPDF (PDF解析)
- OpenCV (图像处理)

### 差异检测
- 像素级比较
- 结构相似性(SSIM)算法
- 轮廓检测

## 依赖安装

### Python依赖
```bash
pip install pdf2image opencv-python scikit-image PyMuPDF pywin32
```

### 系统依赖
1. AutoCAD（用于DWG到PDF转换）
2. Poppler（用于pdf2image，Windows可以从https://github.com/oschwartz10612/poppler-windows下载）

## 预期优势

1. 更高的转换质量（使用AutoCAD原生导出）
2. 更准确的差异检测
3. 更好的可视化效果
4. 保持现有系统架构