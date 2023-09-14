import os
import sys
import argparse

import cv2
import numpy
from moviepy import editor

VIDEO_SOURCE_PATH = 'video'
VIDEO_OUTPUT_PATH = 'output'
VIDEO_OUTPUT_PATH_2 = os.path.join(os.path.pardir, 'video_bilibili')
VIDEO_OUTPUT_TEMP_VIDEO = 'temp.mp4'


class WatermarkRemover():
  
  def __init__(self, threshold: int, kernel_size: int, source_path: str, output_path: str):
    self.threshold = threshold #阈值分割所用阈值
    self.kernel_size = kernel_size #膨胀运算核尺寸
    self.source_path = source_path #视频源文件路径
    self.output_path = output_path #输出文件路径


  def select_roi(self, img: numpy.ndarray, hint: str) -> list:
    '''
    框选水印或字幕位置，SPACE或ENTER键退出
    :param img: 显示图片
    :return: 框选区域坐标
    '''
    COFF = 0.7
    w, h = int(COFF * img.shape[1]), int(COFF * img.shape[0])
    resize_img = cv2.resize(img, (w, h))
    roi = cv2.selectROI(hint, resize_img, False, False)
    cv2.destroyAllWindows()
    watermark_roi = [int(roi[0] / COFF), int(roi[1] / COFF), int(roi[2] / COFF), int(roi[3] / COFF)]
    return watermark_roi

  def dilate_mask(self, mask: numpy.ndarray) -> numpy.ndarray:
    
    '''
    对蒙版进行膨胀运算
    :param mask: 蒙版图片
    :return: 膨胀处理后蒙版
    '''
    kernel = numpy.ones((self.kernel_size, self.kernel_size), numpy.uint8)
    mask = cv2.dilate(mask, kernel)
    return mask

  def generate_single_mask(self, img: numpy.ndarray, roi: list, threshold: int) -> numpy.ndarray:
    '''
    通过手动选择的ROI区域生成单帧图像的水印蒙版
    :param img: 单帧图像
    :param roi: 手动选择区域坐标
    :param threshold: 二值化阈值
    :return: 水印蒙版
    '''
    #区域无效，程序退出
    if len(roi) != 4:
      print('NULL ROI!')
      sys.exit()
    
    
    #复制单帧灰度图像ROI内像素点
    roi_img = numpy.zeros((img.shape[0], img.shape[1]), numpy.uint8)
    start_x, end_x = int(roi[1]), int(roi[1] + roi[3])
    start_y, end_y = int(roi[0]), int(roi[0] + roi[2])
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    roi_img[start_x:end_x, start_y:end_y] = gray[start_x:end_x, start_y:end_y]

    #阈值分割
    _, mask = cv2.threshold(roi_img, threshold, 255, cv2.THRESH_BINARY)
    print("=== Step 2: finish to generate_single_mask of frame ")
    return mask
  

  def generate_watermark_mask(self, video_path: str) -> numpy.ndarray:
    '''
    截取视频中多帧图像生成多张水印蒙版，通过逻辑与计算生成最终水印蒙版
    :param video_path: 视频文件路径
    :return: 水印蒙版
    '''
    video = cv2.VideoCapture(video_path)
    success, frame = video.read()
    print("=== Please select the region of the watermark. Then press SPACE or ENTER to continue ")
    print("=== 请选择要去掉的水印的区域 然后按空格或回车继续 \n")
    roi = self.select_roi(frame, 'Select watermark ROI')
    generateAllFrameMask = numpy.ones((frame.shape[0], frame.shape[1]), numpy.uint8)
    generateAllFrameMask.fill(255)

    step = video.get(cv2.CAP_PROP_FRAME_COUNT) // 5
    index = 0
    print(f"=== Step 1: start  generate_watermark_mask. Total frame: {video.get(cv2.CAP_PROP_FRAME_COUNT)}, Step: {step}, CAP_PROP_FRAME_COUNT: {cv2.CAP_PROP_FRAME_COUNT} " )

    while success:
      if index % step == 0:
        generateAllFrameMask = cv2.bitwise_and(generateAllFrameMask, self.generate_single_mask(frame, roi, self.threshold))
      success, frame = video.read()
      index += 1
    video.release()
    print("=== Step 1: finish to generate_watermark_mask ")

    return self.dilate_mask(generateAllFrameMask)

  def generate_subtitle_mask(self, frame: numpy.ndarray, roi: list) -> numpy.ndarray:
    '''
    通过手动选择ROI区域生成单帧图像字幕蒙版
    :param frame: 单帧图像
    :param roi: 手动选择区域坐标
    :return: 字幕蒙版
    '''
    mask = self.generate_single_mask(frame, [0, roi[1], frame.shape[1], roi[3]], self.threshold) #仅使用ROI横坐标区域
    return self.dilate_mask(mask)

  def inpaint_image(self, img: numpy.ndarray, mask: numpy.ndarray) -> numpy.ndarray:
    '''
    修复图像
    :param img: 单帧图像
    :parma mask: 蒙版
    :return: 修复后图像
    '''

    telea = cv2.inpaint(img, mask, 1, cv2.INPAINT_TELEA)
    return telea
  
  def merge_audio(self, input_path: str, merge_output_path: str, temp_path: str):
    '''
    合并音频与处理后视频
    :param input_path: 原视频文件路径
    :param merge_output_path: 封装音视频后文件路径
    :param temp_path: 无声视频文件路径 
    '''
    with editor.VideoFileClip(input_path) as video:
      audio = video.audio
      with editor.VideoFileClip(temp_path) as opencv_video:
        clip = opencv_video.set_audio(audio)
        clip.to_videofile(merge_output_path)

  def remove_video_watermark(self):
    '''
    去除视频水印
    '''
    if not os.path.exists(self.output_path):
      os.makedirs(self.output_path)

    filenames = []

    for singleFile in os.listdir(self.source_path):
        filenames.append(os.path.join(self.source_path, singleFile))
        print(f"Source file path: {self.source_path}, filename: {singleFile},  full path: {os.path.join(self.source_path, singleFile)} \n")

    mask = None

    for i, singleSourceVideoFileName in enumerate(filenames):

      #生成水印蒙版
      mask = self.generate_watermark_mask(singleSourceVideoFileName)
      
      #创建待写入文件对象
      video = cv2.VideoCapture(singleSourceVideoFileName)
      fps = video.get(cv2.CAP_PROP_FPS)
      size = (int(video.get(cv2.CAP_PROP_FRAME_WIDTH)), int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)))
      video_writer = cv2.VideoWriter(VIDEO_OUTPUT_TEMP_VIDEO, cv2.VideoWriter_fourcc(*'mp4v'), fps, size)
    
      print(f"=== Step 3: Start to inpaint all frame. FPS: {fps}. Please wait... " )

      #逐帧处理图像
      success, frame = video.read()
      while success:
        frame = self.inpaint_image(frame, mask)
        video_writer.write(frame)
        success, frame = video.read()

      print("=== Step 3: finish to inpaint all frame")
      video.release()
      video_writer.release()

      #封装视频
      (_, filename) = os.path.split(singleSourceVideoFileName)
      output_path = os.path.join(self.output_path, filename.split('.')[0] + '_no_watermark.mp4')#输出文件路径
      self.merge_audio(singleSourceVideoFileName, output_path, VIDEO_OUTPUT_TEMP_VIDEO)

      print(" \n")

    if os.path.exists(VIDEO_OUTPUT_TEMP_VIDEO):
      os.remove(VIDEO_OUTPUT_TEMP_VIDEO)

    return output_path
  
  

  def remove_video_subtitle(self):
    '''
    去除视频字幕
    '''
    if not os.path.exists(self.output_path):
      os.makedirs(self.output_path)


    filenames = [os.path.join(self.source_path, i) for i in os.listdir(self.source_path)]
    roi = []

    for i, name in enumerate(filenames):
      #创建待写入文件对象
      video = cv2.VideoCapture(name)
      fps = video.get(cv2.CAP_PROP_FPS)
      size = (int(video.get(cv2.CAP_PROP_FRAME_WIDTH)), int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)))
      video_writer = cv2.VideoWriter(VIDEO_OUTPUT_TEMP_VIDEO, cv2.VideoWriter_fourcc(*'mp4v'), fps, size)
    
      #逐帧处理图像
      success, frame = video.read()
      if i == 0:
        roi = self.select_roi(frame, 'select subtitle ROI')

      while success:
        mask = self.generate_subtitle_mask(frame, roi)
        frame = self.inpaint_image(frame, mask)
        video_writer.write(frame)
        success, frame = video.read()

      video.release()
      video_writer.release()

      #封装视频
      (_, filename) = os.path.split(name)
      output_path = os.path.join(self.output_path, filename.split('.')[0] + '_no_sub.mp4')#输出文件路径
      self.merge_audio(name, output_path, VIDEO_OUTPUT_TEMP_VIDEO)

    if os.path.exists(VIDEO_OUTPUT_TEMP_VIDEO):
      os.remove(VIDEO_OUTPUT_TEMP_VIDEO)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--threshold', type=int, default=80, help='Threshold value for watermark removal')
  parser.add_argument('--kernel_size', type=int, default=5, help='Kernel size for watermark removal')
  parser.add_argument('--subtitle', action='count', default=0, help='Subtitle watermark removal')

  parser.add_argument('--output', action='count', default=0, help='Output file path')
  
  args = parser.parse_args()
  print("====================")
  print(f"APP start! arguments: [subtitle: {args.subtitle} , threshold: {args.threshold}, output: {args.output} ] ")
  print("====================")

  if args.output > 0:
    VIDEO_OUTPUT_PATH = VIDEO_OUTPUT_PATH_2
    
  if args.subtitle > 0:
    remover = WatermarkRemover(threshold=80, kernel_size=10, source_path=VIDEO_SOURCE_PATH, output_path=VIDEO_OUTPUT_PATH)
    remover.remove_video_subtitle()
  else:
    remover = WatermarkRemover(threshold=80, kernel_size=6, source_path=VIDEO_SOURCE_PATH, output_path=VIDEO_OUTPUT_PATH)
    remover.remove_video_watermark()



  #去除视频水印
  # remover = WatermarkRemover(threshold=80, kernel_size=5)
  # remover.remove_video_watermark()

  #去除视频字幕
  # remover = WatermarkRemover(threshold=80, kernel_size=10)
  # remover.remove_video_subtitle()

