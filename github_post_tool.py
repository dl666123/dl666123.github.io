#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton, QMessageBox,
    QFileDialog, QProgressBar, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

class GitHubPostTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitHub 自动发帖工具")
        self.setGeometry(100, 100, 800, 600)
        
        # 初始化数据
        self.access_token = ""
        self.repos = []
        self.selected_repo = ""
        
        # 创建主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # 编辑器标签页
        editor_tab = QWidget()
        editor_layout = QVBoxLayout(editor_tab)
        
        # 仓库选择
        repo_layout = QHBoxLayout()
        repo_label = QLabel("选择仓库:")
        self.repo_combo = QComboBox()
        refresh_repo_btn = QPushButton("刷新仓库")
        refresh_repo_btn.clicked.connect(self.refresh_repos)
        repo_layout.addWidget(repo_label)
        repo_layout.addWidget(self.repo_combo)
        repo_layout.addWidget(refresh_repo_btn)
        editor_layout.addLayout(repo_layout)
        
        # 标题输入
        title_layout = QHBoxLayout()
        title_label = QLabel("标题:")
        self.title_input = QLineEdit()
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_input)
        editor_layout.addLayout(title_layout)
        
        # 内容编辑器
        content_label = QLabel("内容 (Markdown):")
        editor_layout.addWidget(content_label)
        self.content_edit = QTextEdit()
        self.content_edit.setFont(QFont("Courier New", 10))
        editor_layout.addWidget(self.content_edit)
        
        # 发布按钮
        publish_btn = QPushButton("发布帖子")
        publish_btn.clicked.connect(self.publish_post)
        editor_layout.addWidget(publish_btn)
        
        # 设置标签页
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        
        # GitHub Token 输入
        token_layout = QHBoxLayout()
        token_label = QLabel("GitHub Token:")
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        save_token_btn = QPushButton("保存 Token")
        save_token_btn.clicked.connect(self.save_token)
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.token_input)
        token_layout.addWidget(save_token_btn)
        settings_layout.addLayout(token_layout)
        
        # 状态标签
        self.status_label = QLabel("状态: 未登录")
        settings_layout.addWidget(self.status_label)
        
        # 添加标签页
        self.tabs.addTab(editor_tab, "编辑器")
        self.tabs.addTab(settings_tab, "设置")
        
        # 加载保存的 Token
        self.load_token()
        if self.access_token:
            self.status_label.setText("状态: 已登录")
            self.refresh_repos()
    
    def load_token(self):
        """加载保存的 GitHub Token"""
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.access_token = config.get("access_token", "")
                    self.token_input.setText(self.access_token)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载配置失败: {str(e)}")
    
    def save_token(self):
        """保存 GitHub Token"""
        self.access_token = self.token_input.text()
        try:
            config = {"access_token": self.access_token}
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            self.status_label.setText("状态: 已登录")
            QMessageBox.information(self, "成功", "Token 保存成功！")
            self.refresh_repos()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存 Token 失败: {str(e)}")
    
    def refresh_repos(self):
        """刷新仓库列表"""
        if not self.access_token:
            QMessageBox.warning(self, "错误", "请先设置 GitHub Token！")
            return
        
        try:
            headers = {"Authorization": f"token {self.access_token}"}
            response = requests.get("https://api.github.com/user/repos", headers=headers)
            response.raise_for_status()
            
            self.repos = response.json()
            self.repo_combo.clear()
            for repo in self.repos:
                self.repo_combo.addItem(repo["full_name"])
            
            QMessageBox.information(self, "成功", f"已加载 {len(self.repos)} 个仓库")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"获取仓库列表失败: {str(e)}")
    
    def publish_post(self):
        """发布帖子"""
        if not self.access_token:
            QMessageBox.warning(self, "错误", "请先设置 GitHub Token！")
            return
        
        if self.repo_combo.currentIndex() == -1:
            QMessageBox.warning(self, "错误", "请选择一个仓库！")
            return
        
        title = self.title_input.text().strip()
        content = self.content_edit.toPlainText().strip()
        
        if not title:
            QMessageBox.warning(self, "错误", "请输入标题！")
            return
        
        if not content:
            QMessageBox.warning(self, "错误", "请输入内容！")
            return
        
        # 获取选择的仓库
        selected_repo = self.repo_combo.currentText()
        
        # 发布帖子到 GitHub Issues
        try:
            headers = {
                "Authorization": f"token {self.access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            data = {
                "title": title,
                "body": content
            }
            
            url = f"https://api.github.com/repos/{selected_repo}/issues"
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            issue_data = response.json()
            issue_url = issue_data["html_url"]
            
            QMessageBox.information(self, "成功", f"帖子发布成功！\n{issue_url}")
            
            # 清空输入
            self.title_input.clear()
            self.content_edit.clear()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"发布失败: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GitHubPostTool()
    window.show()
    sys.exit(app.exec_())