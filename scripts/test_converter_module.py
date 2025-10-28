"""
测试现有的DWG到PDF转换器模块
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

def test_converter_module():
    """测试转换器模块"""
    try:
        from app.modules.dwg_to_pdf.converter import DWGToPDFConverter
        
        # 创建转换器实例
        converter = DWGToPDFConverter()
        print("✓ DWGToPDFConverter 导入成功")
        
        return converter
    except Exception as e:
        print(f"✗ DWGToPDFConverter 导入失败: {e}")
        return None

def test_conversion(input_dwg, output_pdf):
    """测试转换功能"""
    try:
        from app.modules.dwg_to_pdf.converter import convert_dwg_to_pdf
        
        print(f"正在转换: {input_dwg} -> {output_pdf}")
        success = convert_dwg_to_pdf(input_dwg, output_pdf)
        
        if success:
            print("✓ 转换成功")
            if os.path.exists(output_pdf):
                print(f"  PDF文件已生成: {output_pdf}")
                file_size = os.path.getsize(output_pdf)
                print(f"  文件大小: {file_size} 字节")
            return True
        else:
            print("✗ 转换失败")
            return False
            
    except Exception as e:
        print(f"✗ 转换过程中出现错误: {e}")
        return False

if __name__ == "__main__":
    print("DWG到PDF转换器测试")
    print("=" * 30)
    
    # 测试模块导入
    print("\n1. 测试模块导入:")
    converter = test_converter_module()
    if not converter:
        exit(1)
    
    # 测试转换功能
    print("\n2. 测试转换功能:")
    test_dwg = r"D:\test.dwg"  # 请修改为实际的DWG文件路径
    test_pdf = r"D:\test_output.pdf"
    
    if os.path.exists(test_dwg):
        test_conversion(test_dwg, test_pdf)
    else:
        print(f"提示: 请准备测试文件 {test_dwg}")
        print("您可以:")
        print("1. 创建一个简单的DWG文件")
        print("2. 或修改脚本中的文件路径")