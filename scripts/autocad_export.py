"""
AutoCAD PDF导出脚本
通过COM接口调用AutoCAD执行批处理导出
"""

import os
import sys
import time
import win32com.client
import pythoncom
from pathlib import Path

def export_dwg_to_pdf_batch(source_dir, target_dir):
    """
    批量导出DWG文件为PDF
    
    Args:
        source_dir (str): 源DWG文件目录
        target_dir (str): 目标PDF文件目录
    """
    # 确保目标目录存在
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # 初始化COM
        pythoncom.CoInitialize()
        
        # 连接到AutoCAD
        acad = win32com.client.Dispatch("AutoCAD.Application")
        print("已连接到AutoCAD")
        
        # 获取文档对象
        doc = acad.ActiveDocument
        
        # 加载LISP脚本
        lisp_script = os.path.join(os.path.dirname(__file__), "BatchExportPDF.lsp")
        doc.SendCommand(f'(load "{lisp_script}") ')
        
        # 执行批处理导出命令
        # 注意：这里需要根据实际的LISP函数名调整
        doc.SendCommand("(BatchExportPDF) ")
        
        # 等待处理完成（可以根据文件数量调整等待时间）
        time.sleep(10)
        
        print("批处理导出完成")
        
    except Exception as e:
        print(f"导出过程中出现错误: {e}")
    finally:
        # 清理COM
        pythoncom.CoUninitialize()

def export_single_dwg_to_pdf(dwg_path, pdf_path):
    """
    导出单个DWG文件为PDF
    
    Args:
        dwg_path (str): DWG文件路径
        pdf_path (str): PDF文件路径
    """
    try:
        # 初始化COM
        pythoncom.CoInitialize()
        
        # 连接到AutoCAD
        acad = win32com.client.Dispatch("AutoCAD.Application")
        
        # 打开DWG文件
        doc = acad.Documents.Open(dwg_path)
        
        # 导出为PDF
        doc.ExportPdf(pdf_path)
        
        # 关闭文档
        doc.Close(False)
        
        print(f"已导出: {dwg_path} -> {pdf_path}")
        
    except Exception as e:
        print(f"导出文件 {dwg_path} 时出现错误: {e}")
    finally:
        # 清理COM
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python autocad_export.py <源目录> <目标目录>")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    target_dir = sys.argv[2]
    
    export_dwg_to_pdf_batch(source_dir, target_dir)