测试AutoCAD COM接口连接

import win32com.client
import pythoncom
import os

def test_autocad_connection():
    测试AutoCAD连接
    try:
        # 初始化COM
        pythoncom.CoInitialize()
        
        # 连接到AutoCAD
        print("正在连接AutoCAD...")
        acad = win32com.client.Dispatch("AutoCAD.Application")
        print(f"✓ 成功连接到AutoCAD {acad.Version}")
        print(f"  可见性: {acad.Visible}")
        
        # 清理
        del acad
        pythoncom.CoUninitialize()
        
        return True
        
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        try:
            pythoncom.CoUninitialize()
        except:
            pass
        return False

def test_dwg_export(dwg_path, pdf_path):
    测试DWG导出为PDF
    try:
        if not os.path.exists(dwg_path):
            print(f"✗ DWG文件不存在: {dwg_path}")
            return False
            
        # 初始化COM
        pythoncom.CoInitialize()
        
        # 连接到AutoCAD
        acad = win32com.client.Dispatch("AutoCAD.Application")
        acad.Visible = False  # 后台运行
        
        # 打开DWG文件
        print(f"正在打开DWG文件: {dwg_path}")
        doc = acad.Documents.Open(dwg_path)
        
        # 导出为PDF
        print(f"正在导出为PDF: {pdf_path}")
        doc.Export(pdf_path, "PDF", "")
        
        # 关闭文档
        doc.Close(SaveChanges=False)
        
        # 清理
        del doc
        del acad
        pythoncom.CoUninitialize()
        
        if os.path.exists(pdf_path):
            print(f"✓ 成功导出PDF: {pdf_path}")
            return True
        else:
            print("✗ PDF文件未生成")
            return False
            
    except Exception as e:
        print(f"✗ 导出失败: {e}")
        try:
            pythoncom.CoUninitialize()
        except:
            pass
        return False

if __name__ == "__main__":
    print("AutoCAD COM接口测试")
    print("=" * 30)
    
    # 测试1: 连接测试
    print("\n1. 测试AutoCAD连接:")
    if test_autocad_connection():
        print("AutoCAD连接测试通过")
    else:
        print("AutoCAD连接测试失败")
        exit(1)
    
    # 测试2: 导出测试（需要准备测试文件）
    print("\n2. 测试DWG导出:")
    # 请准备一个测试DWG文件
    test_dwg = r"D:\test.dwg"  # 请修改为实际的DWG文件路径
    test_pdf = r"D:\test_output.pdf"
    
    if os.path.exists(test_dwg):
        if test_dwg_export(test_dwg, test_pdf):
            print("DWG导出测试通过")
        else:
            print("DWG导出测试失败")
    else:
        print(f"提示: 请准备测试文件 {test_dwg} 以进行导出测试")