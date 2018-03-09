# CryptoCurrencyTrader

#### 虚拟货币自动交易程序

##### 我还未真正在交易所跑这个系统，所以OrderManager中与交易所交互的那几行代码暂时用了本地模拟代码代替，本地跑几天后，会切到真正的环境中


> 这个交易程序目前只适合于btcusdt交易对，因为在进行买入或卖出的时候，会以当前价格+1usdt或-1usdt进行买入和卖出，为了尽快的成交，1usdt对于btc来说可以忽略，但是对于其他币种来说，可能是一个很大的值，所以这里如果要用于其他币种的交易，请仔细阅读源代码，进行修改，我觉得可以改成当前价格的1.005倍，这个是在Start.py脚本中的**TryToBuy**和**TryToSell**函数中

**系统使用:**
1. 在Start.py同级目录新建一个Config.json文件，内容如下，在access_key和secret_key的地方分别填写自己的key
```
{"access_key":"","secret_key":""}
```
2. 运行 python3 Start.py
3. 如果要终止系统，可以在Start.py目录下创建一个'terminated'的空文件，系统一旦检测到这个文件的存在，就会停止各子模块，等待20秒后退出系统，等待20秒是为了让子模块的各线程执行完毕，数据保存完毕，要重新启动系统时，记得把'terminated'文件删除

**系统流程:**
整个系统的流程如下
DataDownloader 负责从交易所获取最新的价格数据，Start 脚本中依赖DataDownloader的数据执行"探针"策略进行买卖，可以说策略只是决定什么时候买入，系统启动时会以当前价格为参考，在当前价格下方的一个位置，目前是150usdt的地方，设置一个探针，当这个探针被触发时，就会执行买入，并且重新以新的价格为参考，重置探针位置。还有一个探针是上涨探针，如果价格不降，上涨了，触发了上方的探针，目前这个值设置的是100usdt，就会以最新的价格为参考，重新设置上面和下面的探针。简单来说，任何一个探针被触发，都将重置探针。下方探针被触发，还会执行买入。至于卖出，很简单，每一个买入的单，都为归为"持有"，每一次价格循环，都会检查所有的"持有"是否能够盈利5%，如果是，则会卖出。所以整个系统一开始，是只有USDT,然后会不断买入卖出。HoldManager就是所有"持有"的管理器。OrderManager是执行下单和成交检查的模块。