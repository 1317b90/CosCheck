import os
import fitz  # PyMuPDF
from PIL import Image, ImageFile
from pathlib import Path
import numpy as np
Image.MAX_IMAGE_PIXELS = None  # 禁用最大像素限制
ImageFile.LOAD_TRUNCATED_IMAGES = True 


def pdf_to_img(pdf_path):
    # 打开 PDF 文件
    doc = fitz.open(pdf_path)
    
    # 创建一个空列表，用于保存每一页的图像
    images = []
    
    # 遍历 PDF 文件的每一页
    for page_num in range(doc.page_count):
        # 获取当前页
        page = doc.load_page(page_num)
        
        # 将当前页渲染成图像，降低dpi以减小文件大小
        pix = page.get_pixmap(dpi=300)  # 将dpi从300降至200
        
        # 将渲染后的图像转换为 Pillow Image 对象
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # 在添加到列表前对单页进行压缩
        if img.size[0] > 2000 or img.size[1] > 2000:
            # 如果图像太大，将其缩小到合理尺寸
            ratio = min(2000/img.size[0], 2000/img.size[1])
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        images.append(img)
    
    # 获取每个图像的宽度和高度
    width, height = images[0].size
    
    # 创建一个新的空白图像，大小为所有页面的高度总和
    total_height = height * len(images)
    combined_image = Image.new('RGB', (width, total_height))
    
    # 将每一页的图像按顺序粘贴到新的图像中
    y_offset = 0
    for img in images:
        combined_image.paste(img, (0, y_offset))
        y_offset += height
    # 获取pdf文件路径并替换后缀为png作为输出路径
    output_path = str(Path(pdf_path).with_suffix('.png'))
    # 保存合并后的图片
    combined_image.save(output_path, format='PNG')

    # 尝试删除图片白边
    try:
        remove_white_border(output_path)
    except:
        pass
    
    # 尝试压缩图片
    try:
        compress_image(output_path)
    except Exception as e:
        raise Exception("图片压缩失败：",str(e))

    return output_path

def remove_white_border(image_path):
    # 打开图像
    img = Image.open(image_path)
    
    # 转换为灰度图像
    gray_img = img.convert("L")
    
    # 转换为 numpy 数组
    img_array = np.array(gray_img)
    
    # 找到非白色部分的边界
    non_white_pixels = np.where(img_array < 255)  # 假设白色是255, 你可以调整这��阈值
    
    # 获取裁剪区域的边界
    top, bottom = non_white_pixels[0].min(), non_white_pixels[0].max()
    left, right = non_white_pixels[1].min(), non_white_pixels[1].max()
    
    # 裁剪图像
    cropped_img = img.crop((left, top, right, bottom))
    
    # 保存裁剪后的图像
    cropped_img.save(image_path, format='PNG')


# 压缩图片
def compress_image(image_path):
    """
    压缩图片，直到其小于 max_size。
    """
    max_size = 5 * 1024 * 1024  # 5MB
    img = Image.open(image_path)
    
    # 获取图片的当前大小
    img_size = os.path.getsize(image_path)
    
    # 如果图片小于5MB, 不做压缩
    if img_size <= max_size:
        return
        
    # 获取原始图片尺寸
    width, height = img.size
    
    # 首先尝试调整图片尺寸
    while img_size > max_size:
        # 每次将宽高缩小10%
        width = int(width * 0.9)
        height = int(height * 0.9)
        resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # 保存调整后的图片
        resized_img.save(image_path, optimize=True, quality=95)
        img_size = os.path.getsize(image_path)
        
        # 如果尺寸已经很小但文件仍然过大,则降低质量
        if width < 800 or height < 800:
            quality = 90
            while img_size > max_size and quality >= 60:
                resized_img.save(image_path, optimize=True, quality=quality)
                img_size = os.path.getsize(image_path)
                quality -= 5
            break

if __name__ == "__main__":
    pdf_to_img("./file/test.pdf")

