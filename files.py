import tkinter as tk
from tkinter import filedialog, messagebox
import os
import fitz  # PyMuPDF
from PIL import Image, ImageTk

class FileCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文件检查器与编辑器")
        self.root.state('zoomed')

        # 初始化变量
        self.pages = []
        self.txt_content = ""
        self.image_refs = []
        self.txt_file_path = ""
        self.pdf_files = []
        self.txt_files = {}
        self.current_index = 0
        self.scale_factor = 1.0
        self.unsaved_changes = False

        # 主界面布局
        self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=8)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # PDF显示区域（左侧）
        self.left_frame = tk.Frame(self.main_paned, bg='white')
        self.h_scroll = tk.Scrollbar(self.left_frame, orient=tk.HORIZONTAL)
        self.v_scroll = tk.Scrollbar(self.left_frame, orient=tk.VERTICAL)
        self.pdf_canvas = tk.Canvas(
            self.left_frame,
            bg="white",
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set
        )
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.pdf_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.v_scroll.config(command=self.pdf_canvas.yview)
        self.h_scroll.config(command=self.pdf_canvas.xview)

        # 文本编辑区域（右侧）
        self.right_frame = tk.Frame(self.main_paned)

        self.txt_scroll = tk.Scrollbar(self.right_frame, orient=tk.VERTICAL)
        self.txt_text = tk.Text(
            self.right_frame,
            wrap=tk.WORD,
            yscrollcommand=self.txt_scroll.set,
            height=20,
            font=('宋体', 16)
        )
        self.txt_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=55)

        self.main_paned.add(self.left_frame, minsize=800)
        self.main_paned.add(self.right_frame, minsize=400)

        # 底部按钮区域
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # 加载按钮
        self.load_button = tk.Button(self.button_frame, text="   打开文件夹   ", command=self.load_files)
        self.load_button.pack(side=tk.LEFT, padx=50, pady=2)

        self.previous_button = tk.Button(self.button_frame, text="    上一个    ", command=self.previous_file)
        self.previous_button.place(x=700, y=2)

        self.next_button = tk.Button(self.button_frame, text="    下一个    ", command=self.next_file)
        self.next_button.place(x=850, y=2)

        # 绑定滚轮缩放事件
        self.pdf_canvas.bind("<MouseWheel>", self.zoom)
        self.txt_text.bind("<<Modified>>", self.auto_save_on_modify)

        # 信息显示区域
        self.pdf_info_frame = tk.Frame(self.root, bg='lightgray')
        self.pdf_info_frame.place(x=0, y=0, relwidth=1.0)

        self.pdf_path_label = tk.Label(self.pdf_info_frame, text="PDF路径：", bg='lightgray', anchor='w')
        self.pdf_path_label.pack(fill=tk.X, padx=5, pady=2)

        self.pdf_name_label = tk.Label(self.pdf_info_frame, text="PDF文件名：", bg='lightgray', anchor='w')
        self.pdf_name_label.pack(fill=tk.X, padx=5, pady=2)

        self.txt_info_frame = tk.Frame(self.root, bg='lightgray')
        self.txt_info_frame.place(relx=1.0, y=0, anchor='ne')

        self.txt_path_label = tk.Label(self.txt_info_frame, text="TXT路径：", bg='lightgray', anchor='w')
        self.txt_path_label.pack(fill=tk.X, padx=5, pady=2)

        self.txt_name_label = tk.Label(self.txt_info_frame, text="TXT文件名：", bg='lightgray', anchor='w')
        self.txt_name_label.pack(fill=tk.X, padx=5, pady=2)

    def auto_save_on_modify(self, event=None):
        """当文本框内容修改时，自动保存"""
        if self.txt_text.edit_modified():
            self.auto_save()

    def set_unsaved_changes(self, event=None):
        """当文本框内容修改时，设置未保存更改的标记"""
        self.unsaved_changes = True

    def previous_file(self):
        self.auto_save()
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_file()
        else:
            messagebox.showinfo("提示", "已经是第一个文件了！")

    def next_file(self):
        self.auto_save()
        if self.current_index < len(self.pdf_files) - 1:
            self.current_index += 1
            self.load_current_file()
        else:
            messagebox.showinfo("提示", "已经是最后一个文件了！")

    def load_files(self):
        folder_path = filedialog.askdirectory(title="选择文件夹")
        if not folder_path:
            return

        self.pdf_files = []
        self.txt_files = {}

        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
        for pdf_file in pdf_files:
            base_name = os.path.splitext(pdf_file)[0]
            txt_matches = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.lower() == f"{base_name}_main_content.txt"
            ]
            if txt_matches:
                self.pdf_files.append(os.path.join(folder_path, pdf_file))
                self.txt_files[os.path.join(folder_path, pdf_file)] = txt_matches

        if not self.pdf_files:
            messagebox.showerror("错误", "未找到有效的PDF-TXT文件对！")
            return

        self.current_index = 0
        self.load_current_file()

    def load_current_file(self):
        pdf_path = self.pdf_files[self.current_index]
        pdf_name = os.path.basename(pdf_path)
        self.pdf_path_label.config(text=f"PDF路径：{pdf_path}")
        self.pdf_name_label.config(text=f"PDF文件名：{pdf_name}")

        try:
            doc = fitz.open(pdf_path)
            self.pages = []
            for page in doc:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                self.pages.append(img)
            self.show_image()
        except Exception as e:
            messagebox.showerror("错误", f"PDF加载失败: {e}")
            return

        txt_files = self.txt_files[pdf_path]
        if txt_files:
            self.load_selected_txt(0)

    def show_image(self):
        """重新绘制PDF图像，更新缩放后的图片"""
        self.pdf_canvas.delete("all")  # 清除原有图像
        self.image_refs = []  # 清空图片引用
        y_offset = 100  # 初始y轴偏移量
        max_width = 0  # 记录最大宽度

        for page_img in self.pages:
            # 按照缩放比例计算新的宽度和高度
            scaled_width = int(page_img.width * self.scale_factor)
            scaled_height = int(page_img.height * self.scale_factor)
            max_width = max(max_width, scaled_width)

            img = page_img.resize((scaled_width, scaled_height), Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            self.image_refs.append(img_tk)  # 保存图像引用，避免被垃圾回收

            # 在Canvas上绘制缩放后的图像
            self.pdf_canvas.create_image(0, y_offset, anchor=tk.NW, image=img_tk)
            y_offset += scaled_height  # 更新y偏移量

        # 更新Canvas的滚动区域
        self.pdf_canvas.config(scrollregion=(0, 0, max_width, y_offset))

    def zoom(self, event):
        """通过鼠标滚轮实现缩放功能"""
        # 根据滚轮方向调整缩放比例
        scale = 1.1 if event.delta > 0 else 0.9
        self.scale_factor = max(0.1, min(5.0, self.scale_factor * scale))
        self.show_image()

    def load_selected_txt(self, index):
        self.txt_file_path = self.txt_files[self.pdf_files[self.current_index]][index]
        self.txt_path_label.config(text=f"TXT路径：{self.txt_file_path}")
        self.txt_name_label.config(text=f"TXT文件名：{os.path.basename(self.txt_file_path)}")

        try:
            with open(self.txt_file_path, "r", encoding="utf-8") as f:
                self.txt_text.delete(1.0, tk.END)
                self.txt_text.insert(tk.END, f.read())
                self.txt_text.edit_modified(False)
        except Exception as e:
            messagebox.showerror("错误", f"加载TXT文件失败: {e}")

    def auto_save(self):
        """自动保存文本框内容"""
        if self.txt_text.edit_modified():
            with open(self.txt_file_path, "w", encoding="utf-8") as f:
                f.write(self.txt_text.get(1.0, tk.END).strip())
            self.txt_text.edit_modified(False)
            self.unsaved_changes = False

    def save_file(self):
        """保存文件的操作"""
        if self.unsaved_changes:
            with open(self.txt_file_path, "w", encoding="utf-8") as f:
                f.write(self.txt_text.get(1.0, tk.END).strip())
            self.txt_text.edit_modified(False)
            self.unsaved_changes = False
            messagebox.showinfo("保存", "文件已保存！")
        else:
            messagebox.showinfo("保存", "没有修改内容，不需要保存。")

    def run(self):
        """启动应用程序"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_close(self):
        """窗口关闭时的操作，检查是否保存了未保存的更改"""
        if self.unsaved_changes:
            if messagebox.askyesno("提示", "是否保存未保存的更改?"):
                self.save_file()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FileCheckerApp(root)
    app.run()