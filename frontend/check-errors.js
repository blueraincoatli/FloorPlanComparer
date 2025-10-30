import { create } from 'browserless';

async function checkConsoleErrors() {
    try {
        console.log('启动浏览器检查控制台错误...');

        const browserless = await create({
            timeout: 30000,
            rejectTracking: true,
            ignoreDefaultArgs: false
        });

        console.log('📱 正在访问 http://localhost:5176...');

        const page = await browserless.page();
        const errors = [];
        const warnings = [];

        // 监听控制台消息
        page.on('console', msg => {
            const text = msg.text();
            const type = msg.type();

            if (type === 'error') {
                errors.push({
                    text,
                    location: msg.location()
                });
                console.error(`❌ [ERROR] ${text}`);
                if (msg.location()) {
                    console.error(`   位置: ${msg.location().url}:${msg.location().lineNumber}`);
                }
            } else if (type === 'warning') {
                warnings.push({
                    text,
                    location: msg.location()
                });
                console.warn(`⚠️ [WARNING] ${text}`);
            } else if (type === 'log') {
                console.log(`ℹ️ [LOG] ${text}`);
            }
        });

        // 监听页面错误
        page.on('pageerror', error => {
            errors.push({
                text: error.message,
                stack: error.stack
            });
            console.error(`❌ [PAGE ERROR] ${error.message}`);
            if (error.stack) {
                console.error(`   堆栈: ${error.stack}`);
            }
        });

        // 监听请求失败
        page.on('requestfailed', request => {
            console.error(`❌ [REQUEST FAILED] ${request.url()} - ${request.failure()?.errorText}`);
        });

        // 访问页面
        const response = await page.goto('http://localhost:5176', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });

        if (!response.ok()) {
            throw new Error(`HTTP ${response.status()}: ${response.statusText()}`);
        }

        console.log('✅ 页面加载成功');

        // 等待React应用完全加载
        await page.waitForTimeout(3000);

        // 检查React是否已加载
        const reactLoaded = await page.evaluate(() => {
            return !!window.React || !!document.querySelector('[data-reactroot]');
        });

        if (reactLoaded) {
            console.log('✅ React已加载');
        } else {
            console.warn('⚠️ React可能未正确加载');
        }

        // 检查Ant Design组件是否存在
        const antdLoaded = await page.evaluate(() => {
            // 检查Ant Design CSS
            const links = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
            const hasAntdStyles = links.some(link =>
                link.href.includes('antd') ||
                link.href.includes('ant-design')
            );

            // 检查Ant Design组件
            const hasAntdComponents = !!document.querySelector('.ant-btn, .ant-card, .ant-menu');

            return hasAntdStyles || hasAntdComponents;
        });

        if (antdLoaded) {
            console.log('✅ Ant Design已加载');
        } else {
            console.warn('⚠️ Ant Design可能未正确加载');
        }

        // 检查主要组件是否存在
        const componentsExist = await page.evaluate(() => {
            const root = document.getElementById('root');
            if (!root) return { root: false };

            const hasNav = !!root.querySelector('nav, .ant-menu');
            const hasSidebar = !!root.querySelector('.ant-layout-sider');
            const hasContent = !!root.querySelector('.ant-layout-content');

            return {
                root: true,
                nav: hasNav,
                sidebar: hasSidebar,
                content: hasContent
            };
        });

        console.log('📊 组件检查结果:', componentsExist);

        // 获取页面标题
        const title = await page.title();
        console.log(`📄 页面标题: "${title}"`);

        // 检查页面内容
        const hasContent = await page.evaluate(() => {
            const root = document.getElementById('root');
            return root && root.children.length > 0;
        });

        if (hasContent) {
            console.log('✅ 页面有内容渲染');
        } else {
            console.warn('⚠️ 页面可能没有正确渲染');
        }

        await browserless.close();

        // 汇总结果
        console.log('\n📋 检查结果汇总:');
        console.log(`- 错误数量: ${errors.length}`);
        console.log(`- 警告数量: ${warnings.length}`);

        if (errors.length === 0 && warnings.length === 0) {
            console.log('🎉 没有发现控制台错误或警告！');
        } else {
            if (errors.length > 0) {
                console.log(`❌ 发现 ${errors.length} 个错误需要修复`);
            }
            if (warnings.length > 0) {
                console.log(`⚠️ 发现 ${warnings.length} 个警告需要关注`);
            }
        }

    } catch (error) {
        console.error('💥 检查过程中发生错误:', error);
    }
}

checkConsoleErrors().catch(console.error);