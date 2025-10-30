import fetch from 'node-fetch';

async function testFrontend() {
  try {
    console.log('🔍 检查前端服务器状态...');
    
    // 尝试访问前端服务器
    const response = await fetch('http://localhost:3000');
    
    if (response.ok) {
      console.log('✅ 前端服务器正在运行，状态码:', response.status);
      
      const html = await response.text();
      if (html.includes('id="root"')) {
        console.log('✅ 找到React根元素');
      } else {
        console.log('❌ 未找到React根元素');
      }
    } else {
      console.log('❌ 前端服务器响应错误，状态码:', response.status);
    }
  } catch (error) {
    console.log('❌ 无法连接到前端服务器:', error.message);
    console.log('💡 提示: 请确保在另一个终端中运行了 npm run dev');
  }
}

testFrontend();