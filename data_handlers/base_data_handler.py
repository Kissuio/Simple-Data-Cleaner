class BaseDataHandler:
    """数据处理类的公共父类

    为所有数据处理子类（FileLoader / DataCleaner / RFMAnalyzer）提供
    共用属性与基础方法，体现 OOP 的继承与封装思想。

    属性:
        df (pandas.DataFrame | None): 当前持有的数据；初始化为 None
        log (list[str]): 操作日志列表，子类按需追加

    提供的基础方法:
        validate()      —— 校验 self.df 是否为有效数据
        report_change() —— 记录前后行数变化并写入日志
    """
    def __init__(self):
       """初始化空容器

        属性:
            df: pandas.DataFrame | None
                子类加载/接收数据后填充
            log: list[str]
                操作日志，按需追加字符串
       """
       self.df=None 
       self.log=[]  
       
    #未提交表格和空表格的检验
    def validate(self): 
      """检查数据是否为有效数据

      无文档或空文档: False

      正常文档: True
      """
      if (self.df is None):
            return False #未提交就是默认的none，返回flase
      if (len(self.df) == 0):
            return False #提交了但是是空的，仍然返回false
      return True
    
    #日志记录，改变行数多少
    def report_change(self, before_count, after_count):
      """记录操作前后行数变化，并返回日志消息
    
      参数:
          before_count: 操作前的行数
          after_count: 操作后的行数
    
      返回值:
          str: 操作日志消息
      """
      diff = before_count - after_count
      msg = f"操作完成：{before_count}—>{after_count}.改变{diff}行数据"
      self.log.append(msg)  # 加入自己的日志
      return msg  # 返回数据以便他人调用
