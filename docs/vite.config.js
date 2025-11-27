export default {
  server: {
    // 允许访问的主机列表（添加需要允许的域名）
    allowedHosts: [
      'docs.agentkit.bytedance.net', // 解决当前报错的主机
      // 可选：添加其他需要允许的主机，如本地IP、自定义域名等
      // 'localhost',
      // '192.168.1.100'
    ]
  }
}
