PDF差异比较测试脚本
用于测试PDF图像差异比较功能

import sys
import os
import cv2
import numpy as np
from pdf2image import convert_from_path

# 将脚本目录添加到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_diff import pdf_to_image, compare_images, detect_changes, generate_diff_report

def create_test_pdfs():
    """
    创建测试PDF文件（用于演示）
    """
    print("创建测试PDF文件...")
    
    # 这里可以创建一些简单的测试PDF
    # 在实际使用中，您将使用真实的PDF文件

def test_image_conversion():
    """
    测试PDF到图像的转换
    """
    print("测试PDF到图像转换...")
    
    # 创建一个简单的测试图像
    test_img = np.zeros((500, 500, 3), dtype=np.uint8)
    cv2.rectangle(test_img, (50, 50), (200, 200), (255, 255, 255), -1)
    cv2.putText(test_img, "Test PDF 1", (60, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # 保存为PNG（模拟PDF转换结果）
    cv2.imwrite("test1.png", test_img)
    
    # 创建第二个测试图像（有差异）
    test_img2 = test_img.copy()
    cv2.rectangle(test_img2, (300, 300), (450, 450), (0, 255, 0), -1)  # 新增矩形
    cv2.rectangle(test_img2, (50, 50), (200, 200), (0, 0, 0), -1)  # 删除原有矩形
    cv2.putText(test_img2, "Test PDF 2", (60, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # 保存为PNG（模拟PDF转换结果）
    cv2.imwrite("test2.png", test_img2)
    
    print("测试图像已创建")

def test_diff_detection():
    """
    测试差异检测功能
    """
    print("测试差异检测功能...")
    
    # 读取测试图像
    img1 = cv2.imread("test1.png")
    img2 = cv2.imread("test2.png")
    
    if img1 is None or img2 is None:
        print("无法读取测试图像")
        return
    
    # 检测变化
    diff_img, contours = detect_changes(img1, img2)
    
    # 保存差异图像
    cv2.imwrite("diff_result.png", diff_img)
    
    print(f"差异检测完成，找到 {len(contours)} 个变化区域")
    print("差异图像已保存为 diff_result.png")

def main():
    """
    主函数
    """
    print("PDF差异比较测试")
    print("=" * 30)
    
    # 创建测试图像
    test_image_conversion()
    
    # 测试差异检测
    test_diff_detection()
    
    print("
测试完成！")
    print("请查看生成的文件：")
    print("- test1.png (原始图像)")
    print("- test2.png (修改后图像)")
    print("- diff_result.png (差异标记图像)")

if __name__ == "__main__":
    main()