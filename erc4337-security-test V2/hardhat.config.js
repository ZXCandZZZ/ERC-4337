require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  // 1. 设置Solidity编译器版本（必须与ERC-4337合约版本匹配）
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  
  // 2. 配置网络：最重要的本地开发网络
  networks: {
    hardhat: {
      // 这是Hardhat内置的本地网络，无需额外安装
      chainId: 31337, // 本地测试链的标准ID
      mining: {
        auto: true,    // 自动挖矿，交易立即确认
        interval: 0    // 无延迟
      },
      // 提供测试账户（每个账户10000 ETH）
      accounts: {
        mnemonic: "test test test test test test test test test test test junk",
        count: 20,
        accountsBalance: "10000000000000000000000" // 10000 ETH
      }
    },
    // 你也可以为后续连接公共测试网预留配置
    localhost: {
      url: "http://127.0.0.1:8545", // 本地节点RPC地址
      chainId: 31337
    }
  },
  
  // 3. 配置项目路径（保持默认即可）
  paths: {
    sources: "./contracts",
    tests: "./tests",
    cache: "./cache",
    artifacts: "./artifacts"
  }
};