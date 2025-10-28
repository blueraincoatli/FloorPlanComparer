# QCAD 安装指南

为了使用我们新开发的 DWG 到 PDF 转换模块，您需要先安装 QCAD 软件，因为该模块依赖于 QCAD 提供的 `dwg2pdf` 命令行工具。

## 下载 QCAD

1. 访问 QCAD 官方下载页面: https://qcad.org/en/download
2. 根据您的操作系统选择相应的版本:
   - Windows 用户: 选择 "QCAD Trial for Windows 64bit Installer" 或 "QCAD Trial for Windows 32bit Installer"
   - macOS 用户: 选择相应的 macOS 版本
   - Linux 用户: 选择相应的 Linux 版本

## 安装 QCAD

### Windows 安装步骤

1. 下载完成后，双击安装文件开始安装过程
2. 按照安装向导的提示完成安装
3. 安装完成后，QCAD 会自动将命令行工具添加到系统路径中

### Linux 安装步骤

1. 下载安装包后，解压缩到您选择的目录
2. 如果下载的是 .tar.gz 文件，可以使用以下命令解压：
   ```
   tar -xzf qcad-<version>-linux-64bit.tar.gz
   ```
3. 进入解压后的目录，运行 QCAD：
   ```
   cd qcad-<version>-linux-64bit
   ./qcad
   ```

## 验证安装

安装完成后，您可以通过以下方式验证 `dwg2pdf` 命令是否可用：

1. 打开命令提示符（Windows）或终端（Linux/macOS）
2. 输入以下命令：
   ```
   dwg2pdf -h
   ```
3. 如果安装成功，您应该能看到 `dwg2pdf` 的帮助信息

## 在无头模式下运行

如果您需要在服务器环境或无图形界面的环境中运行 `dwg2pdf`，可以使用以下参数：

```
dwg2pdf -platform offscreen [其他参数] input.dwg
```

这将允许 `dwg2pdf` 在没有图形界面的情况下运行。

## 故障排除

如果在安装后无法找到 `dwg2pdf` 命令，请尝试以下解决方案：

1. 重新启动命令行窗口或终端
2. 手动将 QCAD 安装目录添加到系统 PATH 环境变量中
3. 在转换模块中直接指定 QCAD 安装路径

## 参考资料

- QCAD 官方网站: https://qcad.org/
- QCAD 命令行工具文档: https://qcad.org/en/products/qcad-command-line-tools