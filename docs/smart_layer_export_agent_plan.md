# Floor Plan Comparer 智能图层导出代理规划文档

## 1. 项目概述

### 1.1 目标
开发一个智能代理系统，允许用户通过自然语言控制AutoCAD图层的导出行为，提升用户体验和操作效率。

### 1.2 核心功能
- 自然语言解析：将用户输入转换为标准化导出参数
- 智能图层识别：根据语义匹配相关图层
- 灵活导出控制：支持单PDF合并或分图层导出
- 用户交互优化：提供直观的自然语言输入界面

## 2. 系统架构

### 2.1 整体架构
```
用户输入(自然语言)
    ↓
自然语言处理模块
    ↓
意图识别与参数提取
    ↓
图层映射与筛选
    ↓
AutoCAD COM接口调用
    ↓
PDF导出执行
```

### 2.2 模块划分
1. **自然语言处理模块**：解析用户输入
2. **意图识别模块**：识别导出意图和图层类型
3. **参数标准化模块**：生成标准化导出参数
4. **图层处理模块**：与AutoCAD交互执行导出
5. **用户接口模块**：提供自然语言输入界面

## 3. 核心组件设计

### 3.1 自然语言处理模块

#### 3.1.1 语言解析器
```python
class NaturalLanguageParser:
    """自然语言解析器"""
    
    def __init__(self):
        # 关键词映射表
        self.keywords = {
            'layer_types': {
                '建筑': ['architecture', 'A-', 'WALL', 'DOOR', 'FLOOR'],
                '电气': ['electrical', 'E-', 'POWER', 'LIGHT', 'PLUG'],
                '给排水': ['plumbing', 'W-', 'WATER', 'DRAIN'],
                '暖通': ['hvac', 'H-', 'AIR', 'VENT'],
                '结构': ['structure', 'S-', 'BEAM', 'COLUMN'],
                '标注': ['annotation', 'TEXT', 'NOTE'],
                '尺寸': ['dimension', 'DIM']
            },
            'export_modes': {
                '单个': 'single',
                '合并': 'single',
                '分别': 'separate',
                '每个': 'separate',
                '单独': 'separate'
            },
            'actions': {
                '导出': 'export',
                '生成': 'export',
                '创建': 'export'
            }
        }
```

#### 3.1.2 意图识别器
```python
class IntentRecognizer:
    """意图识别器"""
    
    def recognize_intent(self, parsed_text: dict) -> dict:
        """识别用户意图"""
        intent = {
            'action': 'export',  # 默认动作为导出
            'layer_types': [],   # 识别的图层类型
            'export_mode': 'single',  # 默认导出模式
            'include_annotations': True,  # 是否包含标注
            'include_dimensions': True  # 是否包含尺寸
        }
        
        # 识别图层类型
        for layer_type, keywords in self.keywords['layer_types'].items():
            for keyword in keywords:
                if keyword.lower() in parsed_text['text'].lower():
                    intent['layer_types'].append(layer_type)
                    break
        
        # 识别导出模式
        for mode, keywords in self.keywords['export_modes'].items():
            for keyword in keywords:
                if keyword in parsed_text['text']:
                    intent['export_mode'] = keywords
                    break
        
        return intent
```

### 3.2 图层处理模块

#### 3.2.1 图层映射器
```python
class LayerMapper:
    """图层映射器"""
    
    def __init__(self):
        # 图层类型到实际图层名的映射
        self.layer_mapping = {
            'architecture': ['A-WALL', 'A-DOOR', 'A-WINDOW', 'A-FLOOR'],
            'electrical': ['E-POWER', 'E-LIGHT', 'E-PLUG', 'E-SWITCH'],
            'plumbing': ['W-WATER', 'W-DRAIN', 'W-VENT'],
            'hvac': ['H-AIR', 'H-VENT', 'H-DUCT'],
            'structure': ['S-BEAM', 'S-COLUMN', 'S-SLAB'],
            'annotation': ['A-TEXT', 'A-ANNO', 'A-NOTE'],
            'dimension': ['A-DIM', 'A-DIMS', 'A-DIMENSION']
        }
    
    def get_layers_by_types(self, layer_types: list, available_layers: list) -> list:
        """根据类型获取实际图层列表"""
        result_layers = []
        for layer_type in layer_types:
            if layer_type in self.layer_mapping:
                # 只返回在当前DWG中实际存在的图层
                for layer in self.layer_mapping[layer_type]:
                    if layer in available_layers:
                        result_layers.append(layer)
        return result_layers
```

#### 3.2.2 AutoCAD导出器
```python
class AutoCADExporter:
    """AutoCAD导出器"""
    
    def export_single_pdf(self, dwg_path: str, output_path: str, layers: list):
        """导出单个PDF包含指定图层"""
        acad = win32com.client.Dispatch("AutoCAD.Application")
        doc = acad.Documents.Open(dwg_path)
        
        # 控制图层可见性
        self._set_layer_visibility(doc, layers, visible=True)
        
        # 导出PDF
        doc.Export(output_path, "PDF", "")
        doc.Close(SaveChanges=False)
    
    def export_separate_pdfs(self, dwg_path: str, output_dir: str, layers: list):
        """分别导出每个图层为单独PDF"""
        acad = win32com.client.Dispatch("AutoCAD.Application")
        doc = acad.Documents.Open(dwg_path)
        
        for layer in layers:
            # 只显示当前图层
            self._set_layer_visibility(doc, [layer], visible=True)
            
            # 导出为单独PDF
            output_path = os.path.join(output_dir, f"{layer}.pdf")
            doc.Export(output_path, "PDF", "")
        
        doc.Close(SaveChanges=False)
    
    def _set_layer_visibility(self, doc, layers: list, visible: bool):
        """设置图层可见性"""
        for layer in doc.Layers:
            if layer.Name in layers:
                layer.LayerOn = visible
                layer.Freeze = not visible
            else:
                if visible:  # 如果是要显示某些图层，则隐藏其他图层
                    layer.LayerOn = False
                    layer.Freeze = True
```

### 3.3 用户接口模块

#### 3.3.1 自然语言输入组件
```tsx
// NaturalLanguageInput.tsx
import React, { useState } from 'react';

interface NaturalLanguageInputProps {
  onExport: (instruction: string) => void;
}

const NaturalLanguageInput: React.FC<NaturalLanguageInputProps> = ({ onExport }) => {
  const [instruction, setInstruction] = useState('');
  const [examples, setExamples] = useState([
    '导出电气相关的图层，包含基础平面布局和标注',
    '分别导出给排水和暖通图层',
    '生成包含所有建筑元素的单个PDF文件',
    '导出水电图层，每个图层单独一个PDF'
  ]);

  const handleSubmit = () => {
    if (instruction.trim()) {
      onExport(instruction);
    }
  };

  return (
    <div className="natural-language-input">
      <h3>智能图层导出</h3>
      <textarea
        value={instruction}
        onChange={(e) => setInstruction(e.target.value)}
        placeholder="请输入自然语言指令，例如：'导出电气相关的图层，包含基础平面布局和标注'"
        rows={4}
        style={{ width: '100%', marginBottom: '10px' }}
      />
      <button onClick={handleSubmit} style={{ marginRight: '10px' }}>
        智能导出
      </button>
      
      <div style={{ marginTop: '15px' }}>
        <h4>示例指令：</h4>
        {examples.map((example, index) => (
          <div 
            key={index} 
            onClick={() => setInstruction(example)}
            style={{ 
              cursor: 'pointer', 
              padding: '5px', 
              backgroundColor: '#f0f0f0',
              marginBottom: '5px',
              borderRadius: '3px'
            }}
          >
            {example}
          </div>
        ))}
      </div>
    </div>
  );
};
```

## 4. API设计

### 4.1 端点定义
```
POST /api/smart-export/process
{
  "dwg_file": "string",           // DWG文件路径
  "instruction": "string",        // 自然语言指令
  "output_mode": "single|separate" // 导出模式
}
```

### 4.2 响应格式
```json
{
  "status": "success|error",
  "message": "string",
  "result": {
    "exported_files": ["file1.pdf", "file2.pdf"],
    "layers_processed": ["A-WALL", "E-POWER"],
    "export_mode": "single"
  }
}
```

### 4.3 后端实现
```python
# app/api/routes/smart_export.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.smart_export import SmartExportService

router = APIRouter(prefix="/smart-export", tags=["smart-export"])

class SmartExportRequest(BaseModel):
    dwg_file: str
    instruction: str
    output_mode: str = "single"

class SmartExportResponse(BaseModel):
    status: str
    message: str
    result: dict

@router.post("/process", response_model=SmartExportResponse)
async def process_smart_export(request: SmartExportRequest):
    try:
        service = SmartExportService()
        result = service.process_request(request.dwg_file, request.instruction, request.output_mode)
        return SmartExportResponse(
            status="success",
            message="导出完成",
            result=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 5. 数据模型

### 5.1 导出配置模型
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ExportConfig:
    """导出配置"""
    layers: List[str]              # 要导出的图层列表
    export_mode: str = "single"    # 导出模式: single, separate
    include_base: bool = True      # 是否包含基础图层
    include_annotations: bool = True  # 是否包含标注
    include_dimensions: bool = True   # 是否包含尺寸
    output_directory: str = ""     # 输出目录
```

### 5.2 处理结果模型
```python
@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    exported_files: List[str]
    processed_layers: List[str]
    processing_time: float
    error_message: Optional[str] = None
```

## 6. 实施计划

### 6.1 第一阶段：核心功能实现（2周）
1. **第1周**：
   - 实现自然语言解析器
   - 开发意图识别模块
   - 创建图层映射器

2. **第2周**：
   - 实现AutoCAD导出器
   - 开发参数标准化模块
   - 完成基础API端点

### 6.2 第二阶段：用户界面集成（1周）
1. 开发自然语言输入组件
2. 集成前端与后端API
3. 实现示例指令展示

### 6.3 第三阶段：优化与扩展（1周）
1. 优化图层识别准确率
2. 添加更多图层类型支持
3. 实现错误处理和用户反馈

## 7. 测试计划

### 7.1 单元测试
```python
def test_natural_language_parser():
    """测试自然语言解析"""
    parser = NaturalLanguageParser()
    result = parser.parse("导出电气相关的图层，包含基础平面布局和标注")
    assert 'electrical' in result['layer_types']
    assert result['export_mode'] == 'single'

def test_layer_mapper():
    """测试图层映射"""
    mapper = LayerMapper()
    available_layers = ['E-POWER', 'E-LIGHT', 'A-WALL']
    result = mapper.get_layers_by_types(['electrical'], available_layers)
    assert 'E-POWER' in result
    assert 'E-LIGHT' in result
```

### 7.2 集成测试
1. 测试完整的自然语言到PDF导出流程
2. 验证不同导出模式的正确性
3. 测试错误处理机制

## 8. 部署要求

### 8.1 环境依赖
- AutoCAD 2018或更高版本
- Python 3.11+
- Windows操作系统（用于COM接口）
- 相关Python包：pywin32, fastapi, uvicorn

### 8.2 配置要求
```env
# .env文件配置
FLOORPLAN_SMART_EXPORT_ENABLED=true
FLOORPLAN_LAYER_MAPPING_PATH=config/layer_mapping.json
```

## 9. 扩展功能

### 9.1 高级图层识别
- 支持正则表达式匹配
- 添加用户自定义图层映射
- 实现图层智能推荐

### 9.2 多语言支持
- 支持中英文自然语言输入
- 添加国际化界面

### 9.3 批量处理
- 支持多个DWG文件批量处理
- 添加处理队列管理

## 10. 风险评估

### 10.1 技术风险
1. **AutoCAD COM接口稳定性**：需要处理COM调用异常
2. **自然语言理解准确率**：可能需要持续优化关键词映射
3. **性能问题**：大量图层处理可能影响性能

### 10.2 解决方案
1. 添加COM调用重试机制
2. 实现用户反馈学习机制
3. 优化图层处理算法