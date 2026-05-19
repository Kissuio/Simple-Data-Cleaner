class BaseDataHandler:
    #初始化空一点吧
    def __init__(self):
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
