import tkinter as tk
from tkinter import ttk, colorchooser
import json
import os

class DisplaySettings:
    def __init__(self, root, preview_text, toc_listbox=None, apply_callback=None):
        """
        显示设置类，用于管理预览文本的显示参数
        
        参数:
            root: 主窗口
            preview_text: 预览文本控件
            toc_listbox: 目录列表框控件（可选）
            apply_callback: 应用设置后的回调函数（可选）
        """
        self.root = root
        self.preview_text = preview_text
        self.toc_listbox = toc_listbox
        self.apply_callback = apply_callback
        
        # 默认设置
        self.default_settings = {
            "font_family": "Microsoft YaHei",
            "font_size": 12,
            "font_color": "#000000",  # 添加字体颜色设置
            "line_spacing": 1.0,
            "background_color": "#FAFAFA",
            "first_line_indent": False,
            "indent_chars": 2,
            "bold_chapter_title": True,
            "center_chapter_title": False,  # 添加章节标题居中设置
            "page_margin": 10  # 添加页边距设置
        }
        
        # 当前设置
        self.current_settings = self.default_settings.copy()
        
        # 尝试加载保存的设置
        self.load_settings()
    
    def show_settings_dialog(self):
        """
        显示设置对话框
        """
        # 创建设置对话框
        settings_window = tk.Toplevel(self.root)
        settings_window.title("显示设置")
        settings_window.geometry("450x800")
        settings_window.transient(self.root)  # 设置为主窗口的子窗口
        settings_window.grab_set()  # 模态对话框
        
        # 创建主框架
        main_frame = ttk.Frame(settings_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 字体设置
        font_frame = ttk.LabelFrame(main_frame, text="字体设置", padding="10")
        font_frame.pack(fill=tk.X, pady=5)
        
        # 字体选择
        ttk.Label(font_frame, text="字体:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 获取系统可用字体
        available_fonts = ["SimSun", "Microsoft YaHei", "KaiTi", "FangSong", "SimHei", "Arial", "Times New Roman"]
        
        font_var = tk.StringVar(value=self.current_settings["font_family"])
        font_combo = ttk.Combobox(font_frame, textvariable=font_var, values=available_fonts, width=20)
        font_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 字体大小
        ttk.Label(font_frame, text="字体大小:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        size_var = tk.IntVar(value=self.current_settings["font_size"])
        size_spinbox = ttk.Spinbox(font_frame, from_=8, to=24, textvariable=size_var, width=5)
        size_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 行距设置
        ttk.Label(font_frame, text="行距:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        line_spacing_var = tk.DoubleVar(value=self.current_settings["line_spacing"])
        line_spacing_spinbox = ttk.Spinbox(font_frame, from_=1.0, to=3.0, increment=0.1, textvariable=line_spacing_var, width=5)
        line_spacing_spinbox.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 颜色设置
        color_frame = ttk.LabelFrame(main_frame, text="颜色设置", padding="10")
        color_frame.pack(fill=tk.X, pady=5)
        
        # 背景颜色设置
        ttk.Label(color_frame, text="背景颜色:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 创建背景颜色显示框和颜色代码输入框
        bg_color_display_frame = ttk.Frame(color_frame)
        bg_color_display_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        bg_color_var = tk.StringVar(value=self.current_settings["background_color"])
        
        # 背景颜色显示框
        bg_color_canvas = tk.Canvas(bg_color_display_frame, width=20, height=20, bg=bg_color_var.get())
        bg_color_canvas.pack(side=tk.LEFT, padx=(0, 5))
        
        # 背景颜色代码输入框
        bg_color_entry = ttk.Entry(bg_color_display_frame, textvariable=bg_color_var, width=10)
        bg_color_entry.pack(side=tk.LEFT)
        
        # 选择背景颜色按钮
        def choose_bg_color():
            color = colorchooser.askcolor(initialcolor=bg_color_var.get())
            if color[1]:
                bg_color_var.set(color[1])
                bg_color_canvas.config(bg=color[1])
        
        bg_color_btn = ttk.Button(bg_color_display_frame, text="选择", command=choose_bg_color)
        bg_color_btn.pack(side=tk.LEFT, padx=5)
        
        # 字体颜色设置
        ttk.Label(color_frame, text="字体颜色:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 创建字体颜色显示框和颜色代码输入框
        font_color_display_frame = ttk.Frame(color_frame)
        font_color_display_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        font_color_var = tk.StringVar(value=self.current_settings["font_color"])
        
        # 字体颜色显示框
        font_color_canvas = tk.Canvas(font_color_display_frame, width=20, height=20, bg=font_color_var.get())
        font_color_canvas.pack(side=tk.LEFT, padx=(0, 5))
        
        # 字体颜色代码输入框
        font_color_entry = ttk.Entry(font_color_display_frame, textvariable=font_color_var, width=10)
        font_color_entry.pack(side=tk.LEFT)
        
        # 选择字体颜色按钮
        def choose_font_color():
            color = colorchooser.askcolor(initialcolor=font_color_var.get())
            if color[1]:
                font_color_var.set(color[1])
                font_color_canvas.config(bg=color[1])
        
        font_color_btn = ttk.Button(font_color_display_frame, text="选择", command=choose_font_color)
        font_color_btn.pack(side=tk.LEFT, padx=5)
        
        # 段落设置
        paragraph_frame = ttk.LabelFrame(main_frame, text="段落设置", padding="10")
        paragraph_frame.pack(fill=tk.X, pady=5)
        
        # 页边距设置
        ttk.Label(paragraph_frame, text="页边距:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        page_margin_var = tk.IntVar(value=self.current_settings["page_margin"])
        page_margin_spinbox = ttk.Spinbox(paragraph_frame, from_=0, to=50, textvariable=page_margin_var, width=5)
        page_margin_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 目录设置
        toc_frame = ttk.LabelFrame(main_frame, text="目录设置", padding="10")
        toc_frame.pack(fill=tk.X, pady=5)
        
        # 目录标题加粗选项
        bold_title_var = tk.BooleanVar(value=self.current_settings["bold_chapter_title"])
        bold_title_check = ttk.Checkbutton(toc_frame, text="目录标题加粗显示", variable=bold_title_var)
        bold_title_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # 目录标题居中选项
        center_title_var = tk.BooleanVar(value=self.current_settings["center_chapter_title"])
        center_title_check = ttk.Checkbutton(toc_frame, text="目录标题居中显示", variable=center_title_var)
        center_title_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # 预览效果
        preview_frame = ttk.LabelFrame(main_frame, text="预览效果", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建预览文本框
        preview_text = tk.Text(preview_frame, wrap=tk.WORD, width=40, height=5)
        preview_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加示例文本
        preview_text.insert(tk.END, "第一章 示例章节标题\n\n这是一个示例段落，用于预览显示效果。您可以在这里看到字体、行距和背景颜色等设置的效果。")
        
        # 更新预览效果的函数
        def update_preview():
            # 更新字体和大小
            font_family = font_var.get()
            font_size = size_var.get()
            preview_text.config(font=(font_family, font_size))
            
            # 更新背景颜色
            preview_text.config(bg=bg_color_var.get())
            
            # 更新字体颜色
            preview_text.config(fg=font_color_var.get())
            
            # 更新行距 - 修复行距设置，使用spacing2控制行间距
            line_spacing = line_spacing_var.get()
            # 安全获取字体大小
            try:
                font = preview_text.cget("font")
                if isinstance(font, str):
                    font_parts = font.split()
                    font_size = int(font_parts[1]) if len(font_parts) > 1 else font_size
                else:
                    # 如果不是字符串，使用当前设置的字体大小
                    font_size = font_size
            except:
                # 出错时使用当前设置的字体大小
                font_size = font_size
                
            # spacing2控制段落间距，spacing1控制行前间距
            preview_text.config(spacing1=0, spacing2=int(line_spacing * font_size), spacing3=0)
            
            # 清除所有标签
            preview_text.tag_remove("indent", "1.0", tk.END)
            preview_text.tag_remove("chapter_title", "1.0", tk.END)
            preview_text.tag_remove("center", "1.0", tk.END)
            
             # 处理章节标题加粗和居中
            if bold_title_var.get() or center_title_var.get():
                # 查找章节标题（第一行）
                title_end = preview_text.index("1.0 lineend")
                
                # 配置章节标题标签
                font_style = "bold" if bold_title_var.get() else ""
                preview_text.tag_configure("chapter_title", font=(font_family, font_size, font_style))
                preview_text.tag_add("chapter_title", "1.0", title_end)
                
                # 处理居中显示
                if center_title_var.get():
                    preview_text.tag_configure("center", justify="center")
                    preview_text.tag_add("center", "1.0", title_end)
        
        # 初始更新预览
        update_preview()
        
        # 绑定更改事件
        font_combo.bind("<<ComboboxSelected>>", lambda e: update_preview())
        size_spinbox.bind("<KeyRelease>", lambda e: update_preview())
        line_spacing_spinbox.bind("<KeyRelease>", lambda e: update_preview())
        bg_color_var.trace_add("write", lambda *args: update_preview())
        font_color_var.trace_add("write", lambda *args: update_preview())
        bold_title_var.trace_add("write", lambda *args: update_preview())
        center_title_var.trace_add("write", lambda *args: update_preview())
        
        # 添加按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10, side=tk.BOTTOM)
        
        # 应用设置函数
        def apply_settings():
            # 收集设置
            self.current_settings = {
                "font_family": font_var.get(),
                "font_size": size_var.get(),
                "font_color": font_color_var.get(),
                "line_spacing": line_spacing_var.get(),
                "background_color": bg_color_var.get(),
                "bold_chapter_title": bold_title_var.get(),
                "center_chapter_title": center_title_var.get(),
                "page_margin": page_margin_var.get()
            }
            
            # 保存设置
            self.save_settings()
            
            # 应用设置到预览文本
            self.apply_settings_to_preview()
            
            # 如果有回调函数，调用它
            if self.apply_callback:
                self.apply_callback()
            
            # 关闭对话框
            settings_window.destroy()
        
        # 重置为默认设置函数
        def reset_to_default():
            font_var.set(self.default_settings["font_family"])
            size_var.set(self.default_settings["font_size"])
            font_color_var.set(self.default_settings["font_color"])
            line_spacing_var.set(self.default_settings["line_spacing"])
            bg_color_var.set(self.default_settings["background_color"])
            bg_color_canvas.config(bg=self.default_settings["background_color"])
            font_color_canvas.config(bg=self.default_settings["font_color"])
            indent_var.set(self.default_settings["first_line_indent"])
            indent_chars_var.set(self.default_settings["indent_chars"])
            bold_title_var.set(self.default_settings["bold_chapter_title"])
            center_title_var.set(self.default_settings["center_chapter_title"])
            update_preview()
        
        # 添加按钮
        apply_btn = ttk.Button(button_frame, text="应用", command=apply_settings)
        apply_btn.pack(side=tk.RIGHT, padx=5)
        
        cancel_btn = ttk.Button(button_frame, text="取消", command=settings_window.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        reset_btn = ttk.Button(button_frame, text="恢复默认", command=reset_to_default)
        reset_btn.pack(side=tk.LEFT, padx=5)
    
    def apply_settings_to_preview(self):
        """
        将当前设置应用到预览文本
        """
        # 清除所有标签
        self.preview_text.tag_remove("indent", "1.0", tk.END)
        self.preview_text.tag_remove("chapter_title", "1.0", tk.END)
        self.preview_text.tag_remove("center", "1.0", tk.END)
        
        # 应用字体和大小
        self.preview_text.config(font=(self.current_settings["font_family"], self.current_settings["font_size"]))
        
        # 应用背景颜色
        self.preview_text.config(bg=self.current_settings["background_color"])
        
        # 应用字体颜色
        self.preview_text.config(fg=self.current_settings["font_color"])
        
        # 应用行距 - 优化行距设置
        font_size = self.current_settings["font_size"]
        # 计算实际行间距像素值 = 字体大小 * (行距系数 - 1)
        actual_spacing = int((self.current_settings["line_spacing"] - 1) * font_size)
        # spacing2控制行间距
        self.preview_text.config(spacing1=0, spacing2=actual_spacing, spacing3=0)
        
               
        # 处理章节标题
        if self.current_settings["bold_chapter_title"] or self.current_settings["center_chapter_title"]:
            # 查找所有章节标题
            content = self.preview_text.get("1.0", tk.END)
            lines = content.split("\n")
            
            current_pos = "1.0"
            for line in lines:
                line_start = f"{current_pos} linestart"
                line_end = f"{current_pos} lineend"
                
                # 判断是否是章节标题，增加字符长度限制（少于20个字符才是标题）
                if line.strip() and (("第" in line and ("章" in line or "节" in line)) or \
                   any(line.startswith(prefix) for prefix in ["第", "序", "前言", "后记", "附录"])) and \
                   len(line) <= 20:
                    
                    # 应用加粗
                    if self.current_settings["bold_chapter_title"]:
                        self.preview_text.tag_add("chapter_title", line_start, line_end)
                    
                    # 应用居中
                    if self.current_settings["center_chapter_title"]:
                        self.preview_text.tag_add("center", line_start, line_end)
                
                # 移动到下一行
                try:
                    current_pos = self.preview_text.index(f"{line_end}+1c")
                except tk.TclError:
                    break
            
            # 配置章节标题标签
            font_style = "bold" if self.current_settings["bold_chapter_title"] else ""
            self.preview_text.tag_configure("chapter_title", 
                                         font=(self.current_settings["font_family"], 
                                               self.current_settings["font_size"], 
                                               font_style))
            
            # 配置居中标签
            if self.current_settings["center_chapter_title"]:
                self.preview_text.tag_configure("center", justify="center")
        
        # 如果有目录列表框，更新目录样式
        if self.toc_listbox and self.current_settings["bold_chapter_title"]:
            self.toc_listbox.config(font=(self.current_settings["font_family"], 
                                        self.current_settings["font_size"]))
    
    def save_settings(self):
        """
        保存设置到文件
        """
        try:
            # 获取应用程序目录
            app_dir = os.path.dirname(os.path.abspath(__file__))
            settings_file = os.path.join(app_dir, "display_settings.json")
            
            # 保存设置到JSON文件
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(self.current_settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存显示设置时出错: {str(e)}")
    
    def load_settings(self):
        """
        从文件加载设置
        """
        try:
            # 获取应用程序目录
            app_dir = os.path.dirname(os.path.abspath(__file__))
            settings_file = os.path.join(app_dir, "display_settings.json")
            
            # 如果设置文件存在，加载设置
            if os.path.exists(settings_file):
                with open(settings_file, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)
                
                # 更新当前设置
                for key, value in loaded_settings.items():
                    if key in self.current_settings:
                        self.current_settings[key] = value
        except Exception as e:
            print(f"加载显示设置时出错: {str(e)}")