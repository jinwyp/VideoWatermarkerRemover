import threading
import queue
import os

import customtkinter


from watermark_remover import WatermarkRemover

# customtkinter.set_ctk_parent_class(tkinterDnD.Tk)

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


# tkinter GUI example with threading and queue
# https://gist.github.com/roosnic1/f1d1d17c663476af3279ab6ae3e80206

"""
The following code is for non-UI function.

"""

def remove_watermark(threshold, kernel_size, sourceFolder, outputFolder):
    remover = WatermarkRemover(threshold, kernel_size, sourceFolder, outputFolder)
    outputVideoPath = remover.remove_video_watermark()

    # print("Add outputVideoPath to the Queue")
    app.queue_UI.put(outputVideoPath, block=False, timeout=None)
    # queue_UI.put_nowait(outputVideoPath) # same as queue_UI.put(outputVideoPath, block=False, timeout=None)


# get each files in the folder
def get_files_in_folder(folder_path):
    
    temp_files = []

    for file in os.listdir(folder_path):
        temp_files.append(os.path.join(folder_path, file))
        # print(f"Source path: {folder_path} , file: {file}", os.path.join(folder_path, file))
    return temp_files

# check if the folder is exist
def check_folder_exist(folder_path):
    if os.path.exists(folder_path):
        return True
    else:
        return False


    


"""
The following code is for sub-thread function.

"""
def start_new_thread(targetSubThread, *args):
    newThreadTemp = threading.Thread(target=targetSubThread, args=args)
    newThreadTemp.start()
    return newThreadTemp



class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()


        self.title("Video Watermark Removal")
        self.minsize(900, 700)
        self.geometry("900x780")

        self.queue_UI = queue.Queue()



        """
        The following code is for layout components

        """

        self.grid_rowconfigure(0, weight=1)  # configure grid system
        self.grid_columnconfigure((0, 1), weight=1)
    
        frame1 = customtkinter.CTkFrame(master=self)
        frame1.grid(row=0, column=0, columnspan=4, pady=6, padx=6, sticky="nsew")
        self.frame1 = frame1


        self.label_threshold = customtkinter.CTkLabel(master=frame1, justify=customtkinter.LEFT, text="灰度阈值 threshold", font=("Arial", 16))
        self.label_threshold.grid(row=0, column=0, pady=6, padx=6, sticky="ens")

        self.entry_threshold = customtkinter.CTkEntry(master=frame1, placeholder_text="80")
        self.entry_threshold.grid(row=0, column=1, pady=6, padx=6, sticky="w")
        self.entry_threshold.insert(0, int(80))

        self.slider_threshold = customtkinter.CTkSlider(master=frame1, command=self.slider_threshold_callback, from_=0, to=255)
        self.slider_threshold.grid(row=0, column=2, columnspan=2, pady=6, padx=0, sticky="ew")
        self.slider_threshold.set(80)



        self.label_kernel_size = customtkinter.CTkLabel(master=frame1, justify=customtkinter.LEFT, text="边缘膨胀系数 kernel_size", font=("Arial", 16))
        self.label_kernel_size.grid(row=1, column=0, pady=6, padx=6, sticky="ens")

        self.entry_kernel_size = customtkinter.CTkEntry(master=frame1, placeholder_text="6")
        self.entry_kernel_size.grid(row=1, column=1, pady=6, padx=6, sticky="w")
        self.entry_kernel_size.insert(0, int(6))

        self.slider_kernel_size = customtkinter.CTkSlider(master=frame1, command=self.slider_kernel_size_callback, from_=0, to=50)
        self.slider_kernel_size.grid(row=1, column=2, columnspan=2, pady=6, padx=0, sticky="ew")
        self.slider_kernel_size.set(6)



        self.label_source_video = customtkinter.CTkLabel(master=frame1, justify=customtkinter.LEFT, text="源目录 Video source folder:", font=("Arial", 16))
        self.label_source_video.grid(row=2, column=0, pady=6, padx=6, sticky="ens")

        self.entry_source_video = customtkinter.CTkEntry(master=frame1, placeholder_text="")
        self.entry_source_video.grid(row=2, column=1, columnspan=2, pady=3, padx=1, sticky="ew")
        self.entry_source_video.insert(0, "video")

        self.button_source_video = customtkinter.CTkButton(master=frame1, command=self.button_video_source_callback, text="Select Folder")
        self.button_source_video.grid(row=2, column=3, pady=3, padx=6, sticky="w")



        self.label_output_video = customtkinter.CTkLabel(master=frame1, justify=customtkinter.LEFT, text="输出目录 Video output folder:", font=("Arial", 16))
        self.label_output_video.grid(row=3, column=0, pady=6, padx=6, sticky="ens")

        self.entry_output_video = customtkinter.CTkEntry(master=frame1, placeholder_text="")
        self.entry_output_video.grid(row=3, column=1, columnspan=2, pady=3, padx=1, sticky="ew")
        self.entry_output_video.insert(0, "output")

        self.button_output_video = customtkinter.CTkButton(master=frame1, command=self.button_video_output_callback, text="Select Folder")
        self.button_output_video.grid(row=3, column=3, pady=3, padx=6, sticky="w")




        self.button_start = customtkinter.CTkButton(master=frame1, command=self.button_start_callback, text="Remove Watermark")
        self.button_start.grid(row=4, column=1, pady=3, padx=10, sticky="ew")

        self.button_log = customtkinter.CTkButton(master=frame1, command=self.button_log_callback, text="Clear log")
        self.button_log.grid(row=4, column=2, pady=3, padx=10, sticky="ew")


        self.progressbar_1 = customtkinter.CTkProgressBar(master=frame1, orientation="horizontal", mode="determinate", determinate_speed=0.01, width=600)
        self.progressbar_1.grid(row=5, column=0, columnspan=4,  pady=10, padx=10)
        self.progressbar_1.set(0)  


        self.text_log = customtkinter.CTkTextbox(master=frame1, width=850, height=500)
        self.text_log.grid(row=6, column=0, columnspan=4, pady=10, padx=10)

        self.text_log.insert("0.0", "kernel_size 膨胀运算核尺寸, 范围为所有正整数, 用于处理水印或字幕边缘, 数值越大最后生成的蒙版覆盖面积边缘越大 \n")
        self.text_log.insert("0.0", "threshold 阈值分割灰度值，范围0~255, 大于该灰度值的水印将被处理, 数字越小被去掉的水印越多, 如果水印为亮白色该值数字尽量大一些,这样去掉的画面更少画质更好, 如果水印较暗该值就要小些才去掉水印,同时画面也会被去掉更多信息 \n")
        self.text_log.insert("0.0", "参数说明: \n")
        self.text_log.insert("0.0", " \n")

        self.update()


    """
    The following code is for UI event action callback 
    Example: button click, slider change, etc.

    """

    def button_start_callback(self):
        temp_threshold = int(self.entry_threshold.get())
        temp_kernel_size = int(self.entry_kernel_size.get())

        temp_sourceFolder = self.entry_source_video.get()
        temp_outputFolder = self.entry_output_video.get()

        if not temp_sourceFolder:
            temp_sourceFolder = "video"

        if not temp_outputFolder:
            temp_outputFolder = "output"
        
        if not check_folder_exist(temp_sourceFolder):
            self.text_log.insert("0.0", "Source folder not exist ! 源目录不存在 \n")
            return

        if not check_folder_exist(temp_outputFolder):
            self.text_log.insert("0.0", "Output folder not exist ! 输出目录不存在 \n")
            return
        
        filelist = get_files_in_folder(temp_sourceFolder)


        # check filelist is empty or not
        if not filelist:
            self.text_log.insert("0.0", "Source folder is empty ! 源目录为空 \n")
            return

        self.progressbar_1.set(0)
        self.progressbar_1.start() 

        self.button_start.configure(state="disabled")
        print("\n\n")
        # print(f"Start to remove watermark, threshold: {temp_threshold},  kernel_size: {temp_kernel_size}")
        self.text_log.insert("0.0", "Initiating watermark removal. Please wait... (threshold: "+str(temp_threshold)+", kernel_size: "+str(temp_kernel_size)+") \n")

        # Start a new thread to run the watermark removal process
        newThreadRemoveWatermark = start_new_thread(remove_watermark, temp_threshold, temp_kernel_size, temp_sourceFolder, temp_outputFolder)

        self.after(1000, self.updateUI_WatermarkRemovalFinished, newThreadRemoveWatermark)


    def button_log_callback(self):
        self.text_log.delete("0.0", customtkinter.END)


    def slider_threshold_callback(self, value):
        self.entry_threshold.delete(0, customtkinter.END)
        self.entry_threshold.insert(0, int(value))

    def slider_kernel_size_callback(self, value):
        self.entry_kernel_size.delete(0, customtkinter.END)
        self.entry_kernel_size.insert(0, int(value))

    def button_video_source_callback(self):
        sourceFolder = customtkinter.filedialog.askdirectory()
        self.entry_source_video.delete(0, customtkinter.END)
        self.entry_source_video.insert(0, sourceFolder)

    def button_video_output_callback(self):
        outputFolder = customtkinter.filedialog.askdirectory()
        self.entry_output_video.delete(0, customtkinter.END)
        self.entry_output_video.insert(0, outputFolder)



    """
    The following code is for after loop callback 
    Which is used to update UI after thread finished

    """

    def updateUI_WatermarkRemovalFinished(self, subThread):

        # if subThread.is_alive():
        #     print("subThread is still running. Thread Alive Status: ", subThread.is_alive())
        #     self.after(1000, self.updateUI_WatermarkRemovalFinished, subThread)
        # else:
        #     print("subThread is finished. Thread Alive Status: ", subThread.is_alive())
        #     self.button_start.configure(state="normal")
        #     self.progressbar_1.stop()
        #     self.progressbar_1.set(1)


        try:
            # print("Try to get output_path from queue")
            # print("===== SubThread is still running. Thread Alive Status: ", subThread.is_alive())
            # print("Quene 队列是否为空: {}, 队列还有 {} 个项目, ".format(self.queue_UI.empty(), self.queue_UI.qsize()))
            output_path = self.queue_UI.get(block=False)

        except queue.Empty:
            # print("Queue is empty, let's try again later")
            self.after(2000, self.updateUI_WatermarkRemovalFinished, subThread)
            return
        
        if output_path is not None:
            self.text_log.insert("0.0", " \n")
            self.text_log.insert("0.0", "Watermark removal successful! File: "+output_path+" \n")
            self.text_log.insert("0.0", " \n")

            self.button_start.configure(state="normal")
            self.progressbar_1.stop()
            self.progressbar_1.set(1)
            output_path = ""


if __name__ == "__main__":
    app = App()
    # app1 = customtkinter.CTk()
    print("Customtkinter APP Start!  Type: ", type(app))

    app.mainloop()



