# PowerShell script to check frontend console errors
Add-Type -AssemblyName System.Web

Write-Host "🔍 开始检查前端控制台错误..." -ForegroundColor Green

try {
    # 检查服务器是否运行
    $response = Invoke-WebRequest -Uri "http://localhost:5176" -TimeoutSec 10 -UseBasicParsing
    Write-Host "✅ 前端服务器响应正常 (Status: $($response.StatusCode))" -ForegroundColor Green

    # 获取页面内容
    $html = $response.Content

    # 检查关键元素
    if ($html -match '<div id="root">') {
        Write-Host "✅ 找到React根元素" -ForegroundColor Green
    } else {
        Write-Host "❌ 未找到React根元素" -ForegroundColor Red
    }

    if ($html -match 'from "/@vite/client"') {
        Write-Host "✅ Vite客户端脚本已加载" -ForegroundColor Green
    } else {
        Write-Host "❌ Vite客户端脚本未找到" -ForegroundColor Red
    }

    if ($html -match 'src="/src/main.tsx"') {
        Write-Host "✅ React应用入口脚本已加载" -ForegroundColor Green
    } else {
        Write-Host "❌ React应用入口脚本未找到" -ForegroundColor Red
    }

    # 检查页面标题
    if ($html -match '<title>(.*?)</title>') {
        $title = $matches[1]
        Write-Host "📄 页面标题: $title" -ForegroundColor Cyan
    }

    Write-Host "`n🔍 检查已知问题..." -ForegroundColor Yellow

    # 检查我之前修复的导入问题
    $appFile = Get-Content "src\App.tsx" -Raw
    if ($appFile -match 'import.*Alert.*Card.*from.*antd') {
        Write-Host "✅ Alert和Card组件已正确导入" -ForegroundColor Green
    } else {
        Write-Host "❌ Alert和Card组件导入有问题" -ForegroundColor Red
    }

    # 检查MaterialLayout组件
    if (Test-Path "src\components\MaterialLayout.tsx") {
        Write-Host "✅ MaterialLayout组件存在" -ForegroundColor Green
    } else {
        Write-Host "❌ MaterialLayout组件不存在" -ForegroundColor Red
    }

    # 检查其他关键组件
    $components = @(
        "UploadForm.tsx",
        "JobsTable.tsx",
        "DiffViewer.tsx",
        "EnhancedUploadForm.tsx",
        "ModernDWGConverter.tsx"
    )

    Write-Host "`n📁 检查组件文件..." -ForegroundColor Yellow
    foreach ($component in $components) {
        if (Test-Path "src\components\$component") {
            Write-Host "✅ $component" -ForegroundColor Green
        } else {
            Write-Host "❌ $component" -ForegroundColor Red
        }
    }

    # 检查hooks
    Write-Host "`n📁 检查Hooks..." -ForegroundColor Yellow
    if (Test-Path "src\hooks\useJobs.ts") {
        Write-Host "✅ useJobs hook存在" -ForegroundColor Green
    } else {
        Write-Host "❌ useJobs hook不存在" -ForegroundColor Red
    }

    # 检查types
    Write-Host "`n📁 检查类型定义..." -ForegroundColor Yellow
    if (Test-Path "src\types\jobs.ts") {
        Write-Host "✅ jobs类型定义存在" -ForegroundColor Green
    } else {
        Write-Host "❌ jobs类型定义不存在" -ForegroundColor Red
    }

    # 检查样式文件
    if (Test-Path "src\styles.css") {
        Write-Host "✅ 样式文件存在" -ForegroundColor Green
    } else {
        Write-Host "❌ 样式文件不存在" -ForegroundColor Red
    }

    Write-Host "`n🎯 基于代码分析的常见问题检查:" -ForegroundColor Cyan

    # 检查是否有未处理的异步操作
    $tsFiles = Get-ChildItem "src" -Filter "*.tsx" -Recurse
    $asyncIssues = 0
    foreach ($file in $tsFiles) {
        $content = Get-Content $file.FullName -Raw
        if ($content -match 'await.*void' -or $content -match 'void.*await') {
            Write-Host "⚠️ 发现可能的异步操作问题: $($file.Name)" -ForegroundColor Yellow
            $asyncIssues++
        }
    }

    if ($asyncIssues -eq 0) {
        Write-Host "✅ 没有发现明显的异步操作问题" -ForegroundColor Green
    }

    # 检查TypeScript错误
    Write-Host "`n🔍 尝试编译检查TypeScript错误..." -ForegroundColor Yellow
    try {
        $tscResult = npm run build 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ TypeScript编译成功" -ForegroundColor Green
        } else {
            Write-Host "❌ TypeScript编译失败:" -ForegroundColor Red
            Write-Host $tscResult -ForegroundColor Red
        }
    } catch {
        Write-Host "⚠️ 无法检查TypeScript编译" -ForegroundColor Yellow
    }

} catch {
    Write-Host "❌ 无法访问前端服务器: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "请确保开发服务器正在运行 (npm run dev)" -ForegroundColor Yellow
}

Write-Host "`n📋 检查完成！" -ForegroundColor Green
Write-Host "💡 要查看实时控制台错误，请在浏览器中打开 http://localhost:5176 并打开开发者工具" -ForegroundColor Cyan