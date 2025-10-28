"""
PDF图像差异比较脚本
将PDF转换为图像并进行差异检测
"""

import cv2
import numpy as np
from pdf2image import convert_from_path
from skimage.metrics import structural_similarity as ssim
import os

def pdf_to_image(pdf_path, dpi=300):
    """
    将PDF转换为图像
    
    Args:
        pdf_path (str): PDF文件路径
        dpi (int): 转换分辨率
        
    Returns:
        PIL.Image: 转换后的图像
    """
    images = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=1)
    return images[0] if images else None

def compare_images(img1, img2):
    """
    比较两个图像的差异
    
    Args:
        img1 (numpy.ndarray): 第一个图像
        img2 (numpy.ndarray): 第二个图像
        
    Returns:
        tuple: (差异图像, 相似度分数)
    """
    # 转换为灰度图
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # 计算结构相似性指数
    score, diff = ssim(gray1, gray2, full=True)
    diff = (diff * 255).astype("uint8")
    
    # 计算绝对差异
    abs_diff = cv2.absdiff(gray1, gray2)
    
    return abs_diff, score

def detect_changes(img1, img2, threshold=30):
    """
    检测图像中的变化区域
    
    Args:
        img1 (numpy.ndarray): 原始图像
        img2 (numpy.ndarray): 修改后的图像
        threshold (int): 差异阈值
        
    Returns:
        numpy.ndarray: 标记差异的图像
    """
    # 转换为灰度图
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # 计算差异
    diff = cv2.absdiff(gray1, gray2)
    
    # 应用阈值
    _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    
    # 形态学操作去除噪声
    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # 创建彩色标记图像
    result = img2.copy()
    
    # 找到轮廓
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 用不同颜色标记不同类型的差异
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 100:  # 过滤小区域
            # 获取边界框
            x, y, w, h = cv2.boundingRect(contour)
            
            # 根据像素值判断是新增还是删除
            # 这里简化处理，实际应用中可能需要更复杂的逻辑
            region1 = gray1[y:y+h, x:x+w]
            region2 = gray2[y:y+h, x:x+w]
            
            mean1 = np.mean(region1)
            mean2 = np.mean(region2)
            
            if mean2 > mean1:  # 新增（更亮）
                cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 2)  # 绿色
            elif mean2 < mean1:  # 删除（更暗）
                cv2.rectangle(result, (x, y), (x+w, y+h), (0, 0, 255), 2)  # 红色
            else:  # 修改
                cv2.rectangle(result, (x, y), (x+w, y+h), (255, 255, 0), 2)  # 黄色
    
    return result, contours

def generate_diff_report(img1_path, img2_path, output_path, dpi=300):
    """
    生成差异报告
    
    Args:
        img1_path (str): 原始PDF路径
        img2_path (str): 修改后PDF路径
        output_path (str): 输出差异图像路径
        dpi (int): 转换分辨率
    """
    # 转换PDF为图像
    print("正在转换PDF为图像...")
    img1_pil = pdf_to_image(img1_path, dpi)
    img2_pil = pdf_to_image(img2_path, dpi)
    
    if img1_pil is None or img2_pil is None:
        print("无法转换PDF文件")
        return
    
    # 转换为OpenCV格式
    img1 = cv2.cvtColor(np.array(img1_pil), cv2.COLOR_RGB2BGR)
    img2 = cv2.cvtColor(np.array(img2_pil), cv2.COLOR_RGB2BGR)
    
    # 比较图像
    print("正在比较图像...")
    diff_img, contours = detect_changes(img1, img2)
    
    # 保存结果
    cv2.imwrite(output_path, diff_img)
    
    # 计算统计信息
    change_count = len(contours)
    total_area = sum(cv2.contourArea(c) for c in contours)
    
    print(f"差异检测完成:")
    print(f"  - 发现 {change_count} 个变化区域")
    print(f"  - 总变化面积: {total_area:.2f} 像素")
    print(f"  - 差异图像已保存到: {output_path}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("用法: python pdf_diff.py <原始PDF> <修改后PDF> <输出差异图像>")
        sys.exit(1)
    
    original_pdf = sys.argv[1]
    modified_pdf = sys.argv[2]
    output_image = sys.argv[3]
    
    generate_diff_report(original_pdf, modified_pdf, output_image)