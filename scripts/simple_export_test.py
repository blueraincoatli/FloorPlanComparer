import win32com.client
import pythoncom
import os
import sys

def simple_export_test():
    """简单的导出测试"""
    
    # 请修改为您的实际文件路径
    dwg_file = r"D:\test.dwg"
    pdf_file = r"D:\test_output.pdf"
    
    if not os.path.exists(dwg_file):
        print(f"错误: DWG文件不存在 - {dwg_file}")
        print("请:")
        print("1. 创建一个测试DWG文件")
        print("2. 或修改脚本中的文件路径")
        return False
    
    try:
        print("开始测试AutoCAD导出功能...")
        print(f"输入文件: {dwg_file}")
        print(f"输出文件: {pdf_file}")
        
        # 初始化COM
        pythoncom.CoInitialize()
        
        # 连接到AutoCAD
        print("连接到AutoCAD...")
        acad = win32com.client.Dispatch("AutoCAD.Application")
        acad.Visible = False  # 后台运行
        
        # 打开DWG文件
        print("打开DWG文件...")
        doc = acad.Documents.Open(dwg_file)
        
        # 导出为PDF
        print("导出为PDF...")
        doc.Export(pdf_file, "PDF", "")
        
        # 关闭文档
        print("关闭文档...")
        doc.Close(SaveChanges=False)
        
        # 清理
        del doc
        del acad
        pythoncom.CoUninitialize()
        
        # 检查结果
        if os.path.exists(pdf_file):
            size = os.path.getsize(pdf_file)
            print(f"✓ 成功! PDF文件已生成")
            print(f"  文件路径: {pdf_file}")
            print(f"  文件大小: {size} 字节")
            return True
        else:
            print("✗ 失败! PDF文件未生成")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        try:
            pythoncom.CoUninitialize()
        except:
            pass
        return False

if __name__ == "__main__":
    print("AutoCAD DWG到PDF导出测试")
    print("=" * 40)
    simple_export_test()