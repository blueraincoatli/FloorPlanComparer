import { chromium } from 'playwright';

async function checkConsoleErrors() {
    let browser;
    try {
        console.log('启动浏览器...');
        browser = await chromium.launch({ headless: false });
        const page = await browser.newPage();

        // 收集控制台消息
        const consoleMessages = [];
        page.on('console', msg => {
            consoleMessages.push({
                type: msg.type(),
                text: msg.text(),
                location: msg.location()
            });
        });

        // 收集页面错误
        const pageErrors = [];
        page.on('pageerror', error => {
            pageErrors.push({
                message: error.message,
                stack: error.stack
            });
        });

        // 收集失败的请求
        const failedRequests = [];
        page.on('requestfailed', request => {
            failedRequests.push({
                url: request.url(),
                failure: request.failure()
            });
        });

        console.log('导航到页面...');
        await page.goto('http://localhost:5176', { waitUntil: 'networkidle' });

        // 等待页面完全加载
        await page.waitForTimeout(3000);

        console.log('\n=== 控制台消息 ===');
        if (consoleMessages.length > 0) {
            consoleMessages.forEach(msg => {
                console.log(`[${msg.type.toUpperCase()}] ${msg.text}`);
                if (msg.location) {
                    console.log(`  位置: ${msg.location.url}:${msg.location.lineNumber}`);
                }
            });
        } else {
            console.log('没有控制台消息');
        }

        console.log('\n=== 页面错误 ===');
        if (pageErrors.length > 0) {
            pageErrors.forEach(error => {
                console.log(`❌ 错误: ${error.message}`);
                if (error.stack) {
                    console.log(`堆栈: ${error.stack}`);
                }
            });
        } else {
            console.log('✅ 没有页面错误');
        }

        console.log('\n=== 失败的请求 ===');
        if (failedRequests.length > 0) {
            failedRequests.forEach(req => {
                console.log(`❌ 失败请求: ${req.url}`);
                console.log(`   原因: ${req.failure ? req.failure.errorText : '未知'}`);
            });
        } else {
            console.log('✅ 没有失败的请求');
        }

        console.log('\n=== 页面元素检查 ===');

        // 检查导航栏
        try {
            const nav = await page.$('nav');
            if (nav) {
                console.log('✅ 导航栏存在');

                // 检查导航按钮
                const buttons = await nav.$$('button');
                console.log(`✅ 找到 ${buttons.length} 个导航按钮`);

                for (let i = 0; i < Math.min(buttons.length, 3); i++) {
                    const text = await buttons[i].textContent();
                    console.log(`  按钮 ${i + 1}: ${text}`);
                }
            } else {
                console.log('❌ 导航栏不存在');
            }
        } catch (e) {
            console.log(`❌ 导航栏检查失败: ${e.message}`);
        }

        // 检查应用容器
        try {
            const app = await page.$('#app');
            if (app) {
                console.log('✅ App根元素存在');
            } else {
                console.log('❌ App根元素不存在');
            }
        } catch (e) {
            console.log(`❌ App根元素检查失败: ${e.message}`);
        }

        // 检查是否有Material-UI样式
        try {
            const hasMuiStyles = await page.$eval('link[rel="stylesheet"]', link =>
                link.href.includes('material') || link.href.includes('mui')
            ).catch(() => false);

            if (hasMuiStyles) {
                console.log('✅ 检测到Material-UI样式');
            } else {
                console.log('⚠️  未检测到Material-UI样式');
            }
        } catch (e) {
            console.log('⚠️  样式检查失败');
        }

    } catch (error) {
        console.error(`检查过程中发生错误: ${error.message}`);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

checkConsoleErrors().catch(console.error);