import os,time, queue
from subprocess import Popen
from locust.runners import MasterRunner, WorkerRunner
from locust import HttpUser,FastHttpUser, task, TaskSet, events, run_single_user
from loguru import logger as log
# 全局变量
LOCUST_HOST = "http://0.0.0.0:8089"
USER_LIST = ["user1", "user2"]
users_queue = queue.Queue()
WORKER_ID = None

class TestCasesTasks(TaskSet):
    def on_start(self):
        
        # 不同worker上取用户
        try:
            user = users_queue.get()
        except:
            log.info("用户队列已空, 请确保并发数小于等于用户队列数")
        self.username = user
        global WORKER_ID
        self.work_id = WORKER_ID
        log.debug(f"worker: {self.work_id}, {self.username}, TaskSet on_start()")
        
    def on_stop(self):
        log.debug(f"worker: {self.work_id}, {self.username}, TaskSet on_stop()")
        
    @task
    def test_public_route(self):
        log.debug(f"worker: {self.work_id}, {self.username}, TaskSet @task")
        time.sleep(1)


def setup_test_users(environment, msg, **kwargs):
    # 通过消息机制，将用户数据分发到不同Worker上
    for user in msg.data["users"]:
        users_queue.put(user)
    # 此时更新WORKER_ID全局变量
    global WORKER_ID
    WORKER_ID = msg.data["worker"]
    log.debug(f"worker: {WORKER_ID}, setup_test_users message")
    
    
@events.init.add_listener
def init_event(environment, **kwargs):
    
    # 注册消息,用于接收MasterRunner发送的消息
    if not isinstance(environment.runner, MasterRunner):
        environment.runner.register_message("setup_test_users", setup_test_users)
        # 此阶段woker实例会生成一个随机id，locust内部传给master
        log.debug("worker init event")
    else:
        log.debug("master init event")
        
@events.test_start.add_listener
def test_start_event(environment, **kwargs):
    # 在Master上进行用户分发
    if isinstance(environment.runner, MasterRunner):
        log.debug("master, test_start event")
        worker_count = environment.runner.worker_count
        # 根据worker数量计算每个worker需要的数据大小(即用户数量)
        chunk_size = int(len(USER_LIST) / worker_count)
        # environment.runner.clients 是一个列表，里面放的是每个worker的ID
        # 注：只有在test_start阶段,worker实例都已经启动后，master才能获取到所有worker id的信息
        for i, worker in enumerate(environment.runner.clients):
            # 通过数据大小计算列表的开始、结束下标
            start_index = i * chunk_size
            end_index = start_index + chunk_size if i + 1 < worker_count else len(USER_LIST)

            # 发送消息给setup_test_users，并且指定worker
            data = {"worker": worker, "users": USER_LIST[start_index:end_index]}
            # 发送用户信息到不同worker
            environment.runner.send_message("setup_test_users", data, worker)
    else:
        # worker实例，此时可以拿到worker id
        global WORKER_ID
        log.debug(f"worker: {WORKER_ID}, test_start event")
    
@events.test_stopping.add_listener
def test_stopping_event(environment, **kwargs):
    
    if isinstance(environment.runner, MasterRunner):
        log.debug("master, test_stopping event")
    else:
        global WORKER_ID
        log.debug(f"worker: {WORKER_ID}, test_stopping event")

@events.test_stop.add_listener
def test_stop_event(environment, **kwargs):

    if isinstance(environment.runner, MasterRunner):
        log.debug("master, test_stop event")
    else:
        global WORKER_ID
        log.debug(f"worker: {WORKER_ID}, test_stop event")

@events.quitting.add_listener
def quitting_event(environment, **kwargs):
    if isinstance(environment.runner, MasterRunner):
        log.debug("master, quitting event")
    else:
        global WORKER_ID
        log.debug(f"worker: {WORKER_ID}, quitting event")

@events.quit.add_listener
def quit_event(exit_code):
    global WORKER_ID
    if WORKER_ID is None:
        log.debug("master, quit event")
    else:
        log.debug(f"worker: {WORKER_ID}, quit event")
    
class MockUser(FastHttpUser):
    host = LOCUST_HOST
    tasks = [TestCasesTasks]
     
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        global WORKER_ID
        log.debug(f"worker: {WORKER_ID}, MockUser __init__")
     
if __name__ == "__main__":
    locust_file = os.path.abspath(__file__)
    # 启动2个worker
    for index in range(2):
        print("启动worker" + str(index))
        Popen(f"locust -f {locust_file} --worker", shell=True)
    # 启动master
    os.system(f"locust -f {locust_file} --host {LOCUST_HOST} --headless --users 2 --spawn-rate 2 --run-time 1s --master")