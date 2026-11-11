# 可执行测试

仓库根目录设置 `PYTHONPATH=src` 后执行 `python -m unittest discover -s tests -v`。测试使用独立工作目录与固定时钟，不连接真实模型；测试用数据库不提交。
