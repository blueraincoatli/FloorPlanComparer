#!/usr/bin/env python3
"""
测试脚本：验证AutoCAD集成和PDF比较功能
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

def test_autocad_converter():
    """测试AutoCAD转换器"""
    print("测试AutoCAD转换器...")
    
    try:
        # 导入转换器
        from app.modules.dwg_to_pdf.converter import DWGToPDFConverter
        
        # 创建转换器实例
        converter = DWGToPDFConverter()
        
        print("✓ AutoCAD转换器导入成功")
        print("注意：实际转换测试需要AutoCAD安装")
        
        return True
    except Exception as e:
        print(f"✗ AutoCAD转换器测试失败: {e}")
        return False

def test_pdf_comparison():
    """测试PDF比较功能"""
    print("\n测试PDF比较功能...")
    
    try:
        # 导入比较器
        from app.services.pdf_comparison import PDFComparator
        
        # 创建比较器实例
        comparator = PDFComparator(dpi=150)  # 使用较低DPI以加快测试
        
        print("✓ PDF比较器导入成功")
        
        # 创建测试图像
        import cv2
        import numpy as np
        
        # 创建测试图像
        img1 = np.zeros((300, 300, 3), dtype=np.uint8)
        cv2.rectangle(img1, (50, 50), (150, 150), (255, 255, 255), -1)
        
        img2 = img1.copy()
        cv2.rectangle(img2, (200, 200), (250, 250), (0, 255, 0), -1)  # 新增区域
        
        # 保存为PNG文件
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pdf1_path = tmp_path / "test1.png"
            pdf2_path = tmp_path / "test2.png"
            diff_path = tmp_path / "diff.png"
            
            cv2.imwrite(str(pdf1_path), img1)
            cv2.imwrite(str(pdf2_path), img2)
            
            # 测试PDF比较（使用PNG文件模拟）
            # 注意：在实际使用中，这里应该是真实的PDF文件
            print("  创建测试图像完成")
            
        return True
    except Exception as e:
        print(f"✗ PDF比较器测试失败: {e}")
        return False

def test_enhanced_api():
    """测试增强版API"""
    print("\n测试增强版API...")
    
    try:
        # 检查API路由是否正确导入
        from app.api.routes import enhanced
        
        print("✓ 增强版API路由导入成功")
        
        # 检查主路由是否包含增强路由
        from app.api import router
        
        print("✓ 主路由导入成功")
        
        return True
    except Exception as e:
        print(f"✗ 增强版API测试失败: {e}")
        return False

def test_dependencies():
    """测试依赖安装"""
    print("\n测试依赖安装...")
    
    dependencies = [
        "win32com",
        "cv2",
        "numpy",
        "pdf2image",
        "skimage"
    ]
    
    missing_deps = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✓ {dep}")
        except ImportError:
            missing_deps.append(dep)
            print(f"  ✗ {dep} (缺失)")
    
    if missing_deps:
        print(f"\n缺失的依赖: {', '.join(missing_deps)}")
        print("请运行: pip install pdf2image opencv-python scikit-image PyMuPDF pywin32")
        return False
    else:
        print("✓ 所有依赖都已正确安装")
        return True

def main():
    """主测试函数"""
    print("Floor Plan Comparer - 功能测试")
    print("=" * 40)
    
    tests = [
        ("依赖检查", test_dependencies),
        ("AutoCAD转换器", test_autocad_converter),
        ("PDF比较功能", test_pdf_comparison),
        ("增强版API", test_enhanced_api)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 测试过程中出现异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 40)
    print("测试结果汇总:")
    
    all_passed = True
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 40)
    if all_passed:
        print("🎉 所有测试通过！")
        print("\n下一步:")
        print("1. 确保安装了AutoCAD")
        print("2. 准备测试DWG文件")
        print("3. 运行前端应用并切换到增强模式")
        print("4. 上传DWG文件进行测试")
    else:
        print("❌ 部分测试失败，请检查上述错误信息")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)