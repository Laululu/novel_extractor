import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from bs4 import BeautifulSoup
import os
import re
import threading
import time
from urllib.parse import urlparse

class NovelExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("小说网页内容提取工具V1.10")
        self.root.geometry("700x800")
        self.root.resizable(True, True)
        
        # 初始化停止标志
        self.stop_flag = False
        
        # 设置应用程序样式
        style = ttk.Style()
        style.configure("TFrame", background="#F5F5F5")
        style.configure("TLabelframe", background="#F5F5F5", borderwidth=2)
        style.configure("TLabelframe.Label", font=("SimSun", 10, "bold"))
        style.configure("TButton", font=("SimSun", 9))
        style.configure("TRadiobutton", background="#F5F5F5", font=("SimSun", 9))
        style.configure("TCheckbutton", background="#F5F5F5", font=("SimSun", 9))
        style.configure("TLabel", background="#F5F5F5", font=("SimSun", 9))
        
        # 创建右键菜单
        self.create_context_menu()
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 网址输入区域
        self.url_frame = ttk.LabelFrame(self.main_frame, text="网页地址", padding="10")
        self.url_frame.pack(fill=tk.X, pady=5)
        
        # 为所有Entry控件启用复制粘贴功能
        self.root.option_add('*Entry.exportSelection', True)
        
        # 添加模式选择单选按钮
        self.mode_frame = ttk.Frame(self.url_frame)
        self.mode_frame.pack(fill=tk.X, pady=5)
        
        self.url_mode_var = tk.StringVar(value="range")
        
        # 创建单选按钮并水平排列
        self.radio_frame = ttk.Frame(self.mode_frame)
        self.radio_frame.pack(fill=tk.X, pady=2)
        
        self.range_mode_radio = ttk.Radiobutton(self.radio_frame, text="网页地址范围下载模式", 
                                              value="range", variable=self.url_mode_var,
                                              command=self.toggle_url_mode)
        self.range_mode_radio.pack(side=tk.LEFT, padx=10)
        
        self.batch_mode_radio = ttk.Radiobutton(self.radio_frame, text="粘贴批量网页地址模式", 
                                              value="batch", variable=self.url_mode_var,
                                              command=self.toggle_url_mode)
        self.batch_mode_radio.pack(side=tk.LEFT, padx=10)
        
        self.catalog_mode_radio = ttk.Radiobutton(self.radio_frame, text="小说目录模式", 
                                                value="catalog", variable=self.url_mode_var,
                                                command=self.toggle_url_mode)
        self.catalog_mode_radio.pack(side=tk.LEFT, padx=10)
        
        # 创建一个框架来容纳URL输入控件（范围模式）
        self.url_input_frame = ttk.Frame(self.url_frame)
        self.url_input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.url_input_frame, text="网页开始地址:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.start_url = ttk.Entry(self.url_input_frame, width=75)
        self.start_url.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(self.url_input_frame, text="网页结束地址:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.end_url = ttk.Entry(self.url_input_frame, width=75)
        self.end_url.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 批量网址输入框（初始隐藏）
        self.batch_url_frame = ttk.Frame(self.url_frame)
        self.batch_url_text = tk.Text(self.batch_url_frame, wrap=tk.WORD, height=6, width=70)
        self.batch_url_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.apply_text_bindings(self.batch_url_text)
        ttk.Label(self.batch_url_frame, text="请每行输入一个网址").pack(anchor=tk.W, pady=2)
        
        # 小说目录输入框（初始隐藏）
        self.catalog_url_frame = ttk.Frame(self.url_frame)
        self.catalog_url_frame.pack_forget()
        
        ttk.Label(self.catalog_url_frame, text="小说目录网址:").pack(anchor=tk.W, pady=5)
        self.catalog_url = ttk.Entry(self.catalog_url_frame, width=70)
        self.catalog_url.pack(fill=tk.X, pady=5)
        
        # 输出设置区域
        self.output_frame = ttk.LabelFrame(self.main_frame, text="输出设置", padding="10")
        self.output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.output_frame, text="小说保存为:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.output_path = ttk.Entry(self.output_frame, width=60)
        self.output_path.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.output_path.insert(0, os.path.join(os.path.expanduser("~"), "Documents", "合并小说.txt"))
        
        self.browse_btn = ttk.Button(self.output_frame, text="浏览...", command=self.browse_output_file)
        
        self.browse_btn.grid(row=0, column=2, padx=5)
        
        # 添加删除临时文件选项
        self.delete_temp_var = tk.BooleanVar(value=True)
        self.delete_temp_check = ttk.Checkbutton(self.output_frame, text="完成后删除临时文件", variable=self.delete_temp_var)
        self.delete_temp_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 创建一个框架来容纳多线程下载、测试下载量和备份文件数选项（放在同一行）
        self.settings_frame = ttk.Frame(self.output_frame)
        self.settings_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # 添加线程数选择
        ttk.Label(self.settings_frame, text="多线程下载:").pack(side=tk.LEFT, padx=(0, 5))
        self.thread_count_frame = ttk.Frame(self.settings_frame)
        self.thread_count_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        self.thread_count_var = tk.IntVar(value=3)
        self.thread_count_spinbox = ttk.Spinbox(self.thread_count_frame, from_=1, to=10, width=5, textvariable=self.thread_count_var)
        self.thread_count_spinbox.pack(side=tk.LEFT)
        ttk.Label(self.thread_count_frame, text="(建议不超过5)").pack(side=tk.LEFT, padx=5)
        
        # 添加下载测试文件数量选择
        ttk.Label(self.settings_frame, text="测试下载量:").pack(side=tk.LEFT, padx=(0, 5))
        self.test_count_frame = ttk.Frame(self.settings_frame)
        self.test_count_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        self.test_count_var = tk.IntVar(value=0)
        self.test_count_spinbox = ttk.Spinbox(self.test_count_frame, from_=0, to=1000, width=5, textvariable=self.test_count_var)
        self.test_count_spinbox.pack(side=tk.LEFT)
        ttk.Label(self.test_count_frame, text="(0下载全部)").pack(side=tk.LEFT, padx=5)
        
        # 添加备份次数选择
        ttk.Label(self.settings_frame, text="备份文件数:").pack(side=tk.LEFT, padx=(0, 5))
        self.backup_count_frame = ttk.Frame(self.settings_frame)
        self.backup_count_frame.pack(side=tk.LEFT)
        
        self.backup_count_var = tk.IntVar(value=2)
        self.backup_count_spinbox = ttk.Spinbox(self.backup_count_frame, from_=0, to=10, width=5, textvariable=self.backup_count_var)
        self.backup_count_spinbox.pack(side=tk.LEFT)
        ttk.Label(self.backup_count_frame, text="(0不备份)").pack(side=tk.LEFT, padx=5)
        
        # 添加自定义规则区域
        self.filter_frame = ttk.LabelFrame(self.main_frame, text="自定义规则", padding="10")
        self.filter_frame.pack(fill=tk.X, pady=5)
        
        # 创建一个框架来容纳规则列表
        self.rules_frame = ttk.Frame(self.filter_frame)
        self.rules_frame.pack(fill=tk.X, pady=5)
        
        # 初始化规则列表
        self.filter_rules = []
        # 初始化替换规则列表
        self.replace_rules = []
        
        # 创建一个框架来容纳三个选项，使它们在同一行
        self.options_frame = ttk.Frame(self.filter_frame)
        self.options_frame.pack(fill=tk.X, pady=5)
        
        # 添加段落缩进选项
        self.paragraph_indent_var = tk.BooleanVar(value=True)
        self.paragraph_indent_check = ttk.Checkbutton(self.options_frame, text="段落缩进", variable=self.paragraph_indent_var)
        self.paragraph_indent_check.pack(side=tk.LEFT, padx=10)
        
        # 添加删除行末数字选项
        self.remove_end_numbers_var = tk.BooleanVar(value=True)
        self.remove_end_numbers_check = ttk.Checkbutton(self.options_frame, text="删除行末数字", variable=self.remove_end_numbers_var)
        self.remove_end_numbers_check.pack(side=tk.LEFT, padx=10)
        
        # 添加删除空行选项
        self.remove_empty_lines_var = tk.BooleanVar(value=False)
        self.remove_empty_lines_check = ttk.Checkbutton(self.options_frame, text="删除空行", variable=self.remove_empty_lines_var)
        self.remove_empty_lines_check.pack(side=tk.LEFT, padx=10)
        
        # 添加删除上下行相同字符选项
        self.remove_duplicate_lines_var = tk.BooleanVar(value=False)
        self.remove_duplicate_lines_check = ttk.Checkbutton(self.options_frame, text="删除上下行相同字符", variable=self.remove_duplicate_lines_var)
        self.remove_duplicate_lines_check.pack(side=tk.LEFT, padx=10)
        
        # 添加默认规则
        self.add_filter_rule("新书推荐", "目录")
        self.add_filter_rule("请收藏本站", "目录")
        
        # 添加按钮区域
        self.rules_btn_frame = ttk.Frame(self.filter_frame)
        self.rules_btn_frame.pack(fill=tk.X, pady=5)
        
        self.add_rule_btn = ttk.Button(self.rules_btn_frame, text="添加删除规则", command=self.add_empty_rule)
        self.add_rule_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加替换规则按钮
        self.add_replace_rule_btn = ttk.Button(self.rules_btn_frame, text="添加替换规则", command=self.add_empty_replace_rule)
        self.add_replace_rule_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加特殊删除按钮
        self.add_special_replace_btn = ttk.Button(self.rules_btn_frame, text="添加特殊删除", command=self.add_special_replace_rule)
        self.add_special_replace_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_rules_btn = ttk.Button(self.rules_btn_frame, text="导出规则", command=self.export_rules)
        self.export_rules_btn.pack(side=tk.LEFT, padx=5)
        
        self.import_rules_btn = ttk.Button(self.rules_btn_frame, text="导入规则", command=self.import_rules)
        self.import_rules_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加恢复备份按钮
        self.restore_btn = ttk.Button(self.rules_btn_frame, text="恢复备份", command=self.restore_backup)
        self.restore_btn.pack(side=tk.LEFT, padx=5)
        
        # 操作按钮区域
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        self.extract_btn = ttk.Button(self.button_frame, text="开始提取", command=self.start_extraction)
        self.extract_btn.pack(side=tk.LEFT, padx=5)
        
        self.extract_with_rules_btn = ttk.Button(self.button_frame, text="提取并应用规则", command=self.start_extraction_with_rules)
        self.extract_with_rules_btn.pack(side=tk.LEFT, padx=5)
        
        self.apply_rules_btn = ttk.Button(self.button_frame, text="应用规则", command=self.apply_rules_to_file)
        self.apply_rules_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(self.button_frame, text="停止", command=self.stop_extraction)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(self.button_frame, text="清空", command=self.clear_fields)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加预览按钮
        self.preview_var = tk.BooleanVar(value=False)
        self.preview_btn = ttk.Button(self.button_frame, text="预览", command=self.toggle_preview)
        self.preview_btn.pack(side=tk.LEFT, padx=5)
        
        # 预览框架（初始隐藏）- 作为独立窗口吸附在右侧
        self.preview_frame = ttk.LabelFrame(self.root, text="预览内容", padding="10")
        # 设置预览框架的最小宽度，确保能完整显示目录内容
        self.preview_frame.config(width=400)
        
        # 添加按钮框架
        self.preview_btn_frame = ttk.Frame(self.preview_frame)
        self.preview_btn_frame.pack(fill=tk.X, pady=5)
        
        # 添加显示设置按钮
        self.display_settings_btn = ttk.Button(self.preview_btn_frame, text="显示设置", command=self.show_display_settings)
        self.display_settings_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加查找替换按钮
        self.search_btn = ttk.Button(self.preview_btn_frame, text="查找替换", command=self.show_search_replace)
        self.search_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加保存按钮
        self.save_btn = ttk.Button(self.preview_btn_frame, text="保存", command=self.save_preview_content)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加目录按钮
        self.toc_btn = ttk.Button(self.preview_btn_frame, text="目录", command=self.toggle_chapter_toc)
        self.toc_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加更新目录按钮
        self.update_toc_btn = ttk.Button(self.preview_btn_frame, text="更新目录", command=self.update_chapter_toc)
        self.update_toc_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加向上翻页按钮
        self.page_up_btn = ttk.Button(self.preview_btn_frame, text="向上翻页", command=self.page_up)
        self.page_up_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加向下翻页按钮
        self.page_down_btn = ttk.Button(self.preview_btn_frame, text="向下翻页", command=self.page_down)
        self.page_down_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建主预览区域框架
        self.preview_content_frame = ttk.Frame(self.preview_frame)
        self.preview_content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 预览文本区域
        self.preview_text = tk.Text(self.preview_content_frame, wrap=tk.WORD, width=50)
        self.preview_scrollbar = ttk.Scrollbar(self.preview_content_frame, command=self.preview_text.yview)
        self.preview_text.config(yscrollcommand=self.preview_scrollbar.set)
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建目录框架（初始隐藏）
        self.toc_frame = ttk.LabelFrame(self.preview_content_frame, text="章节目录")
        self.toc_visible = False
        # 设置预览文本框的字体和样式
        self.preview_text.config(font=("SimSun", 11))
        self.preview_text.config(bg="#FAFAFA", relief=tk.SUNKEN, borderwidth=1)
        # 应用文本绑定（包括鼠标右键菜单和快捷键）
        self.apply_text_bindings(self.preview_text)
        
        # 初始化章节目录数据
        self.chapter_positions = []
        self.toc_visible = False
        

        
        # 进度显示区域
        self.progress_frame = ttk.LabelFrame(self.main_frame, text="处理进度", padding="10")
        self.progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # 创建日志文本框
        self.log_frame = ttk.Frame(self.progress_frame)
        self.log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(self.log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.apply_text_bindings(self.log_text)
        
        self.scrollbar = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=self.scrollbar.set)
        
        # 初始化变量
        self.extracted_files = {}
        self.is_running = False
        self.stop_flag = False
        self.display_settings = None  # 初始化显示设置对象
        
        # 为所有文本控件启用复制粘贴功能
        for widget in [self.start_url, self.end_url, self.catalog_url, self.output_path, 
                       self.batch_url_text, self.preview_text, self.log_text]:
            if isinstance(widget, tk.Text) or isinstance(widget, tk.Entry) or isinstance(widget, ttk.Entry):
                widget.bind("<Button-3>", self.show_context_menu)
                
    def show_display_settings(self):
        """显示设置对话框"""
        # 如果显示设置对象未初始化，则创建一个新的实例
        if self.display_settings is None:
            from display_settings import DisplaySettings
            self.display_settings = DisplaySettings(self.root, self.preview_text, apply_callback=self.apply_display_settings)
        
        # 显示设置对话框
        self.display_settings.show_settings_dialog()
        
    def apply_display_settings(self):
        """应用显示设置的回调函数"""
        # 应用页边距设置
        if self.display_settings and hasattr(self.display_settings, 'current_settings'):
            margin = self.display_settings.current_settings.get("page_margin", 10)
            self.preview_text.config(padx=margin)
            
    def page_up(self):
        """向上翻页"""
        # 使用内置的yview方法向上滚动一页
        self.preview_text.yview_scroll(-1, "pages")
        
    def page_down(self):
        """向下翻页"""
        # 使用内置的yview方法向下滚动一页
        self.preview_text.yview_scroll(1, "pages")
        
    
    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="剪切", command=lambda: self.root.focus_get().event_generate("<<Cut>>"))
        self.context_menu.add_command(label="复制", command=lambda: self.root.focus_get().event_generate("<<Copy>>"))
        self.context_menu.add_command(label="粘贴", command=self.custom_paste_menu)
        self.context_menu.add_command(label="全选", command=self.select_all)
        
    def custom_paste_menu(self):
        """自定义粘贴菜单命令，避免重复粘贴"""
        widget = self.root.focus_get()
        if widget:
            self.custom_paste(widget)
    
    def custom_paste(self, widget):
        """自定义粘贴函数，避免重复粘贴"""
        try:
            # 禁用默认的粘贴事件处理
            widget.unbind("<Control-v>")
            # 执行一次粘贴操作
            widget.event_generate("<<Paste>>")
            # 重新绑定粘贴事件
            widget.bind("<Control-v>", lambda e: self.custom_paste(widget))
            return "break"
        except Exception as e:
            self.log(f"粘贴时出错: {str(e)}")
            return None
        
    def select_all(self):
        """全选文本"""
        widget = self.root.focus_get()
        if isinstance(widget, tk.Text):
            widget.tag_add(tk.SEL, "1.0", tk.END)
            return "break"
        elif isinstance(widget, tk.Entry) or isinstance(widget, ttk.Entry):
            widget.select_range(0, tk.END)
            return "break"
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        widget = event.widget
        # 确保文本被选中时才显示菜单
        if isinstance(widget, tk.Text):
            # 如果没有选中文本，则在点击位置设置插入光标
            try:
                widget.mark_set("insert", "@%d,%d" % (event.x, event.y))
                # 如果没有选中文本，则选中当前单词
                if not widget.tag_ranges(tk.SEL):
                    widget.tag_add(tk.SEL, "insert wordstart", "insert wordend")
            except:
                pass
        elif isinstance(widget, tk.Entry) or isinstance(widget, ttk.Entry):
            widget.focus_set()
            
        self.context_menu.post(event.x_root, event.y_root)
        return "break"
    
    def apply_text_bindings(self, text_widget):
        """为文本框应用绑定，启用复制粘贴功能"""
        # 绑定右键菜单
        text_widget.bind("<Button-3>", self.show_context_menu)
        # 绑定快捷键
        text_widget.bind("<Control-a>", lambda e: self.select_all())
        text_widget.bind("<Control-c>", lambda e: text_widget.event_generate("<<Copy>>"))
        # 修复Ctrl+V粘贴重复的问题，使用自定义粘贴函数
        text_widget.bind("<Control-v>", lambda e: self.custom_paste(text_widget))
        text_widget.bind("<Control-x>", lambda e: text_widget.event_generate("<<Cut>>"))
    
    def browse_output_file(self):
        filepath = filedialog.asksaveasfilename(title="小说保存为", defaultextension=".txt", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if filepath:
            self.output_path.delete(0, tk.END)
            self.output_path.insert(0, filepath)
            
            # 如果预览窗口已打开，自动更新预览内容显示新选择的文件
            if self.preview_var.get() and os.path.exists(filepath):
                try:
                    # 获取文件大小
                    file_size = os.path.getsize(filepath) / (1024 * 1024)  # 转换为MB
                    self.log(f"预览文件大小: {file_size:.2f} MB")
                    
                    # 清空预览文本框和章节目录数据
                    self.preview_text.delete(1.0, tk.END)
                    self.chapter_positions = []
                    
                    # 如果文件大于2MB，使用分块加载
                    if file_size > 2:
                        self.load_large_file(filepath)
                    else:
                        # 小文件直接加载
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        self.preview_text.insert(tk.END, content)
                        self.log(f"已加载预览文件: {filepath}")
                    
                    # 确保每次加载新文件后都应用显示设置
                    if self.display_settings is None:
                        from display_settings import DisplaySettings
                        self.display_settings = DisplaySettings(self.root, self.preview_text, apply_callback=self.apply_display_settings)
                    self.display_settings.apply_settings_to_preview()
                    self.apply_display_settings()
                        
                    # 不再自动提取章节目录，只在用户点击更新目录按钮时更新
                except Exception as e:
                    self.log(f"加载预览文件时出错: {str(e)}")
                    messagebox.showerror("错误", f"加载预览文件时出错: {str(e)}")
    
    def toggle_url_mode(self):
        """切换URL输入模式（范围模式/批量模式/目录模式）"""
        mode = self.url_mode_var.get()
        
        # 隐藏所有输入框
        self.url_input_frame.pack_forget()
        self.batch_url_frame.pack_forget()
        self.catalog_url_frame.pack_forget()
        
        # 根据选择的模式显示对应的输入框
        if mode == "range":
            # 范围模式
            self.url_input_frame.pack(fill=tk.X, pady=5)
        elif mode == "batch":
            # 批量模式
            self.batch_url_frame.pack(fill=tk.X, pady=5)
        elif mode == "catalog":
            # 目录模式
            self.catalog_url_frame.pack(fill=tk.X, pady=5)
    
    def clear_fields(self):
        self.start_url.delete(0, tk.END)
        self.end_url.delete(0, tk.END)
        self.batch_url_text.delete(1.0, tk.END)
        self.catalog_url.delete(0, tk.END)
        self.output_path.delete(0, tk.END)
        self.output_path.insert(0, os.path.join(os.path.expanduser("~"), "Documents", "合并小说.txt"))
        self.log_text.delete(1.0, tk.END)
        self.progress_bar['value'] = 0
        self.extracted_files = {}
        self.thread_count_var.set(3)  # 重置线程数为默认值
        self.test_count_var.set(0)  # 重置测试文件个数为默认值
        self.delete_temp_var.set(True)  # 重置删除临时文件选项为默认值
        self.remove_end_numbers_var.set(True)  # 重置删除行末数字选项为默认值
        self.url_mode_var.set("range")  # 重置为范围模式
        self.toggle_url_mode()  # 切换回范围模式
        
        # 重置过滤规则
        for rule_frame in self.filter_rules:
            rule_frame.destroy()
        self.filter_rules = []
        
        # 添加默认规则
        self.add_filter_rule("新书推荐", "目录")
        self.add_filter_rule("请收藏本站", "目录")
    
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def parse_catalog_page(self, catalog_url):
        """解析小说目录页面，提取包含'第'和'章'的链接"""
        try:
            self.log(f"正在解析目录页面: {catalog_url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(catalog_url, headers=headers, timeout=30)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有链接
            links = soup.find_all('a')
            chapter_links = []
            
            # 针对特定网站的解析逻辑
            if '.cc' in catalog_url:
                # 针对特殊处理
                self.log("检测到**网站，使用特定解析逻辑")
                # 尝试查找章节列表容器
                chapter_containers = soup.select('dl, .listmain, #list, .chapterlist, .article_texttitleb, #chapterlist')
                
                if chapter_containers:
                    for container in chapter_containers:
                        container_links = container.find_all('a')
                        if len(container_links) > 10:  # 假设章节列表至少有10个链接
                            links = container_links
                            self.log(f"找到可能的章节列表容器，包含 {len(links)} 个链接")
                            break
            
            # 筛选章节链接
            for link in links:
                text = link.get_text().strip()
                href = link.get('href')
                # 扩展匹配条件，增加对各种章节格式的支持
                is_chapter = False
                if href:
                    # 检查是否包含章节关键词
                    if ('第' in text and ('章' in text or '节' in text)) or \
                       re.search(r'\d+\.', text) or \
                       re.search(r'chapter|chap\.?\s*\d+', text, re.IGNORECASE):
                        is_chapter = True
                    # 检查链接是否符合章节URL模式
                    elif re.search(r'\d+\.html$|\/\d+\.htm$|\/\d+\/$', href):
                        is_chapter = True
                
                if is_chapter:
                    # 构建完整URL
                    if not href.startswith('http'):
                        # 相对路径，需要构建完整URL
                        base_url = urlparse(catalog_url)
                        if href.startswith('/'):
                            # 绝对路径
                            full_url = f"{base_url.scheme}://{base_url.netloc}{href}"
                        else:
                            # 相对路径
                            path_parts = base_url.path.split('/')
                            if path_parts[-1]:
                                path_parts.pop()
                            base_path = '/'.join(path_parts)
                            full_url = f"{base_url.scheme}://{base_url.netloc}{base_path}/{href}"
                    else:
                        # 已经是完整URL
                        full_url = href
                    
                    chapter_links.append((text, full_url))
            
            # 按章节顺序排序（尝试提取章节数字）
            def extract_chapter_number(chapter_text):
                # 尝试多种章节号提取模式
                patterns = [
                    r'第(\d+)章',
                    r'第(\d+)节',
                    r'(\d+)\.',
                    r'Chapter\s*(\d+)',
                    r'(\d+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, chapter_text, re.IGNORECASE)
                    if match:
                        return int(match.group(1))
                return 0
            
            chapter_links.sort(key=lambda x: extract_chapter_number(x[0]))
            
            self.log(f"共找到 {len(chapter_links)} 个章节链接")
            return chapter_links
        
        except Exception as e:
            self.log(f"解析目录页面出错: {str(e)}")
            return []
    
    def extract_catalog_content(self, catalog_url, output_dir, output_filename, thread_count, delete_temp, apply_rules=False):
        """从小说目录页面提取所有章节内容
        
        参数:
            catalog_url: 小说目录页面URL
            output_dir: 输出目录
            output_filename: 输出文件名
            thread_count: 线程数
            delete_temp: 是否删除临时文件
            apply_rules: 是否应用自定义规则
        """
        try:
            # 解析目录页面，获取章节链接
            chapter_links = self.parse_catalog_page(catalog_url)
            
            if not chapter_links:
                self.log("未找到有效的章节链接，请检查目录页面是否正确")
                messagebox.showerror("错误", "未找到有效的章节链接，请检查目录页面是否正确")
                self.is_running = False
                self.extract_btn.config(state=tk.NORMAL)
                self.extract_with_rules_btn.config(state=tk.NORMAL)
                self.apply_rules_btn.config(state=tk.NORMAL)
                return
            
            # 提取章节URL列表
            urls = [url for _, url in chapter_links]
            
            # 获取测试文件个数限制
            test_count = self.test_count_var.get()
            if test_count > 0 and test_count < len(urls):
                self.log(f"根据设置，仅下载前 {test_count} 个文件进行测试")
                urls = urls[:test_count]
            
            # 使用批量模式处理这些URL
            self.extract_batch_content(urls, output_dir, output_filename, thread_count, delete_temp, apply_rules)
            
        except Exception as e:
            self.log(f"处理目录页面时出错: {str(e)}")
            messagebox.showerror("错误", f"处理目录页面时出错: {str(e)}")
            self.is_running = False
            self.stop_flag = False
            self.extract_btn.config(state=tk.NORMAL)
            self.extract_with_rules_btn.config(state=tk.NORMAL)
            self.apply_rules_btn.config(state=tk.NORMAL)
    
    def start_extraction(self):
        """开始提取网页内容，但不应用自定义规则"""
        if self.is_running:
            messagebox.showwarning("警告", "已有提取任务正在运行！")
            return
            
        # 重置停止标志
        self.stop_flag = False
        
        # 获取输入
        output_path = self.output_path.get().strip()
        thread_count = self.thread_count_var.get()
        delete_temp = self.delete_temp_var.get()
        mode = self.url_mode_var.get()
        
        # 验证输入
        if mode == "batch":
            # 批量模式下验证输入
            batch_urls = self.get_batch_urls()
            if not batch_urls:
                messagebox.showerror("错误", "请输入至少一个有效的网址！")
                return
        elif mode == "range":
            # 范围模式下验证输入
            start_url = self.start_url.get().strip()
            end_url = self.end_url.get().strip()
            if not start_url or not end_url:
                messagebox.showerror("错误", "请输入有效网址！")
                return
        elif mode == "catalog":
            # 目录模式下验证输入
            catalog_url = self.catalog_url.get().strip()
            if not catalog_url:
                messagebox.showerror("错误", "请输入小说目录网址！")
                return
        
        if not output_path:
            messagebox.showerror("错误", "请选择小说保存路径！")
            return
        
        # 确保线程数在合理范围内
        if thread_count < 1:
            thread_count = 1
        elif thread_count > 10:
            thread_count = 10
        
        # 检查文件是否存在，如果存在则询问是否覆盖
        if os.path.exists(output_path):
            if not messagebox.askyesno("文件已存在", f"文件 {output_path} 已存在，是否覆盖？"):
                # 用户选择不覆盖，让用户重新选择保存路径
                new_path = filedialog.asksaveasfilename(title="小说另存为", defaultextension=".txt", 
                                                     filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
                if not new_path:
                    return  # 用户取消了操作
                output_path = new_path
                self.output_path.delete(0, tk.END)
                self.output_path.insert(0, output_path)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("错误", f"创建输出目录失败: {str(e)}")
                return
        
        # 获取文件名
        output_filename = os.path.basename(output_path)
        
        # 启动提取线程
        self.extracted_files = {}
        self.is_running = True
        self.extract_btn.config(state=tk.DISABLED)
        self.extract_with_rules_btn.config(state=tk.DISABLED)
        self.apply_rules_btn.config(state=tk.DISABLED)
        
        if mode == "batch":
            # 批量模式
            extraction_thread = threading.Thread(target=self.extract_batch_content, 
                                               args=(batch_urls, output_dir, output_filename, thread_count, delete_temp, False))
        elif mode == "range":
            # 范围模式
            extraction_thread = threading.Thread(target=self.extract_content, 
                                               args=(start_url, end_url, output_dir, output_filename, thread_count, delete_temp, False))
        elif mode == "catalog":
            # 目录模式
            extraction_thread = threading.Thread(target=self.extract_catalog_content, 
                                               args=(catalog_url, output_dir, output_filename, thread_count, delete_temp, False))
        
        extraction_thread.daemon = True
        extraction_thread.start()
    
    def get_batch_urls(self):
        """从批量URL文本框中获取URL列表"""
        urls_text = self.batch_url_text.get(1.0, tk.END).strip()
        if not urls_text:
            return []
        
        # 按行分割并过滤空行
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        return urls
    
    def extract_batch_content(self, urls, output_dir, output_filename, thread_count, delete_temp, apply_rules=False):
        """提取批量网页内容并合并
        
        参数:
            urls: URL列表
            output_dir: 输出目录
            output_filename: 输出文件名
            thread_count: 线程数
            delete_temp: 是否删除临时文件
            apply_rules: 是否应用自定义规则
        """
        try:
            # 获取测试文件个数限制
            test_count = self.test_count_var.get()
            if test_count > 0 and test_count < len(urls):
                self.log(f"根据设置，仅下载前 {test_count} 个文件进行测试")
                urls = urls[:test_count]
            
            total_urls = len(urls)
            self.log(f"共找到 {total_urls} 个网页需要处理")
            self.progress_bar['maximum'] = total_urls
            
            # 创建线程安全的变量
            self.processed_count = 0
            self.lock = threading.Lock()
            
            # 定义工作线程函数
            def worker(url_list):
                for url_info in url_list:
                    i, url = url_info
                    try:
                        # 下载并解析网页
                        content = self.download_and_extract(url)
                        
                        # 保存为临时文件
                        filename = f"chapter_{i+1}.txt"
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        with self.lock:
                            # 使用索引作为键存储文件路径，确保后续可以按顺序合并
                            self.extracted_files[i] = filepath
                            self.processed_count += 1
                            self.log(f"正在处理 ({self.processed_count}/{total_urls}): {url}")
                            self.log(f"已保存: {filename}")
                            # 更新进度条
                            self.progress_bar['value'] = self.processed_count
                            self.root.update_idletasks()
                            
                    except Exception as e:
                        with self.lock:
                            self.processed_count += 1
                            self.log(f"处理 {url} 时出错: {str(e)}")
                            # 更新进度条
                            self.progress_bar['value'] = self.processed_count
                            self.root.update_idletasks()
            
            # 将URL列表分成多个子列表，每个线程处理一部分
            url_chunks = []
            total_urls_count = len(urls)
            
            # 确保所有URL都被分配，即使不能被线程数整除
            if total_urls_count <= thread_count:
                # 如果URL数量少于或等于线程数，每个线程处理一个URL
                for i in range(total_urls_count):
                    url_chunks.append([(i, urls[i])])
            else:
                # 计算基本的块大小和余数
                base_chunk_size = total_urls_count // thread_count
                remainder = total_urls_count % thread_count
                
                start_idx = 0
                for i in range(thread_count):
                    # 为前remainder个线程多分配一个URL
                    current_chunk_size = base_chunk_size + (1 if i < remainder else 0)
                    end_idx = start_idx + current_chunk_size
                    
                    # 创建(索引, url)元组列表
                    chunk = [(idx, urls[idx]) for idx in range(start_idx, end_idx)]
                    url_chunks.append(chunk)
                    
                    start_idx = end_idx
            
            # 启动工作线程
            threads = []
            self.log(f"启动 {len(url_chunks)} 个线程进行处理...")
            
            for i in range(len(url_chunks)):
                t = threading.Thread(target=worker, args=(url_chunks[i],))
                t.daemon = True
                threads.append(t)
                t.start()
            
            # 等待所有线程完成
            for t in threads:
                t.join()
            
            # 合并文件
            if self.extracted_files:
                self.log("正在合并文件...")
                merged_filepath = os.path.join(output_dir, output_filename)
                
                if apply_rules:
                    self.log("应用自定义规则并合并文件...")
                    self.merge_files_with_rules(self.extracted_files, merged_filepath)
                else:
                    self.log("仅合并文件，不应用规则...")
                    self.merge_files_without_rules(self.extracted_files, merged_filepath)
                
                self.log(f"合并完成: {merged_filepath}")
                
                # 根据设置删除临时文件
                if delete_temp:
                    self.log("正在删除临时文件...")
                    for file in self.extracted_files.values():
                        try:
                            os.remove(file)
                        except:
                            pass
                    self.log("临时文件已删除")
            
            self.log("全部处理完成！")
            messagebox.showinfo("完成", "小说内容提取和合并已完成！")
            
            # 如果预览窗口已打开，更新预览内容
            if self.preview_var.get() and os.path.exists(merged_filepath):
                try:
                    with open(merged_filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.preview_text.delete(1.0, tk.END)
                    self.preview_text.insert(tk.END, content)
                except Exception as e:
                    self.log(f"更新预览内容时出错: {str(e)}")
            
        except Exception as e:
            self.log(f"处理过程中发生错误: {str(e)}")
            messagebox.showerror("错误", f"处理过程中发生错误: {str(e)}")
        
        finally:
            self.is_running = False
            self.stop_flag = False
            self.extract_btn.config(state=tk.NORMAL)
            self.extract_with_rules_btn.config(state=tk.NORMAL)
            self.apply_rules_btn.config(state=tk.NORMAL)
    
    def start_extraction_with_rules(self):
        """开始提取网页内容，并应用自定义规则"""
        if self.is_running:
            messagebox.showwarning("警告", "已有提取任务正在运行！")
            return
            
        # 重置停止标志
        self.stop_flag = False
        
        # 获取输出文件路径
        output_path = self.output_path.get().strip()
        
        # 如果文件已存在且备份次数大于0，则创建备份
        backup_count = self.backup_count_var.get()
        if backup_count > 0 and os.path.exists(output_path):
            self.backup_file(output_path)
        
        # 获取输入
        output_path = self.output_path.get().strip()
        thread_count = self.thread_count_var.get()
        delete_temp = self.delete_temp_var.get()
        mode = self.url_mode_var.get()
        
        # 验证输入
        if mode == "batch":
            # 批量模式下验证输入
            batch_urls = self.get_batch_urls()
            if not batch_urls:
                messagebox.showerror("错误", "请输入至少一个有效的网址！")
                return
        elif mode == "range":
            # 范围模式下验证输入
            start_url = self.start_url.get().strip()
            end_url = self.end_url.get().strip()
            if not start_url or not end_url:
                messagebox.showerror("错误", "请输入有效网址！")
                return
        elif mode == "catalog":
            # 目录模式下验证输入
            catalog_url = self.catalog_url.get().strip()
            if not catalog_url:
                messagebox.showerror("错误", "请输入小说目录网址！")
                return
        
        if not output_path:
            messagebox.showerror("错误", "请选择小说保存路径！")
            return
        
        # 确保线程数在合理范围内
        if thread_count < 1:
            thread_count = 1
        elif thread_count > 10:
            thread_count = 10
        
        # 检查文件是否存在，如果存在则询问是否覆盖
        if os.path.exists(output_path):
            if not messagebox.askyesno("文件已存在", f"文件 {output_path} 已存在，是否覆盖？"):
                # 用户选择不覆盖，让用户重新选择保存路径
                new_path = filedialog.asksaveasfilename(title="小说另存为", defaultextension=".txt", 
                                                     filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
                if not new_path:
                    return  # 用户取消了操作
                output_path = new_path
                self.output_path.delete(0, tk.END)
                self.output_path.insert(0, output_path)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("错误", f"创建输出目录失败: {str(e)}")
                return
        
        # 获取文件名
        output_filename = os.path.basename(output_path)
        
        # 启动提取线程
        self.extracted_files = {}
        self.is_running = True
        self.extract_btn.config(state=tk.DISABLED)
        self.extract_with_rules_btn.config(state=tk.DISABLED)
        self.apply_rules_btn.config(state=tk.DISABLED)
        
        if mode == "batch":
            # 批量模式
            extraction_thread = threading.Thread(target=self.extract_batch_content, 
                                               args=(batch_urls, output_dir, output_filename, thread_count, delete_temp, True))
        elif mode == "range":
            # 范围模式
            extraction_thread = threading.Thread(target=self.extract_content, 
                                               args=(start_url, end_url, output_dir, output_filename, thread_count, delete_temp, True))
        elif mode == "catalog":
            # 目录模式
            extraction_thread = threading.Thread(target=self.extract_catalog_content, 
                                               args=(catalog_url, output_dir, output_filename, thread_count, delete_temp, True))
        
        extraction_thread.daemon = True
        extraction_thread.start()
    
    def extract_chapter_toc(self, content=None):
        """从文本内容中提取章节目录
        如果content为None，则从预览文本框中提取
        添加字符数量检测，超过20个字符的行不计入目录
        使用多线程技术加快目录提取速度
        """
        self.chapter_positions = []
        # 不再保存内容引用，每次都重新提取目录
        
        try:
            # 显示提取进度对话框
            progress_window = tk.Toplevel(self.root)
            progress_window.title("提取章节目录")
            progress_window.geometry("300x100")
            progress_window.transient(self.root)  # 设置为主窗口的子窗口
            progress_window.grab_set()  # 模态对话框
            
            ttk.Label(progress_window, text="正在提取章节目录，请稍候...").pack(pady=10)
            progress_bar = ttk.Progressbar(progress_window, orient=tk.HORIZONTAL, length=250, mode='determinate')
            progress_bar.pack(pady=5)
            progress_label = ttk.Label(progress_window, text="0%")
            progress_label.pack(pady=5)
            progress_window.update()
            
            # 如果没有提供内容，则从预览文本框中获取
            if content is None:
                # 从预览文本框中直接获取每一行，避免一次性获取全部内容
                total_lines = int(self.preview_text.index('end-1c').split('.')[0])
                self.log(f"开始从预览文本中提取章节目录，共 {total_lines} 行")
                
                # 获取线程数
                thread_count = min(self.thread_count_var.get(), 10)  # 最多10个线程
                self.log(f"使用 {thread_count} 个线程提取章节目录")
                
                # 分块处理数据
                chunk_size = max(1, total_lines // thread_count)
                chunks = []
                for i in range(0, total_lines, chunk_size):
                    end = min(i + chunk_size, total_lines)
                    chunks.append((i + 1, end + 1))  # 行号从1开始
                
                # 线程安全的结果列表
                from queue import Queue
                result_queue = Queue()
                
                # 定义线程函数
                def process_chunk(start_line, end_line, queue):
                    local_positions = []
                    for i in range(start_line, end_line):
                        try:
                            # 获取当前行文本
                            line = self.preview_text.get(f"{i}.0", f"{i}.end").strip()
                            
                            # 匹配章节标题
                            if (('第' in line and ('章' in line or '节' in line)) or 
                                re.search(r'^\d+\.\s+\S+', line) or 
                                re.search(r'chapter|chap\.?\s*\d+', line, re.IGNORECASE)):
                                # 检查字符数量，超过20个字符的行不计入目录
                                if len(line) <= 20:
                                    # 记录章节标题和在文本中的位置
                                    position = f"{i}.0"
                                    local_positions.append((line, position))
                        except Exception as e:
                            self.log(f"处理第 {i} 行时出错: {str(e)}")
                    
                    # 将结果放入队列
                    queue.put(local_positions)
                
                # 创建并启动线程
                threads = []
                for start, end in chunks:
                    thread = threading.Thread(target=process_chunk, args=(start, end, result_queue))
                    thread.daemon = True
                    threads.append(thread)
                    thread.start()
                
                # 更新进度条
                completed_threads = 0
                while completed_threads < len(threads):
                    # 检查已完成的线程数
                    completed_threads = sum(1 for t in threads if not t.is_alive())
                    progress_value = int((completed_threads / len(threads)) * 100)
                    progress_bar['value'] = progress_value
                    progress_label.config(text=f"{progress_value}%")
                    progress_window.title(f"提取章节目录 ({completed_threads}/{len(threads)} 线程)")
                    progress_window.update()
                    time.sleep(0.1)  # 避免过度消耗CPU
                
                # 等待所有线程完成
                for thread in threads:
                    thread.join()
                
                # 收集所有结果
                while not result_queue.empty():
                    self.chapter_positions.extend(result_queue.get())
                
                # 按位置排序章节
                self.chapter_positions.sort(key=lambda x: int(x[1].split('.')[0]))
                
            else:
                # 使用传入的内容提取章节
                lines = content.split('\n')
                total_lines = len(lines)
                self.log(f"开始从内容中提取章节目录，共 {total_lines} 行")
                
                # 获取线程数
                thread_count = min(self.thread_count_var.get(), 10)  # 最多10个线程
                self.log(f"使用 {thread_count} 个线程提取章节目录")
                
                # 分块处理数据
                chunk_size = max(1, total_lines // thread_count)
                chunks = []
                for i in range(0, total_lines, chunk_size):
                    end = min(i + chunk_size, total_lines)
                    chunks.append((i, end))
                
                # 线程安全的结果列表
                from queue import Queue
                result_queue = Queue()
                
                # 定义线程函数
                def process_content_chunk(start_idx, end_idx, queue):
                    local_positions = []
                    for i in range(start_idx, end_idx):
                        try:
                            line = lines[i].strip()
                            # 匹配章节标题
                            if (('第' in line and ('章' in line or '节' in line)) or 
                                re.search(r'^\d+\.\s+\S+', line) or 
                                re.search(r'chapter|chap\.?\s*\d+', line, re.IGNORECASE)):
                                # 检查字符数量，超过20个字符的行不计入目录
                                if len(line) <= 20:
                                    # 记录章节标题和行号
                                    local_positions.append((line, str(i+1) + ".0"))
                        except Exception as e:
                            self.log(f"处理内容第 {i} 行时出错: {str(e)}")
                    
                    # 将结果放入队列
                    queue.put(local_positions)
                
                # 创建并启动线程
                threads = []
                for start, end in chunks:
                    thread = threading.Thread(target=process_content_chunk, args=(start, end, result_queue))
                    thread.daemon = True
                    threads.append(thread)
                    thread.start()
                
                # 更新进度条
                completed_threads = 0
                while completed_threads < len(threads):
                    # 检查已完成的线程数
                    completed_threads = sum(1 for t in threads if not t.is_alive())
                    progress_value = int((completed_threads / len(threads)) * 100)
                    progress_bar['value'] = progress_value
                    progress_label.config(text=f"{progress_value}%")
                    progress_window.title(f"提取章节目录 ({completed_threads}/{len(threads)} 线程)")
                    progress_window.update()
                    time.sleep(0.1)  # 避免过度消耗CPU
                
                # 等待所有线程完成
                for thread in threads:
                    thread.join()
                
                # 收集所有结果
                while not result_queue.empty():
                    self.chapter_positions.extend(result_queue.get())
                
                # 按位置排序章节
                self.chapter_positions.sort(key=lambda x: int(x[1].split('.')[0]))
            
            # 关闭进度窗口
            progress_window.destroy()
            
            self.log(f"已提取 {len(self.chapter_positions)} 个章节")
            
        except Exception as e:
            self.log(f"提取章节目录时出错: {str(e)}")
            # 如果有进度窗口，关闭它
            if 'progress_window' in locals() and progress_window.winfo_exists():
                progress_window.destroy()
    
    def load_large_file(self, file_path, chunk_size=100000):
        """分块加载大文件
        
        Args:
            file_path: 文件路径
            chunk_size: 每次读取的字符数，默认10万字符
        """
        try:
            # 获取文件大小（MB）
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            # 清空章节目录数据，确保目录与新文件同步
            self.chapter_positions = []
            
            # 对于超大文件（>20MB）显示警告
            if file_size_mb > 20:
                if not messagebox.askyesno("文件过大", 
                                          f"文件大小为 {file_size_mb:.2f} MB，加载可能需要较长时间并可能导致程序暂时无响应。\n\n是否继续加载？"):
                    self.log("用户取消了大文件加载")
                    return
            
            # 创建加载进度窗口
            progress_window = tk.Toplevel(self.root)
            progress_window.title("加载文件")
            progress_window.geometry("400x150")
            progress_window.transient(self.root)  # 设置为主窗口的子窗口
            progress_window.grab_set()  # 模态对话框
            
            # 添加进度条和标签
            ttk.Label(progress_window, text=f"正在加载文件 ({file_size_mb:.2f} MB)，请稍候...").pack(pady=10)
            progress_bar = ttk.Progressbar(progress_window, orient=tk.HORIZONTAL, length=350, mode='determinate')
            progress_bar.pack(pady=10)
            progress_label = ttk.Label(progress_window, text="0%")
            progress_label.pack(pady=5)
            
            # 获取文件总大小
            file_size = os.path.getsize(file_path)
            total_chunks = file_size // chunk_size + (1 if file_size % chunk_size else 0)
            
            self.log(f"开始分块加载文件: {file_path}，总块数: {total_chunks}")
            
            # 分块读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                chunk_count = 0
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    # 更新进度条
                    chunk_count += 1
                    progress_value = int((chunk_count / total_chunks) * 100)
                    progress_bar['value'] = progress_value
                    progress_label.config(text=f"{progress_value}%")
                    progress_window.update()
                    
                    # 将内容添加到预览文本框
                    self.preview_text.insert(tk.END, chunk)
                    
                    # 每5个块更新一次日志，避免日志过多
                    if chunk_count % 5 == 0 or chunk_count == total_chunks:
                        self.log(f"已加载 {chunk_count}/{total_chunks} 块 ({progress_value}%)")
                    
                    # 每次加载后更新UI
                    self.root.update_idletasks()
            
            # 关闭进度窗口
            progress_window.destroy()
            
            self.log(f"文件加载完成: {file_path}")
            
            # 不再自动提取章节目录，只在用户点击更新目录按钮时更新
            
            # 确保预览文本框滚动到顶部
            self.preview_text.see("1.0")
            
        except Exception as e:
            self.log(f"分块加载文件时出错: {str(e)}")
            messagebox.showerror("错误", f"分块加载文件时出错: {str(e)}")
            # 如果有进度窗口，关闭它
            if 'progress_window' in locals() and progress_window.winfo_exists():
                progress_window.destroy()
                
    def load_preview_file(self, filepath):
        """加载文件到预览窗口"""
        try:
            # 检查文件大小
            file_size = os.path.getsize(filepath)
            self.log(f"文件大小: {file_size / 1024:.2f} KB")
            
            # 清空预览文本
            self.preview_text.delete("1.0", tk.END)
            
            # 如果文件较大，分块读取
            if file_size > 1024 * 1024:  # 大于1MB
                self.log("文件较大，分块加载中...")
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    chunk_size = 1024 * 100  # 100KB
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        self.preview_text.insert(tk.END, chunk)
                        self.root.update()  # 更新UI，防止界面卡死
            else:
                # 小文件直接读取
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    self.preview_text.insert(tk.END, content)
            
            # 自动应用显示设置
            if self.display_settings is None:
                from display_settings import DisplaySettings
                self.display_settings = DisplaySettings(self.root, self.preview_text, apply_callback=self.apply_display_settings)
            self.display_settings.apply_settings_to_preview()
            self.apply_display_settings()
            
            # 更新章节目录
            self.update_chapter_toc()
            
            self.log(f"已加载文件: {filepath}")
            return True
        except Exception as e:
            self.log(f"加载文件出错: {str(e)}")
            return False
    
    def show_search_replace(self):
        """显示查找替换对话框"""
        # 创建查找替换对话框
        search_window = tk.Toplevel(self.root)
        search_window.title("查找替换")
        search_window.geometry("400x200")
        search_window.transient(self.root)  # 设置为主窗口的子窗口
        search_window.grab_set()  # 模态对话框
        
        # 创建高亮标签
        self.preview_text.tag_configure("search_highlight", background="yellow", foreground="black")
        
        # 创建主框架
        main_frame = ttk.Frame(search_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加查找框
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="查找内容:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # 添加替换框
        replace_frame = ttk.Frame(main_frame)
        replace_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(replace_frame, text="替换内容:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        replace_var = tk.StringVar()
        replace_entry = ttk.Entry(replace_frame, textvariable=replace_var, width=30)
        replace_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # 添加选项框架
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=5)
        
        # 区分大小写选项
        case_sensitive_var = tk.BooleanVar(value=False)
        case_check = ttk.Checkbutton(options_frame, text="区分大小写", variable=case_sensitive_var)
        case_check.pack(side=tk.LEFT, padx=5)
        
        # 添加按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 查找下一个函数
        def find_next():
            search_text = search_var.get()
            if not search_text:
                return
                
            # 清除之前的高亮
            self.preview_text.tag_remove("search_highlight", "1.0", tk.END)
                
            # 获取当前光标位置
            current_pos = self.preview_text.index(tk.INSERT)
            
            # 设置搜索选项
            search_options = ""
            if not case_sensitive_var.get():
                search_options = "nocase"
            
            # 从当前位置开始查找
            pos = self.preview_text.search(search_text, current_pos, stopindex=tk.END, nocase=(not case_sensitive_var.get()))
            
            if not pos:
                # 如果没找到，从头开始查找
                pos = self.preview_text.search(search_text, "1.0", stopindex=tk.END, nocase=(not case_sensitive_var.get()))
            
            if pos:
                # 计算结束位置
                end_pos = f"{pos}+{len(search_text)}c"
                
                # 选中找到的文本并高亮显示
                self.preview_text.tag_remove("sel", "1.0", tk.END)
                self.preview_text.tag_add("sel", pos, end_pos)
                self.preview_text.tag_add("search_highlight", pos, end_pos)
                self.preview_text.mark_set(tk.INSERT, end_pos)
                self.preview_text.see(pos)
                self.preview_text.focus_set()
            else:
                messagebox.showinfo("查找", f"找不到 '{search_text}'")
        
        # 替换函数
        def replace():
            if self.preview_text.tag_ranges("sel"):
                self.preview_text.delete(tk.SEL_FIRST, tk.SEL_LAST)
                self.preview_text.insert(tk.INSERT, replace_var.get())
                find_next()  # 查找下一个
        
        # 替换全部函数
        def replace_all():
            search_text = search_var.get()
            replace_text = replace_var.get()
            
            if not search_text:
                return
                
            count = 0
            current_pos = "1.0"
            
            # 清除之前的高亮
            self.preview_text.tag_remove("search_highlight", "1.0", tk.END)
            
            # 禁用文本框编辑
            self.preview_text.config(state=tk.NORMAL)
            
            while True:
                # 查找下一个匹配项
                pos = self.preview_text.search(search_text, current_pos, stopindex=tk.END, nocase=(not case_sensitive_var.get()))
                
                if not pos:
                    break
                
                # 计算结束位置
                end_pos = f"{pos}+{len(search_text)}c"
                
                # 替换文本
                self.preview_text.delete(pos, end_pos)
                self.preview_text.insert(pos, replace_text)
                
                # 高亮显示替换后的文本
                new_end_pos = f"{pos}+{len(replace_text)}c"
                self.preview_text.tag_add("search_highlight", pos, new_end_pos)
                
                # 更新当前位置为替换后的位置
                current_pos = new_end_pos
                count += 1
            
            # 恢复文本框编辑
            self.preview_text.config(state=tk.NORMAL)
            
            if count > 0:
                messagebox.showinfo("替换完成", f"共替换了 {count} 处匹配项")
            else:
                messagebox.showinfo("替换", f"找不到 '{search_text}'")
        
        # 添加按钮
        ttk.Button(button_frame, text="查找下一个", command=find_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="替换", command=replace).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="全部替换", command=replace_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=search_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 设置焦点到查找输入框
        search_entry.focus_set()
        
        # 绑定回车键到查找下一个
        search_entry.bind("<Return>", lambda e: find_next())
        replace_entry.bind("<Return>", lambda e: replace())
    
    def save_preview_content(self, target_file=None):
        """保存预览窗口中的内容"""
        # 获取当前文件路径
        current_file = target_file if target_file else self.output_path.get().strip()
        
        if not current_file:
            # 如果没有设置文件路径，提示用户选择保存位置
            current_file = filedialog.asksaveasfilename(title="保存文件", defaultextension=".txt", 
                                                    filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
            if not current_file:
                return  # 用户取消了操作
            self.output_path.delete(0, tk.END)
            self.output_path.insert(0, current_file)
        
        try:
            # 获取预览文本内容
            content = self.preview_text.get(1.0, tk.END)
            
            # 保存到文件
            with open(current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log(f"已保存文件: {current_file}")
            messagebox.showinfo("保存成功", f"文件已保存到: {current_file}")
            
            # 不再自动提取章节目录，只在用户点击更新目录按钮时更新
            
            return True
        except Exception as e:
            self.log(f"保存文件时出错: {str(e)}")
            messagebox.showerror("保存失败", f"保存文件时出错: {str(e)}")
            return False
    
    def update_chapter_toc(self):
        """强制更新章节目录"""
        current_content = self.preview_text.get("1.0", tk.END)
        self.log("强制更新章节目录")
        self.extract_chapter_toc(current_content)
        
        # 如果目录已显示，则刷新目录内容
        if self.toc_visible and hasattr(self, 'toc_frame') and self.toc_frame.winfo_exists():
            self.toggle_chapter_toc()
            self.toggle_chapter_toc()
            self.log("目录内容已更新")
        else:
            # 只记录日志，不显示提示消息
            self.log("章节目录已更新")
    
    def toggle_chapter_toc(self):
        """切换章节目录显示"""
        # 如果章节位置为空，自动更新目录
        if not self.chapter_positions:
            current_content = self.preview_text.get("1.0", tk.END)
            self.log("章节目录为空，自动更新目录...")
            self.extract_chapter_toc(current_content)
            if not self.chapter_positions:  # 如果更新后仍为空
                messagebox.showinfo("提示", "无法提取章节目录，请检查文本内容")
                return
        
        if self.toc_visible:
            # 如果目录已显示，则隐藏
            self.toc_frame.pack_forget()
            self.toc_visible = False
        else:
            # 如果目录未显示，则显示
            # 清空之前的内容
            for widget in self.toc_frame.winfo_children():
                widget.destroy()
            
            # 创建目录内容
            # 添加搜索框
            search_frame = ttk.Frame(self.toc_frame)
            search_frame.pack(fill=tk.X, pady=(5, 10))
            
            ttk.Label(search_frame, text="搜索章节:").pack(side=tk.LEFT, padx=(0, 5))
            search_var = tk.StringVar()
            search_entry = ttk.Entry(search_frame, textvariable=search_var, width=20)
            search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # 创建滚动列表框
            list_frame = ttk.Frame(self.toc_frame)
            list_frame.pack(fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 创建列表框
            listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("SimSun", 10))
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=listbox.yview)
            
            # 添加章节到列表
            for i, (chapter, _) in enumerate(self.chapter_positions):
                listbox.insert(tk.END, f"{i+1}. {chapter}")
            
            # 双击章节跳转到对应位置
            def on_chapter_select(event):
                # 获取选中的索引
                selection = listbox.curselection()
                if selection:
                    index = selection[0]
                    # 不再自动提取章节目录，只在用户点击更新目录按钮时更新
                    # 直接使用当前的章节位置信息
                    # 跳转到对应位置
                    if index < len(self.chapter_positions):
                        _, position = self.chapter_positions[index]
                        self.preview_text.see(position)
                        # 高亮显示该行
                        self.preview_text.tag_remove("highlight", "1.0", tk.END)
                        line_end = self.preview_text.index(f"{position} lineend")
                        self.preview_text.tag_add("highlight", position, line_end)
                        self.preview_text.tag_config("highlight", background="#FFFF00")
            
            # 绑定双击事件
            listbox.bind("<Double-1>", on_chapter_select)
            
            # 添加按钮框架
            button_frame = ttk.Frame(self.toc_frame)
            button_frame.pack(fill=tk.X, pady=(10, 5))
            
            # 添加跳转到开头和结尾的按钮
            ttk.Button(button_frame, text="跳转到开头", 
                      command=lambda: self.preview_text.see("1.0")).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="跳转到结尾", 
                      command=lambda: self.preview_text.see(tk.END)).pack(side=tk.LEFT, padx=5)
            
            # 双击章节跳转到对应位置
            def on_chapter_select(event):
                selection = listbox.curselection()
                if selection:
                    index = selection[0]
                    _, position = self.chapter_positions[index]
                    self.preview_text.see(position)
                    # 高亮显示选中的章节行
                    self.preview_text.tag_remove("highlight", "1.0", tk.END)
                    line_end = self.preview_text.index(f"{position} lineend")
                    self.preview_text.tag_add("highlight", position, line_end)
                    self.preview_text.tag_config("highlight", background="#FFFF00")
                    # 将焦点转回预览窗口
                    self.preview_text.focus_set()
            
            # 搜索功能
            def search_chapters(event=None):
                search_text = search_var.get().lower()
                listbox.selection_clear(0, tk.END)
                
                if not search_text:
                    # 如果搜索框为空，显示所有章节
                    listbox.delete(0, tk.END)
                    for i, (chapter, _) in enumerate(self.chapter_positions):
                        listbox.insert(tk.END, f"{i+1}. {chapter}")
                    return
                
                # 清空列表框
                listbox.delete(0, tk.END)
                
                # 添加匹配的章节
                for i, (chapter, position) in enumerate(self.chapter_positions):
                    if search_text in chapter.lower():
                        listbox.insert(tk.END, f"{i+1}. {chapter}")
                
                # 如果有匹配项，选中第一项
                if listbox.size() > 0:
                    listbox.selection_set(0)
                    listbox.see(0)
            
            # 绑定搜索事件
            search_entry.bind("<KeyRelease>", search_chapters)
            search_entry.bind("<Return>", lambda e: on_chapter_select(None) if listbox.curselection() else None)
            
            # 绑定双击事件
            listbox.bind("<Double-Button-1>", on_chapter_select)
            # 绑定回车键
            listbox.bind("<Return>", on_chapter_select)
            
            # 设置焦点到搜索框
            search_entry.focus_set()
            
            # 显示目录框架在预览文本右侧
            self.toc_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0), pady=5)
            self.toc_visible = True
    
    def show_chapter_toc(self):
        """显示独立章节目录对话框（保留原方法以兼容旧代码）"""
        self.toggle_chapter_toc()
        
    def toggle_preview(self):
        """切换预览功能"""
        if self.preview_var.get():
            # 检查预览文本是否被修改过
            try:
                current_file = self.output_path.get().strip()
                if os.path.exists(current_file):
                    with open(current_file, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    preview_content = self.preview_text.get(1.0, tk.END)
                    
                    # 比较文件内容和预览内容是否不同（去除可能的尾部换行符差异）
                    if file_content.rstrip() != preview_content.rstrip():
                        # 询问用户是否保存修改
                        response = messagebox.askyesnocancel("保存修改", "预览内容已被修改，是否覆盖保存？")
                        
                        if response is None:  # 用户点击取消，不关闭预览
                            return
                        elif response:  # 用户点击是，保存到当前文件
                            self.save_preview_content()
                        else:  # 用户点击否，询问是否保存为新文件
                            save_as = messagebox.askyesno("另存为", "是否将修改保存为新文件？")
                            if save_as:
                                new_file = filedialog.asksaveasfilename(title="另存为", defaultextension=".txt", 
                                                                    filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
                                if new_file:  # 用户选择了保存位置
                                    try:
                                        with open(new_file, 'w', encoding='utf-8') as f:
                                            f.write(preview_content)
                                        self.log(f"已另存为: {new_file}")
                                    except Exception as e:
                                        self.log(f"保存文件时出错: {str(e)}")
                                        messagebox.showerror("保存失败", f"保存文件时出错: {str(e)}")
            except Exception as e:
                self.log(f"检查文件修改时出错: {str(e)}")
            
            # 关闭预览
            self.preview_var.set(False)
            self.preview_btn.config(text="预览")
            self.preview_frame.pack_forget()
            self.root.geometry("700x800")
            
            # 如果目录窗口是打开的，也关闭它
            if self.toc_visible:
                self.toc_frame.pack_forget()
                self.toc_visible = False
        else:
            # 打开预览
            self.preview_var.set(True)
            self.preview_btn.config(text="关闭预览")
            
            # 调整主窗口大小，扩大显示预览的面积
            self.root.geometry("1500x800")
            
            # 确保预览框架从主窗口中移除（如果之前已添加）
            self.preview_frame.pack_forget()
            
            # 重新配置主窗口布局，保持左侧功能区宽度不变
            self.main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
            
            # 显示预览框架在右侧，并扩大预览区域
            self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 尝试加载最后保存的文件内容
            output_path = self.output_path.get().strip()
            if os.path.exists(output_path):
                try:
                    # 获取文件大小
                    file_size = os.path.getsize(output_path) / (1024 * 1024)  # 转换为MB
                    self.log(f"预览文件大小: {file_size:.2f} MB")
                    
                    # 清空预览文本框
                    self.preview_text.delete(1.0, tk.END)
                    
                    # 清空章节目录数据，确保目录与新文件同步
                    self.chapter_positions = []
                    
                    # 如果文件大于2MB，使用分块加载
                    if file_size > 2:
                        self.load_large_file(output_path)
                        # 大文件加载完成后应用显示设置
                        if self.display_settings is None:
                            from display_settings import DisplaySettings
                            self.display_settings = DisplaySettings(self.root, self.preview_text, apply_callback=self.apply_display_settings)
                        self.display_settings.apply_settings_to_preview()
                        self.apply_display_settings()
                    else:
                        # 小文件直接加载
                        with open(output_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        self.preview_text.insert(tk.END, content)
                        self.log(f"已加载预览文件: {output_path}")
                        
                        # 确保每次加载新文件后都应用显示设置
                        if self.display_settings is None:
                            from display_settings import DisplaySettings
                            self.display_settings = DisplaySettings(self.root, self.preview_text, apply_callback=self.apply_display_settings)
                        self.display_settings.apply_settings_to_preview()
                        self.apply_display_settings()
                    
                    # 不再自动提取章节目录，只在用户点击更新目录按钮时更新
                   # self.log("提示：如需查看章节目录，请点击"更新目录"按钮")
                except Exception as e:
                    self.log(f"加载预览文件时出错: {str(e)}")
                    messagebox.showerror("错误", f"加载预览文件时出错: {str(e)}")
            else:
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(tk.END, "没有可预览的文件。请先提取或应用规则生成文件。")
                
            # 确保预览文本框获得焦点并滚动到顶部
            self.preview_text.focus_set()
            self.preview_text.see("1.0")
    
    def create_backup(self, file_path):
        """创建文件备份
        
        参数:
            file_path: 需要备份的文件路径
        """
        try:
            # 获取备份次数设置
            backup_count = self.backup_count_var.get()
            if backup_count <= 0:
                return  # 如果备份次数设置为0，不创建备份
                
            # 确保文件存在
            if not os.path.exists(file_path):
                self.log(f"无法创建备份: 文件 {file_path} 不存在")
                return
                
            # 获取文件名和扩展名
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            name, ext = os.path.splitext(file_name)
            
            # 创建备份文件名，格式为: 原文件名+当前时间.bak
            timestamp = time.strftime("%H%M%S")
            backup_name = f"{name}{timestamp}.bak"
            backup_path = os.path.join(file_dir, backup_name)
            
            # 复制文件创建备份
            import shutil
            shutil.copy2(file_path, backup_path)
            self.log(f"已创建备份: {backup_name}")
            
            # 获取当前目录中的所有备份文件
            backup_files = []
            for f in os.listdir(file_dir):
                if f.startswith(name) and f.endswith(".bak"):
                    backup_path = os.path.join(file_dir, f)
                    backup_files.append((f, os.path.getmtime(backup_path), backup_path))
            
            # 如果备份文件数量超过设置的备份次数，删除最旧的备份
            if len(backup_files) > backup_count:
                # 按修改时间排序
                backup_files.sort(key=lambda x: x[1])
                # 删除最旧的文件，直到数量符合设置
                for i in range(len(backup_files) - backup_count):
                    try:
                        os.remove(backup_files[i][2])
                        self.log(f"已删除旧备份: {backup_files[i][0]}")
                    except Exception as e:
                        self.log(f"删除旧备份时出错: {str(e)}")
                        
        except Exception as e:
            self.log(f"创建备份时出错: {str(e)}")
            messagebox.showerror("备份错误", f"创建备份时出错: {str(e)}")
    
    def restore_backup(self):
        """还原备份文件"""
        try:
            # 获取当前文件路径
            current_file = self.output_path.get().strip()
            if not current_file:
                messagebox.showerror("错误", "请先设置输出文件路径")
                return
                
            file_dir = os.path.dirname(current_file)
            file_name = os.path.basename(current_file)
            name, ext = os.path.splitext(file_name)
            
            # 查找所有备份文件
            backup_files = []
            for f in os.listdir(file_dir):
                if f.startswith(name) and f.endswith(".bak"):
                    backup_path = os.path.join(file_dir, f)
                    backup_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(backup_path)))
                    backup_files.append((f, backup_time, backup_path))
            
            if not backup_files:
                messagebox.showinfo("提示", "没有找到可用的备份文件")
                return
                
            # 按修改时间排序，最新的排在前面
            backup_files.sort(key=lambda x: os.path.getmtime(x[2]), reverse=True)
            
            # 创建备份选择对话框
            backup_window = tk.Toplevel(self.root)
            backup_window.title("选择要还原的备份")
            backup_window.geometry("500x300")
            backup_window.transient(self.root)  # 设置为主窗口的子窗口
            backup_window.grab_set()  # 模态对话框
            
            ttk.Label(backup_window, text="请选择要还原的备份文件:").pack(pady=10)
            
            # 创建列表框显示备份文件
            backup_frame = ttk.Frame(backup_window)
            backup_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            columns = ("备份文件", "备份时间")
            backup_tree = ttk.Treeview(backup_frame, columns=columns, show="headings")
            for col in columns:
                backup_tree.heading(col, text=col)
                backup_tree.column(col, width=200)
            
            # 添加滚动条
            scrollbar = ttk.Scrollbar(backup_frame, orient=tk.VERTICAL, command=backup_tree.yview)
            backup_tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # 添加备份文件到列表
            for i, (file, time_str, _) in enumerate(backup_files):
                backup_tree.insert("", tk.END, values=(file, time_str))
            
            # 如果有备份文件，默认选中第一个（最新的）
            if backup_files:
                backup_tree.selection_set(backup_tree.get_children()[0])
            
            # 添加按钮框架
            btn_frame = ttk.Frame(backup_window)
            btn_frame.pack(fill=tk.X, pady=10)
            
            # 定义还原操作
            def do_restore():
                selected_items = backup_tree.selection()
                if not selected_items:
                    messagebox.showwarning("警告", "请选择一个备份文件")
                    return
                    
                selected_idx = backup_tree.index(selected_items[0])
                selected_backup = backup_files[selected_idx]
                
                # 确认还原
                if messagebox.askyesno("确认还原", f"确定要还原备份文件 {selected_backup[0]} 吗？\n这将覆盖当前文件 {file_name}"):
                    try:
                        # 如果当前文件存在且备份次数大于0，先创建当前文件的备份
                        if os.path.exists(current_file) and self.backup_count_var.get() > 0:
                            self.create_backup(current_file)
                            
                        # 复制备份文件到当前文件
                        import shutil
                        shutil.copy2(selected_backup[2], current_file)
                        self.log(f"已还原备份: {selected_backup[0]} 到 {file_name}")
                        messagebox.showinfo("还原成功", f"已成功还原备份文件 {selected_backup[0]}")
                        
                        # 如果预览窗口已打开，更新预览内容
                        if self.preview_var.get():
                            try:
                                with open(current_file, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                self.preview_text.delete(1.0, tk.END)
                                self.preview_text.insert(tk.END, content)
                                self.log("已更新预览内容")
                            except Exception as e:
                                self.log(f"更新预览内容时出错: {str(e)}")
                        
                        # 关闭备份选择窗口
                        backup_window.destroy()
                    except Exception as e:
                        self.log(f"还原备份时出错: {str(e)}")
                        messagebox.showerror("还原错误", f"还原备份时出错: {str(e)}")
            
            # 添加还原和取消按钮
            ttk.Button(btn_frame, text="还原", command=do_restore).pack(side=tk.LEFT, padx=10)
            ttk.Button(btn_frame, text="取消", command=backup_window.destroy).pack(side=tk.RIGHT, padx=10)
            
            # 双击列表项也可以还原
            backup_tree.bind("<Double-1>", lambda e: do_restore())
            
        except Exception as e:
            self.log(f"打开备份选择窗口时出错: {str(e)}")
            messagebox.showerror("错误", f"打开备份选择窗口时出错: {str(e)}")
    
    def apply_rules_to_file(self):
        """对已有文件应用自定义规则"""
        if self.is_running:
            messagebox.showwarning("警告", "已有任务正在运行！")
            return
        
        # 获取当前设置的输出文件路径作为输入和输出文件
        output_path = self.output_path.get().strip()
        input_file = output_path
        
        # 检查文件是否存在
        if not os.path.exists(input_file):
            messagebox.showerror("错误", f"文件 {input_file} 不存在！")
            return
        
        # 询问是否覆盖保存
        overwrite = messagebox.askyesno("确认", f"将使用当前文件 {output_path} 应用规则并覆盖保存，是否继续？")
        if not overwrite:
            # 用户选择不覆盖，提示输入新文件名
            new_file = filedialog.asksaveasfilename(title="另存为", defaultextension=".txt", 
                                                 filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
            if not new_file:  # 用户取消了另存为对话框
                return
            output_file = new_file
            # 更新输出路径显示
            self.output_path.delete(0, tk.END)
            self.output_path.insert(0, output_file)
        else:
            output_file = output_path
            # 如果覆盖保存并且备份次数大于0，则创建备份
            backup_count = self.backup_count_var.get()
            if backup_count > 0 and os.path.exists(output_file):
                self.backup_file(output_file)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("错误", f"创建输出目录失败: {str(e)}")
                return
        
        # 开始处理
        self.is_running = True
        self.extract_btn.config(state=tk.DISABLED)
        self.extract_with_rules_btn.config(state=tk.DISABLED)
        self.apply_rules_btn.config(state=tk.DISABLED)
        
        # 创建处理线程
        process_thread = threading.Thread(target=self.process_file_with_rules, args=(input_file, output_file))
        process_thread.daemon = True
        process_thread.start()
        
        # 创建一个监视线程，在处理完成后自动更新目录
        def monitor_process():
            process_thread.join()  # 等待处理线程完成
            if self.preview_var.get() and not self.stop_flag:  # 如果预览窗口打开且未被停止
                self.root.after(500, self.update_chapter_toc)  # 使用after方法在主线程中更新目录
        
        monitor_thread = threading.Thread(target=monitor_process)
        monitor_thread.daemon = True
        monitor_thread.start()
    
    def stop_extraction(self):
        """停止程序并重新启动"""
        if messagebox.askyesno("确认", "确定要结束程序并重新启动吗？"):
            self.log("正在重启程序...")
            # 如果有正在运行的任务，先停止它
            if self.is_running:
                self.stop_flag = True
                self.is_running = False
                self.log("正在停止当前任务...")
            
            # 获取当前程序路径
            import sys
            program_path = sys.executable
            script_path = sys.argv[0]
            
            # 使用subprocess启动新进程
            import subprocess
            subprocess.Popen([program_path, script_path])
            
            # 关闭当前程序
            self.root.destroy()
        else:
            self.log("取消重启")
            
        # 恢复按钮状态（如果没有重启）
        if self.is_running:
            self.extract_btn.config(state=tk.NORMAL)
        self.extract_with_rules_btn.config(state=tk.NORMAL)
        self.apply_rules_btn.config(state=tk.NORMAL)
        
        # 强制中断所有线程
        try:
            # 使用sys._current_frames()获取所有线程的堆栈帧
            import sys
            import _thread
            
            # 尝试终止所有工作线程
            for thread_id, frame in sys._current_frames().items():
                if thread_id != _thread.get_ident():  # 不终止主线程
                    try:
                        # 设置线程的异常状态，使其在下一次检查时退出
                        _thread.interrupt_main()
                    except:
                        pass
            
            # 终止所有非守护线程
            for thread in threading.enumerate():
                if thread != threading.current_thread() and not thread.daemon:
                    try:
                        # 尝试终止线程
                        thread._stop()
                    except:
                        pass
            
            self.log("已强制中断任务执行")
            messagebox.showinfo("停止", "已成功停止任务执行。")
        except Exception as e:
            self.log(f"中断任务时出错: {str(e)}")
        
        # 重置进度条
        self.progress_bar['value'] = 0
        
        # 不再需要等待线程
        # 直接设置标志位
        self.stop_flag = False
    
    def wait_for_stop(self):
        """等待停止完成"""
        # 等待当前操作完成
        while self.is_running and self.stop_flag:
            time.sleep(0.1)
        
        if self.stop_flag:
            self.is_running = False
            self.stop_flag = False
            self.log("处理已停止！")
            self.progress_bar['value'] = 0
            self.extract_btn.config(state=tk.NORMAL)
            self.extract_with_rules_btn.config(state=tk.NORMAL)
            self.apply_rules_btn.config(state=tk.NORMAL)
    
    def create_backup(self, file_path):
        """创建文件备份
        
        Args:
            file_path: 要备份的文件路径
        """
        try:
            if not os.path.exists(file_path):
                self.log(f"文件 {file_path} 不存在，无法创建备份")
                return
            
            # 获取文件目录和文件名
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            file_name_without_ext, file_ext = os.path.splitext(file_name)
            
            # 创建备份文件名，格式为：原文件名+当前时间.bak
            current_time = time.strftime("%H%M%S")
            backup_file_name = f"{file_name_without_ext}{current_time}.bak"
            backup_file_path = os.path.join(file_dir, backup_file_name)
            
            # 复制文件创建备份
            import shutil
            shutil.copy2(file_path, backup_file_path)
            
            self.log(f"已创建备份: {backup_file_name}")
            
            # 管理备份文件数量
            self.manage_backup_files(file_dir, file_name_without_ext)
            
        except Exception as e:
            self.log(f"创建备份时出错: {str(e)}")
    
    def manage_backup_files(self, directory, file_prefix):
        """管理备份文件数量，删除超过设定数量的最早备份文件
        
        Args:
            directory: 备份文件所在目录
            file_prefix: 备份文件前缀（原文件名）
        """
        try:
            # 获取备份次数设置
            backup_count = self.backup_count_var.get()
            if backup_count <= 0:
                return
            
            # 查找所有匹配的备份文件
            backup_files = []
            for file in os.listdir(directory):
                if file.startswith(file_prefix) and file.endswith(".bak"):
                    file_path = os.path.join(directory, file)
                    # 获取文件修改时间
                    mod_time = os.path.getmtime(file_path)
                    backup_files.append((file_path, mod_time))
            
            # 按修改时间排序（最早的在前）
            backup_files.sort(key=lambda x: x[1])
            
            # 如果备份文件数量超过设定值，删除最早的文件
            files_to_delete = len(backup_files) - backup_count
            if files_to_delete > 0:
                for i in range(files_to_delete):
                    file_to_delete = backup_files[i][0]
                    try:
                        os.remove(file_to_delete)
                        self.log(f"已删除旧备份: {os.path.basename(file_to_delete)}")
                    except Exception as e:
                        self.log(f"删除旧备份时出错: {str(e)}")
        
        except Exception as e:
            self.log(f"管理备份文件时出错: {str(e)}")
    
    def backup_file(self, file_path):
        """备份文件
        
        Args:
            file_path: 需要备份的文件路径
        
        Returns:
            备份文件路径或None（如果备份失败）
        """
        try:
            # 检查备份次数设置
            backup_count = self.backup_count_var.get()
            if backup_count <= 0:
                self.log("备份次数设置为0，跳过备份")
                return None
                
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.log(f"文件不存在，无法备份: {file_path}")
                return None
                
            # 创建备份文件名（原文件名+当前时间）
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            file_name_without_ext, file_ext = os.path.splitext(file_name)
            
            # 使用当前时间创建备份文件名
            current_time = time.strftime("%H%M%S")
            backup_file_name = f"{file_name_without_ext}{current_time}.bak"
            backup_file_path = os.path.join(file_dir, backup_file_name)
            
            # 复制文件
            import shutil
            shutil.copy2(file_path, backup_file_path)
            self.log(f"已创建备份: {backup_file_name}")
            
            # 管理备份文件数量
            self.manage_backup_files(file_path)
            
            return backup_file_path
            
        except Exception as e:
            self.log(f"备份文件时出错: {str(e)}")
            return None
            
    def manage_backup_files(self, original_file_path):
        """管理备份文件数量，删除多余的旧备份"""
        try:
            backup_count = self.backup_count_var.get()
            if backup_count <= 0:
                return
                
            # 获取文件目录和文件名
            file_dir = os.path.dirname(original_file_path)
            file_name = os.path.basename(original_file_path)
            file_name_without_ext, file_ext = os.path.splitext(file_name)
            
            # 查找所有匹配的备份文件
            backup_files = []
            for file in os.listdir(file_dir):
                if file.startswith(file_name_without_ext) and file.endswith(".bak"):
                    full_path = os.path.join(file_dir, file)
                    # 获取文件修改时间
                    mod_time = os.path.getmtime(full_path)
                    backup_files.append((full_path, mod_time))
            
            # 按修改时间排序（最旧的在前面）
            backup_files.sort(key=lambda x: x[1])
            
            # 如果备份文件数量超过设置的备份次数，删除多余的旧备份
            files_to_delete = max(0, len(backup_files) - backup_count)
            if files_to_delete > 0:
                for i in range(files_to_delete):
                    file_to_delete = backup_files[i][0]
                    try:
                        os.remove(file_to_delete)
                        self.log(f"已删除旧备份: {os.path.basename(file_to_delete)}")
                    except Exception as e:
                        self.log(f"删除旧备份时出错: {str(e)}")
        
        except Exception as e:
            self.log(f"管理备份文件时出错: {str(e)}")
    
    def restore_backup(self):
        """还原备份文件"""
        try:
            # 获取当前输出文件路径
            current_file = self.output_path.get().strip()
            if not current_file:
                messagebox.showerror("错误", "请先设置输出文件路径！")
                return
            
            # 获取文件目录和文件名
            file_dir = os.path.dirname(current_file)
            file_name = os.path.basename(current_file)
            file_name_without_ext, file_ext = os.path.splitext(file_name)
            
            # 查找所有匹配的备份文件
            backup_files = []
            for file in os.listdir(file_dir):
                if file.startswith(file_name_without_ext) and file.endswith(".bak"):
                    full_path = os.path.join(file_dir, file)
                    # 获取文件修改时间
                    mod_time = os.path.getmtime(full_path)
                    # 格式化时间为可读格式
                    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mod_time))
                    backup_files.append((full_path, mod_time, time_str, file))
            
            if not backup_files:
                messagebox.showinfo("提示", "没有找到可用的备份文件！")
                return
                
            # 按修改时间排序（最新的在前面）
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 创建备份选择窗口
            backup_window = tk.Toplevel(self.root)
            backup_window.title("选择要还原的备份")
            backup_window.geometry("500x300")
            backup_window.transient(self.root)  # 设置为主窗口的子窗口
            backup_window.grab_set()  # 模态对话框
            
            # 添加说明标签
            ttk.Label(backup_window, text="请选择要还原的备份文件：").pack(pady=10)
            
            # 创建列表框架
            list_frame = ttk.Frame(backup_window)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # 创建带滚动条的列表框
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            backup_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("SimSun", 10))
            backup_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=backup_listbox.yview)
            
            # 填充列表
            for i, (path, mod_time, time_str, file_name) in enumerate(backup_files):
                backup_listbox.insert(tk.END, f"{file_name} - {time_str}")
            
            # 选择第一项
            if backup_listbox.size() > 0:
                backup_listbox.selection_set(0)
            
            # 按钮框架
            button_frame = ttk.Frame(backup_window)
            button_frame.pack(fill=tk.X, pady=10)
            
            # 定义还原操作
            def do_restore():
                selected_idx = backup_listbox.curselection()
                if not selected_idx:
                    messagebox.showwarning("警告", "请选择一个备份文件！")
                    return
                    
                selected_backup = backup_files[selected_idx[0]]
                backup_path = selected_backup[0]
                
                # 确认还原
                if not messagebox.askyesno("确认", f"确定要还原到备份 {selected_backup[3]} 吗？\n这将覆盖当前文件！"):
                    return
                    
                try:
                    # 复制备份文件到原文件
                    import shutil
                    shutil.copy2(backup_path, current_file)
                    self.log(f"已还原备份: {selected_backup[3]}")
                    messagebox.showinfo("成功", "备份还原成功！")
                    
                    # 如果预览窗口已打开，更新预览内容
                    if self.preview_var.get():
                        self.preview_text.delete(1.0, tk.END)
                        try:
                            with open(current_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            self.preview_text.insert(tk.END, content)
                            self.log("已更新预览内容")
                        except Exception as e:
                            self.log(f"更新预览内容时出错: {str(e)}")
                    
                    # 关闭窗口
                    backup_window.destroy()
                    
                except Exception as e:
                    self.log(f"还原备份时出错: {str(e)}")
                    messagebox.showerror("错误", f"还原备份时出错: {str(e)}")
            
            # 添加按钮
            ttk.Button(button_frame, text="还原", command=do_restore).pack(side=tk.LEFT, padx=10)
            ttk.Button(button_frame, text="取消", command=backup_window.destroy).pack(side=tk.LEFT, padx=10)
            
        except Exception as e:
            self.log(f"还原备份时出错: {str(e)}")
            messagebox.showerror("错误", f"还原备份时出错: {str(e)}")
            for file in os.listdir(file_dir):
                if file.startswith(file_name_without_ext) and file.endswith(".bak"):
                    backup_files.append(file)
            
            if not backup_files:
                messagebox.showinfo("提示", "没有找到可用的备份文件！")
                return
            
            # 按修改时间排序（最新的在前）
            backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(file_dir, x)), reverse=True)
            
            # 创建还原对话框
            restore_window = tk.Toplevel(self.root)
            restore_window.title("还原备份")
            restore_window.geometry("500x300")
            restore_window.transient(self.root)  # 设置为主窗口的子窗口
            restore_window.grab_set()  # 模态对话框
            
            # 创建主框架
            main_frame = ttk.Frame(restore_window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(main_frame, text="请选择要还原的备份文件:").pack(anchor=tk.W, pady=5)
            
            # 创建列表框架
            list_frame = ttk.Frame(main_frame)
            list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            # 创建备份文件列表
            backup_listbox = tk.Listbox(list_frame, width=50, height=10)
            backup_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # 添加滚动条
            scrollbar = ttk.Scrollbar(list_frame, command=backup_listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            backup_listbox.config(yscrollcommand=scrollbar.set)
            
            # 填充备份文件列表
            for file in backup_files:
                file_path = os.path.join(file_dir, file)
                # 获取文件修改时间
                mod_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(file_path)))
                # 获取文件大小
                file_size = os.path.getsize(file_path) / 1024  # KB
                backup_listbox.insert(tk.END, f"{file} - {mod_time} - {file_size:.2f} KB")
            
            # 选中第一项
            if backup_files:
                backup_listbox.selection_set(0)
            
            # 添加按钮框架
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=10)
            
            # 还原函数
            def do_restore():
                selected_idx = backup_listbox.curselection()
                if not selected_idx:
                    messagebox.showwarning("警告", "请选择一个备份文件！")
                    return
                
                selected_file = backup_files[selected_idx[0]]
                backup_path = os.path.join(file_dir, selected_file)
                
                # 确认还原
                if not messagebox.askyesno("确认", f"确定要还原备份文件 {selected_file} 吗？\n这将覆盖当前文件 {file_name}！"):
                    return
                
                try:
                    # 如果当前文件存在且备份次数大于0，则先备份当前文件
                    if os.path.exists(current_file) and self.backup_count_var.get() > 0:
                        self.create_backup(current_file)
                    
                    # 复制备份文件到当前文件
                    import shutil
                    shutil.copy2(backup_path, current_file)
                    
                    self.log(f"已还原备份: {selected_file} 到 {file_name}")
                    messagebox.showinfo("完成", "备份还原成功！")
                    
                    # 如果预览窗口已打开，更新预览内容
                    if self.preview_var.get() and os.path.exists(current_file):
                        try:
                            # 获取文件大小
                            file_size = os.path.getsize(current_file) / (1024 * 1024)  # 转换为MB
                            
                            # 清空预览文本框
                            self.preview_text.delete(1.0, tk.END)
                            
                            # 如果文件大于2MB，使用分块加载
                            if file_size > 2:
                                self.load_large_file(current_file)
                            else:
                                # 小文件直接加载
                                with open(current_file, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                self.preview_text.insert(tk.END, content)
                        except Exception as e:
                            self.log(f"更新预览内容时出错: {str(e)}")
                    
                    # 关闭对话框
                    restore_window.destroy()
                    
                except Exception as e:
                    self.log(f"还原备份时出错: {str(e)}")
                    messagebox.showerror("错误", f"还原备份时出错: {str(e)}")
            
            # 添加还原按钮
            restore_btn = ttk.Button(button_frame, text="还原", command=do_restore)
            restore_btn.pack(side=tk.LEFT, padx=5)
            
            # 添加取消按钮
            cancel_btn = ttk.Button(button_frame, text="取消", command=restore_window.destroy)
            cancel_btn.pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            self.log(f"打开还原对话框时出错: {str(e)}")
            messagebox.showerror("错误", f"打开还原对话框时出错: {str(e)}")

    
    def extract_content(self, start_url, end_url, output_dir, output_filename, thread_count, delete_temp, apply_rules=False):
        """提取网页内容并合并
        
        参数:
            start_url: 开始URL
            end_url: 结束URL
            output_dir: 输出目录
            output_filename: 输出文件名
            thread_count: 线程数
            delete_temp: 是否删除临时文件
            apply_rules: 是否应用自定义规则
        """
        try:
            # 解析URL以获取范围
            urls = self.generate_urls(start_url, end_url)
            if not urls:
                self.log("无法生成URL范围，请检查输入的URL格式是否正确")
                self.is_running = False
                self.extract_btn.config(state=tk.NORMAL)
                self.extract_with_rules_btn.config(state=tk.NORMAL)
                self.apply_rules_btn.config(state=tk.NORMAL)
                return
            
            # 获取测试文件个数限制
            test_count = self.test_count_var.get()
            if test_count > 0 and test_count < len(urls):
                self.log(f"根据设置，仅下载前 {test_count} 个文件进行测试")
                urls = urls[:test_count]
            
            total_urls = len(urls)
            self.log(f"共找到 {total_urls} 个网页需要处理")
            self.progress_bar['maximum'] = total_urls
            
            # 创建线程安全的变量
            self.processed_count = 0
            self.lock = threading.Lock()
            
            # 定义工作线程函数
            def worker(url_list):
                for url_info in url_list:
                    i, url = url_info
                    try:
                        # 下载并解析网页
                        content = self.download_and_extract(url)
                        
                        # 保存为临时文件
                        filename = f"chapter_{i+1}.txt"
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        with self.lock:
                            # 使用索引作为键存储文件路径，确保后续可以按顺序合并
                            self.extracted_files[i] = filepath
                            self.processed_count += 1
                            self.log(f"正在处理 ({self.processed_count}/{total_urls}): {url}")
                            self.log(f"已保存: {filename}")
                            # 更新进度条
                            self.progress_bar['value'] = self.processed_count
                            self.root.update_idletasks()
                            
                    except Exception as e:
                        with self.lock:
                            self.processed_count += 1
                            self.log(f"处理 {url} 时出错: {str(e)}")
                            # 更新进度条
                            self.progress_bar['value'] = self.processed_count
                            self.root.update_idletasks()
            
            # 将URL列表分成多个子列表，每个线程处理一部分
            url_chunks = []
            total_urls_count = len(urls)
            
            # 确保所有URL都被分配，即使不能被线程数整除
            if total_urls_count <= thread_count:
                # 如果URL数量少于或等于线程数，每个线程处理一个URL
                for i in range(total_urls_count):
                    url_chunks.append([(i, urls[i])])
            else:
                # 计算基本的块大小和余数
                base_chunk_size = total_urls_count // thread_count
                remainder = total_urls_count % thread_count
                
                start_idx = 0
                for i in range(thread_count):
                    # 为前remainder个线程多分配一个URL
                    current_chunk_size = base_chunk_size + (1 if i < remainder else 0)
                    end_idx = start_idx + current_chunk_size
                    
                    # 创建(索引, url)元组列表
                    chunk = [(idx, urls[idx]) for idx in range(start_idx, end_idx)]
                    url_chunks.append(chunk)
                    
                    start_idx = end_idx
            
            # 启动工作线程
            threads = []
            self.log(f"启动 {len(url_chunks)} 个线程进行处理...")
            
            for i in range(len(url_chunks)):
                t = threading.Thread(target=worker, args=(url_chunks[i],))
                t.daemon = True
                threads.append(t)
                t.start()
            
            # 等待所有线程完成
            for t in threads:
                t.join()
            
            # 合并文件
            if self.extracted_files:
                self.log("正在合并文件...")
                merged_filepath = os.path.join(output_dir, output_filename)
                
                if apply_rules:
                    self.log("应用自定义规则并合并文件...")
                    self.merge_files_with_rules(self.extracted_files, merged_filepath)
                else:
                    self.log("仅合并文件，不应用规则...")
                    self.merge_files_without_rules(self.extracted_files, merged_filepath)
                
                self.log(f"合并完成: {merged_filepath}")
                
                # 根据设置删除临时文件
                if delete_temp:
                    self.log("正在删除临时文件...")
                    for file in self.extracted_files.values():
                        try:
                            os.remove(file)
                        except:
                            pass
                    self.log("临时文件已删除")
            
            self.log("全部处理完成！")
            messagebox.showinfo("完成", "小说内容提取和合并已完成！")
            
            # 如果预览窗口已打开，更新预览内容
            if self.preview_var.get() and os.path.exists(merged_filepath):
                try:
                    with open(merged_filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.preview_text.delete(1.0, tk.END)
                    self.preview_text.insert(tk.END, content)
                except Exception as e:
                    self.log(f"更新预览内容时出错: {str(e)}")
            
        except Exception as e:
            self.log(f"处理过程中发生错误: {str(e)}")
            messagebox.showerror("错误", f"处理过程中发生错误: {str(e)}")
        
        finally:
            self.is_running = False
            self.stop_flag = False
            self.extract_btn.config(state=tk.NORMAL)
            self.extract_with_rules_btn.config(state=tk.NORMAL)
            self.apply_rules_btn.config(state=tk.NORMAL)
    
    def process_file_with_rules(self, input_file, output_file):
        """对已有文件应用自定义规则"""
        # 重置停止标志
        self.stop_flag = False
        
        try:
            self.log(f"正在处理文件: {input_file}")
            self.log(f"输出文件: {output_file}")
            self.progress_bar['value'] = 0
            self.progress_bar['maximum'] = 100
            
            # 检查是否需要停止
            if self.stop_flag:
                self.log("处理已停止")
                return
            
            # 读取文件内容
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.progress_bar['value'] = 30
            self.log("文件读取完成，正在应用规则...")
            
            # 检查是否需要停止
            if self.stop_flag:
                self.log("处理已停止")
                return
            
            # 应用自定义规则
            content = self.apply_custom_rules(content)
            
            self.progress_bar['value'] = 70
            self.log("应用规则完成，正在保存文件...")
            
            # 检查是否需要停止
            if self.stop_flag:
                self.log("处理已停止")
                return
            
            # 保存处理后的内容
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.progress_bar['value'] = 100
            self.log(f"处理完成，已保存到: {output_file}")
            
            if not self.stop_flag:
                messagebox.showinfo("完成", "应用规则完成！")
            
            # 如果预览窗口已打开，更新预览内容
            if self.preview_var.get() and os.path.exists(output_file) and not self.stop_flag:
                try:
                    # 获取文件大小
                    file_size = os.path.getsize(output_file) / (1024 * 1024)  # 转换为MB
                    self.log(f"预览文件大小: {file_size:.2f} MB")
                    
                    # 清空预览文本框
                    self.preview_text.delete(1.0, tk.END)
                    
                    # 如果文件大于2MB，使用分块加载
                    if file_size > 2:
                        self.load_large_file(output_file)
                    else:
                        # 小文件直接加载
                        with open(output_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        self.preview_text.insert(tk.END, content)
                        # 不再自动提取章节目录，只在用户点击更新目录按钮时更新
                    
                    # 确保每次加载新文件后都应用显示设置
                    if self.display_settings is None:
                        from display_settings import DisplaySettings
                        self.display_settings = DisplaySettings(self.root, self.preview_text, apply_callback=self.apply_display_settings)
                    self.display_settings.apply_settings_to_preview()
                    self.apply_display_settings()
                except Exception as e:
                    self.log(f"更新预览内容时出错: {str(e)}")
            
        except Exception as e:
            if not self.stop_flag:
                self.log(f"处理文件时出错: {str(e)}")
                messagebox.showerror("错误", f"处理文件时出错: {str(e)}")
        
        finally:
            self.is_running = False
            self.stop_flag = False
            self.extract_btn.config(state=tk.NORMAL)
            self.extract_with_rules_btn.config(state=tk.NORMAL)
            self.apply_rules_btn.config(state=tk.NORMAL)
    
    def generate_urls(self, start_url, end_url):
        """根据开始和结束URL生成URL列表"""
        try:
            # 解析URL
            parsed_start = urlparse(start_url)
            parsed_end = urlparse(end_url)
            
            # 确保域名相同
            if parsed_start.netloc != parsed_end.netloc:
                self.log("开始和结束URL的域名不同，无法生成范围")
                return []
            
            # 尝试找到URL中的数字部分
            start_path = parsed_start.path
            end_path = parsed_end.path
            
            # 使用正则表达式查找路径中的数字
            start_match = re.search(r'(\d+)(?:\.html|\.htm|\.php|\/?)?$', start_path)
            end_match = re.search(r'(\d+)(?:\.html|\.htm|\.php|\/?)?$', end_path)
            
            if not start_match or not end_match:
                self.log("无法在URL中找到递增的数字部分")
                # 如果无法找到数字部分，则只返回这两个URL
                return [start_url, end_url] if start_url != end_url else [start_url]
            
            # 提取数字和前缀
            start_num = int(start_match.group(1))
            end_num = int(end_match.group(1))
            
            # 获取URL前缀（数字之前的部分）
            prefix_start = start_path[:start_match.start(1)]
            
            # 获取URL后缀（数字之后的部分）
            suffix_start = start_path[start_match.end(1):]
            
            # 构建URL列表
            urls = []
            for num in range(start_num, end_num + 1):
                path = f"{prefix_start}{num}{suffix_start}"
                url = f"{parsed_start.scheme}://{parsed_start.netloc}{path}"
                if parsed_start.query:
                    url += f"?{parsed_start.query}"
                urls.append(url)
            
            return urls
            
        except Exception as e:
            self.log(f"生成URL范围时出错: {str(e)}")
            return []
    
    def download_and_extract(self, url):
        """下载网页并提取正文内容"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = response.apparent_encoding  # 自动检测编码
        
        # 使用Beautiful Soup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除不需要的元素
        for element in soup.select('script, style, iframe, ins, .adsbygoogle'):
            element.decompose()
        
        # 尝试找到正文内容
        # 这里需要根据具体网站调整选择器
        content_selectors = [
            'div.content', 'div.article-content', 'div.entry-content',
            'div.post-content', 'div.chapter-content', 'div#content',
            'article', '.article', '.content', '#article', '#articleContent',
            'div.txt', 'div.TXT', 'div.novel', '.novel-content'
        ]
        
        content = None
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element and len(content_element.get_text(strip=True)) > 200:
                content = content_element
                break
        
        # 如果没有找到内容，尝试查找最长的文本块
        if not content:
            paragraphs = soup.find_all('p')
            if paragraphs:
                # 找出包含最多文本的div
                divs = soup.find_all('div')
                if divs:
                    divs_with_text = [(div, len(div.get_text(strip=True))) for div in divs]
                    divs_with_text.sort(key=lambda x: x[1], reverse=True)
                    if divs_with_text and divs_with_text[0][1] > 200:
                        content = divs_with_text[0][0]
        
        # 如果仍然没有找到内容，使用body
        if not content:
            content = soup.body
        
        # 提取文本并处理
        if content:
            text = self.process_text(content.get_text('\n', strip=True))
            return text
        else:
            return "无法提取内容"
    
    def process_text(self, text):
        """处理提取的文本"""
        # 删除空行
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        # 删除引号
        text = text.replace('"', '')
        
        # 标点符号全角化
        punctuation_map = {
            ',': '，',
            '.': '。',
            ':': '：',
            ';': '；',
            '!': '！',
            '?': '？',
            '(': '（',
            ')': '）',
            '[': '【',
            ']': '】'
        }
        
        for en, cn in punctuation_map.items():
            text = text.replace(en, cn)
        
        # 删除可能的广告文本
        ad_patterns = [
            r'广告位',
            r'\d+秒.*跳转',
            r'推荐.*小说',
            r'本章未完.*下一页',
            r'手机阅读.*m\.',
            r'www\.\w+\.(?:com|net|org|cn)',
            r'最新章节',
            r'全文阅读',
            r'字体.*设置',
            r'加入收藏',
            r'TXT下载',
            r'返回目录',
            r'上一章',
            r'下一章',
            r'章节目录',
            r'更新时间',
            r'\d+个书友.*在线',
            r'请记住本站的网址',
            r'如果您喜欢',
            r'本站地址',
            r'免费阅读',
            r'请用.*浏览器',
            r'章节错误,点此举报'
        ]
        
        for pattern in ad_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 智能分段：确保段落之间有空行
        paragraphs = text.split('\n')
        processed_paragraphs = []
        
        for p in paragraphs:
            p = p.strip()
            if p:  # 只保留非空段落
                processed_paragraphs.append(p)
        
        return '\n\n'.join(processed_paragraphs)
    
    def merge_files_without_rules(self, file_paths_dict, output_path):
        """合并多个文本文件，按照索引顺序合并，不应用自定义规则"""
        # 先将所有文件内容合并到一个临时字符串中
        merged_content = ""
        
        # 获取所有索引并排序，确保按照URL的原始顺序合并文件
        sorted_indices = sorted(file_paths_dict.keys())
        self.log(f"按照原始URL顺序合并 {len(sorted_indices)} 个文件...")
        
        for idx in sorted_indices:
            file_path = file_paths_dict[idx]
            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    merged_content += infile.read() + '\n\n'
                self.log(f"合并文件: chapter_{idx+1}.txt")
            except Exception as e:
                self.log(f"合并文件 {file_path} 时出错: {str(e)}")
        
        # 基本清理（只清理多余空行，不应用规则）
        merged_content = re.sub(r'\n\s*\n+', '\n\n', merged_content)
        
        # 写入到输出文件
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write(merged_content)
    
    def merge_files_with_rules(self, file_paths_dict, output_path):
        """合并多个文本文件，按照索引顺序合并，并应用自定义规则"""
        # 先将所有文件内容合并到一个临时字符串中
        merged_content = ""
        
        # 获取所有索引并排序，确保按照URL的原始顺序合并文件
        sorted_indices = sorted(file_paths_dict.keys())
        self.log(f"按照原始URL顺序合并 {len(sorted_indices)} 个文件...")
        
        for idx in sorted_indices:
            file_path = file_paths_dict[idx]
            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    merged_content += infile.read() + '\n\n'
                self.log(f"合并文件: chapter_{idx+1}.txt")
            except Exception as e:
                self.log(f"合并文件 {file_path} 时出错: {str(e)}")
        
        # 应用自定义规则处理合并后的内容
        self.log("正在应用自定义规则...")
        merged_content = self.apply_custom_rules(merged_content)
        
        # 写入到输出文件
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write(merged_content)
    
    def apply_custom_rules(self, content):
        """应用自定义规则处理内容"""
        # 应用所有自定义过滤规则
        for rule_frame in self.filter_rules:
            start_text = rule_frame.start_entry.get().strip()
            end_text = rule_frame.end_entry.get().strip()
            
            if start_text and end_text:
                # 转义正则表达式中的特殊字符
                start_pattern = re.escape(start_text)
                end_pattern = re.escape(end_text)
                
                # 创建正则表达式并应用
                pattern = f'{start_pattern}.*?{end_pattern}'
                content = re.sub(pattern, '', content, flags=re.DOTALL)
                self.log(f"- 删除包含'{start_text}'到'{end_text}'之间的文字")
            elif start_text and not end_text:
                # 如果只有起始文本，直接删除所有匹配的字符串
                # 转义正则表达式中的特殊字符
                pattern = re.escape(start_text)
                content = re.sub(pattern, '', content)
                self.log(f"- 删除所有'{start_text}'字符串")
        
        # 应用所有自定义替换规则
        for rule_frame in self.replace_rules:
            # 检查是否为特殊删除规则
            if hasattr(rule_frame, 'is_special_rule') and rule_frame.is_special_rule:
                # 处理特殊删除规则
                search_text = rule_frame.search_entry.get().strip()
                
                # 按行处理内容
                lines = content.split('\n')
                deleted_count = 0
                new_lines = []
                
                for line in lines:
                    # 检查行是否仅包含指定内容
                    if line.strip() == search_text:
                        # 跳过该行（即删除）
                        deleted_count += 1
                    else:
                        new_lines.append(line)
                
                content = '\n'.join(new_lines)
                if deleted_count > 0:
                    self.log(f"- 特殊删除：删除仅包含'{search_text}'的行，共删除 {deleted_count} 行")
            else:
                # 处理普通替换规则
                search_text = rule_frame.search_entry.get().strip()
                replace_text = rule_frame.replace_entry.get().strip()
                
                if search_text:
                    # 转义正则表达式中的特殊字符
                    pattern = re.escape(search_text)
                    # 执行替换
                    old_content = content
                    content = re.sub(pattern, replace_text, content)
                    # 计算替换次数
                    count = old_content.count(search_text)
                    if count > 0:
                        self.log(f"- 将'{search_text}'替换为'{replace_text}'，共替换 {count} 处")
        
        # 如果选中了段落缩进选项
        if hasattr(self, 'paragraph_indent_var') and self.paragraph_indent_var.get():
            # 为每个段落添加缩进
            lines = content.split('\n')
            processed_lines = []
            indent_count = 0
            
            for line in lines:
                # 跳过空行
                if not line.strip():
                    processed_lines.append(line)
                    continue
                
                # 判断是否是章节标题
                is_title = ((("第" in line and ("章" in line or "节" in line)) or 
                           any(line.startswith(prefix) for prefix in ["第", "序", "前言", "后记", "附录"])) and 
                           len(line) <= 20)
                
                if is_title:
                    processed_lines.append(line)
                else:
                    # 如果行不是以空格开头，添加两个全角空格作为缩进
                    if not line.startswith(' ') and not line.startswith('　'):
                        line = '　　' + line
                        indent_count += 1
                    processed_lines.append(line)
            
            content = '\n'.join(processed_lines)
            if indent_count > 0:
                self.log(f"- 为 {indent_count} 个段落添加了缩进")
        
        # 如果选中了删除行末数字选项
        if hasattr(self, 'remove_end_numbers_var') and self.remove_end_numbers_var.get():
            # 删除每行末尾的纯数字
            lines = content.split('\n')
            processed_lines = []
            removed_count = 0
            
            for line in lines:
                # 使用正则表达式匹配行末的纯数字
                new_line = re.sub(r'\s*\d+\s*$', '', line)
                if new_line != line:
                    removed_count += 1
                processed_lines.append(new_line)
            
            content = '\n'.join(processed_lines)
            if removed_count > 0:
                self.log(f"- 删除了 {removed_count} 行的行末数字")
        
        # 如果选中了删除空行选项
        if hasattr(self, 'remove_empty_lines_var') and self.remove_empty_lines_var.get():
            # 删除空行
            lines = content.split('\n')
            processed_lines = []
            removed_count = 0
            
            for line in lines:
                if line.strip():
                    processed_lines.append(line)
                else:
                    removed_count += 1
            
            content = '\n'.join(processed_lines)
            if removed_count > 0:
                self.log(f"- 删除了 {removed_count} 个空行")
        
        # 如果选中了删除上下行相同字符选项
        if hasattr(self, 'remove_duplicate_lines_var') and self.remove_duplicate_lines_var.get():
            # 删除相邻的重复行
            lines = content.split('\n')
            processed_lines = []
            removed_count = 0
            
            # 处理第一行
            if lines:
                processed_lines.append(lines[0])
            
            # 处理剩余行
            for i in range(1, len(lines)):
                # 如果当前行与前一行不同，则保留
                if lines[i].strip() != processed_lines[-1].strip():
                    processed_lines.append(lines[i])
                else:
                    removed_count += 1
            
            content = '\n'.join(processed_lines)
            if removed_count > 0:
                self.log(f"- 删除了 {removed_count} 个上下行相同的内容")
        
        # 清理可能产生的多余空行
        content = re.sub(r'\n\s*\n+', '\n\n', content)
        
        return content
    
    # 保留原方法以兼容旧代码
    def merge_files(self, file_paths_dict, output_path):
        """合并多个文本文件，按照索引顺序合并（兼容旧代码）"""
        self.merge_files_with_rules(file_paths_dict, output_path)
    
    # 保留原方法以兼容旧代码
    def post_process_content(self, content):
        """对合并后的内容进行后处理（兼容旧代码）"""
        return self.apply_custom_rules(content)

    def add_filter_rule(self, start_text="", end_text=""):
        """添加一个过滤规则"""
        # 创建规则框架
        rule_idx = len(self.filter_rules)
        rule_frame = ttk.Frame(self.rules_frame)
        rule_frame.pack(fill=tk.X, pady=2)
        
        # 添加规则编号标签
        rule_label = ttk.Label(rule_frame, text=f"删除规则 {rule_idx+1}:")
        rule_label.grid(row=0, column=0, padx=5)
        rule_frame.rule_label = rule_label
        
        # 添加开始文本输入框
        ttk.Label(rule_frame, text="删除").grid(row=0, column=1, padx=5)
        start_entry = ttk.Entry(rule_frame, width=20)
        start_entry.grid(row=0, column=2, padx=5)
        start_entry.insert(0, start_text)
        rule_frame.start_entry = start_entry
        
        # 为输入框添加右键菜单
        start_entry.bind("<Button-3>", self.show_context_menu)
        
        # 添加结束文本输入框
        ttk.Label(rule_frame, text="到").grid(row=0, column=3, padx=5)
        end_entry = ttk.Entry(rule_frame, width=20)
        end_entry.grid(row=0, column=4, padx=5)
        end_entry.insert(0, end_text)
        rule_frame.end_entry = end_entry
        
        # 为输入框添加右键菜单
        end_entry.bind("<Button-3>", self.show_context_menu)
        
        # 添加删除按钮
        delete_btn = ttk.Button(rule_frame, text="删除", 
                               command=lambda frame=rule_frame: self.remove_filter_rule(frame))
        delete_btn.grid(row=0, column=5, padx=5)
        
        # 保存规则框架的引用
        self.filter_rules.append(rule_frame)
        return rule_frame
    
    def add_empty_rule(self):
        """添加一个空的过滤规则"""
        self.add_filter_rule()
    
    def remove_filter_rule(self, rule_frame):
        """删除一个过滤规则"""
        if rule_frame in self.filter_rules:
            self.filter_rules.remove(rule_frame)
            rule_frame.destroy()
            
            # 更新剩余规则的编号
            for i, frame in enumerate(self.filter_rules):
                frame.rule_label.config(text=f"删除规则 {i+1}:")
    
    def export_rules(self):
        """导出自定义删除规则到文件"""
        if not self.filter_rules:
            messagebox.showinfo("提示", "当前没有可导出的规则！")
            return
        
        # 选择保存文件的位置
        file_path = filedialog.asksaveasfilename(
            title="保存规则文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            defaultextension=".json"
        )
        
        if not file_path:
            return
        
        try:
            # 收集所有规则
            rules_data = []
            for rule_frame in self.filter_rules:
                start_text = rule_frame.start_entry.get().strip()
                end_text = rule_frame.end_entry.get().strip()
                if start_text or end_text:  # 只保存非空规则
                    rules_data.append({
                        "start": start_text,
                        "end": end_text
                    })
            
            # 保存为JSON文件
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, ensure_ascii=False, indent=2)
            
            self.log(f"规则已成功导出到: {file_path}")
            messagebox.showinfo("成功", f"已成功导出 {len(rules_data)} 条规则！")
            
        except Exception as e:
            self.log(f"导出规则时出错: {str(e)}")
            messagebox.showerror("错误", f"导出规则时出错: {str(e)}")
    
    def import_rules(self):
        """从文件导入自定义删除规则"""
        # 选择要导入的规则文件
        file_path = filedialog.askopenfilename(
            title="选择规则文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 读取JSON文件
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            if not isinstance(rules_data, list):
                raise ValueError("规则文件格式不正确！")
            
            # 清除现有规则
            for rule_frame in self.filter_rules:
                rule_frame.destroy()
            self.filter_rules = []
            
            # 添加导入的规则
            for rule in rules_data:
                if isinstance(rule, dict) and "start" in rule and "end" in rule:
                    self.add_filter_rule(rule["start"], rule["end"])
                else:
                    self.log("跳过格式不正确的规则")
            
            self.log(f"已成功导入 {len(self.filter_rules)} 条规则")
            messagebox.showinfo("成功", f"已成功导入 {len(self.filter_rules)} 条规则！")
            
        except Exception as e:
            self.log(f"导入规则时出错: {str(e)}")
            messagebox.showerror("错误", f"导入规则时出错: {str(e)}")

    def add_empty_replace_rule(self):
        """添加一个空的替换规则"""
        self.add_replace_rule()
        
    def add_special_replace_rule(self):
        """添加特殊删除规则，用于删除仅包含指定内容的行"""
        # 创建规则框架
        rule_frame = ttk.Frame(self.rules_frame)
        rule_frame.pack(fill=tk.X, pady=2)
        
        # 计算特殊规则计数
        special_rule_count = sum(1 for rule in self.replace_rules if hasattr(rule, 'is_special_rule') and rule.is_special_rule) + 1
        
        # 创建一个内部框架来容纳标签和输入框，确保左对齐
        label_frame = ttk.Frame(rule_frame)
        label_frame.grid(row=0, column=0, sticky=tk.W, padx=5)
        
        # 添加规则标签和输入框
        ttk.Label(label_frame, text=f"特殊删除 {special_rule_count}:  删除整行只包含以下文字").pack(side=tk.LEFT, padx=2)
        content_entry = ttk.Entry(label_frame, width=16)
        content_entry.pack(side=tk.LEFT, padx=2)
        ttk.Label(label_frame, text="没有其他文字的行").pack(side=tk.LEFT, padx=2)
        
        # 添加删除按钮，确保与其他规则按钮大小和位置一致
        delete_btn = ttk.Button(rule_frame, text="删除", 
                              command=lambda frame=rule_frame: self.remove_rule_frame(frame))
        delete_btn.grid(row=0, column=5, padx=5)
        
        # 保存规则参数
        rule_frame.is_special_rule = True
        rule_frame.is_delete_only = True  # 标记为仅删除规则
        rule_frame.search_entry = content_entry  # 保存输入框引用
        
        # 添加到替换规则列表
        self.replace_rules.append(rule_frame)
        
        # 为输入框添加右键菜单
        content_entry.bind("<Button-3>", self.show_context_menu)
        
    def remove_rule_frame(self, rule_frame):
        """删除一个特殊删除规则"""
        if rule_frame in self.replace_rules:
            self.replace_rules.remove(rule_frame)
            rule_frame.destroy()
            
            # 更新剩余特殊规则的编号
            special_rule_idx = 0
            for frame in self.replace_rules:
                if hasattr(frame, 'is_special_rule') and frame.is_special_rule:
                    special_rule_idx += 1
                    # 找到标签并更新
                    for child in frame.winfo_children():
                        if isinstance(child, ttk.Frame):
                            for label in child.winfo_children():
                                if isinstance(label, ttk.Label) and "特殊删除" in label.cget("text"):
                                    label.config(text=f"特殊删除 {special_rule_idx}:  删除整行只包含以下文字")
                                    break
                if hasattr(frame, 'is_special_rule') and frame.is_special_rule:
                    # 找到标签并更新
                    for child in frame.winfo_children():
                        if isinstance(child, ttk.Frame):
                            for label in child.winfo_children():
                                if isinstance(label, ttk.Label) and "特殊删除" in label.cget("text"):
                                    label.config(text=f"特殊删除 {special_rule_count}:  删除整行只包含以下文字")
                                    special_rule_count += 1
                                    break
    
    def add_replace_rule(self, search_text="", replace_text=""):
        """添加一个替换规则"""
        # 创建规则框架
        # 计算普通替换规则的数量（不包括特殊删除规则）
        rule_idx = sum(1 for rule in self.replace_rules if not (hasattr(rule, 'is_special_rule') and rule.is_special_rule))
        rule_frame = ttk.Frame(self.rules_frame)
        rule_frame.pack(fill=tk.X, pady=2)
        
        # 添加规则编号标签
        rule_label = ttk.Label(rule_frame, text=f"替换规则 {rule_idx+1}:")
        rule_label.grid(row=0, column=0, padx=5)
        rule_frame.rule_label = rule_label
        
        # 添加查找文本输入框
        ttk.Label(rule_frame, text="替换").grid(row=0, column=1, padx=5)
        search_entry = ttk.Entry(rule_frame, width=20)
        search_entry.grid(row=0, column=2, padx=5)
        search_entry.insert(0, search_text)
        rule_frame.search_entry = search_entry
        
        # 为输入框添加右键菜单
        search_entry.bind("<Button-3>", self.show_context_menu)
        
        # 添加替换文本输入框
        ttk.Label(rule_frame, text="为").grid(row=0, column=3, padx=5)
        replace_entry = ttk.Entry(rule_frame, width=20)
        replace_entry.grid(row=0, column=4, padx=5)
        replace_entry.insert(0, replace_text)
        rule_frame.replace_entry = replace_entry
        
        # 为输入框添加右键菜单
        replace_entry.bind("<Button-3>", self.show_context_menu)
        
        # 添加删除按钮
        delete_btn = ttk.Button(rule_frame, text="删除", 
                               command=lambda frame=rule_frame: self.remove_replace_rule(frame))
        delete_btn.grid(row=0, column=5, padx=5)
        
        # 保存规则框架的引用
        self.replace_rules.append(rule_frame)
        return rule_frame
    
    def remove_replace_rule(self, rule_frame):
        """删除一个替换规则"""
        if rule_frame in self.replace_rules:
            self.replace_rules.remove(rule_frame)
            rule_frame.destroy()
            
            # 更新剩余规则的编号，不包括特殊删除规则
            normal_rule_idx = 0
            for frame in self.replace_rules:
                # 只更新普通替换规则的编号
                if not (hasattr(frame, 'is_special_rule') and frame.is_special_rule):
                    normal_rule_idx += 1
                    frame.rule_label.config(text=f"替换规则 {normal_rule_idx}:")


# 主程序入口
if __name__ == "__main__":
    root = tk.Tk()
    app = NovelExtractor(root)
    root.mainloop()