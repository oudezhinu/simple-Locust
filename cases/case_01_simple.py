# 导入Locust类
from locust import FastHttpUser, task

class MockUser(FastHttpUser):
    # 设置默认的请求hots
    host = "http://127.0.0.1:5000"
    # 使用@task装饰器表明此方法是一个需要执行的用例
    # Locust装饰器详细介绍请查看基础章节
    @task
    def test_public_route(self):
        self.client.get(url="/public")
        # headless方式运行
        # self.client.get(url= MockUser.host + "/public")