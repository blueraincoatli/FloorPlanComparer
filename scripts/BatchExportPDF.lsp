; BatchExportPDF.lsp
; 批量导出DWG文件为PDF

(defun c:BatchExportPDF (/ source_dir target_dir dwg_files file_count)

  ; 获取源文件夹路径
  (setq source_dir (getstring "\n选择源DWG文件夹: "))
  (setq target_dir (getstring "\n选择目标PDF文件夹: "))

  ; 获取DWG文件列表
  (setq dwg_files (getdwgfiles source_dir))

  ; 计数器
  (setq file_count 0)

  ; 遍历文件列表
  (foreach dwg_file dwg_files
    ; 打开DWG文件
    (command "_.open" dwg_file)
    
    ; 等待文档打开
    (while (= (getvar "DWGTITLED") 0)
      (grread)
    )

    ; 选择布局（这里选择模型空间）
    (setvar "CTAB" "Model")
    
    ; 导出为PDF
    (setq pdf_name (strcat target_dir "\\" (vl-filename-base dwg_file) ".pdf"))
    (command "_.pdfexport" pdf_name)
    
    ; 关闭文档（不保存）
    (command "_.close" "N")
    
    ; 更新计数器
    (setq file_count (1+ file_count))
    (princ (strcat "\n已处理文件 " (itoa file_count) ": " dwg_file))
  )

  ; 完成提示
  (princ (strcat "\n完成处理 " (itoa file_count) " 个文件"))
  (princ)
)

; 获取指定目录中的所有DWG文件
(defun getdwgfiles (dir / files)
  (setq files (findfiles (strcat dir "\\*.dwg") 1))
  files
)

; 计算文件名（不带扩展名）
(defun vl-filename-base (filename / pos)
  (setq pos (vl-string-position 46 filename)) ; 46 is ASCII for '.'
  (if pos
    (substr filename 1 pos)
    filename
  )
)