#Dependence
Python
Node.js


#change log 2026.2.6 test_signature_security-fixed.py
'''
测试漏洞用文件，位于.\tests\test_signature_security.py
修复了2个bugs
1.[测试 1/4] 全零签名攻击
   目的: 检查合约是否接受全为零的无效签名
❌ 测试框架初始化失败: 'Contract' object has no attribute 'encodeABI'

问题原因：
第97行的代码调用方法错误
self.account.encodeABI(fn_name='execute', args=[self.accounts['attacker'].address, 0, b'']), # callData

修复方法：
修改为
self.account.functions.execute(self.accounts['attacker'].address, 0, b'')._encode_transaction_data(), #callData

2.运行时测试4显示测试失败
从.\data\results\中的日志可发现'reverted with reason string 'Invalid nonce''
这证明测试4的非法nonce已经被拦截，理应测试成功，却显示测试失败
问题在于测试代码的异常处理逻辑，异常类型可能不是ContractLogicError，而是其他类型的异常（如ValueError或web3的BadResponseFormatError），因此直接进入了报错流程

修复方法：
修改第330-337行代码为：
        except Exception as e:
            error_str = str(e)
            if 'Invalid nonce' in error_str or 'nonce' in error_str.lower():
                return {
                    'test': 'replay_attack',
                    'status': '✅ 通过',
                    'description': '重放交易因nonce无效被拒绝。',
                    'severity': 'NONE',
                    'error': error_str[:100]
                }
            else:
                return {
                    'test': 'replay_attack',
                    'status': '⚠️ 测试失败',
                    'description': f'重放失败，但原因不是nonce无效: {error_str[:50]}',
                    'severity': 'INFO',
                    'error': error_str
                }
'''
