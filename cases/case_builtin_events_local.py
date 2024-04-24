import os,time
from locust import HttpUser,FastHttpUser, task, TaskSet, events, run_single_user
from loguru import logger as log
LOCUST_HOST = "http://0.0.0.0:8089"


class TestCasesTasks(TaskSet):
    def on_start(self):
        log.debug("TaskSet on_start()")
        
    def on_stop(self):
        log.debug("TaskSet on_stop()")
        
    @task
    def test_public_route(self):
        log.debug("TaskSet @task")
        time.sleep(1)

@events.init.add_listener
def init_event(environment, **kwargs):
    log.debug("init event")

@events.test_start.add_listener
def test_start_event(environment, **kwargs):
    log.debug("test_start event")
    
@events.test_stopping.add_listener
def test_stopping_event(environment, **kwargs):
    log.debug("test_stopping event")

@events.test_stop.add_listener
def test_stop_event(environment, **kwargs):
    log.debug("test_stop event")

@events.quitting.add_listener
def quitting_event(environment, **kwargs):
    log.debug("quitting event")

@events.quit.add_listener
def quit_event(exit_code):
    log.debug("quit event")
    
class MockUser(FastHttpUser):
    host = LOCUST_HOST
    tasks = [TestCasesTasks]
     
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        log.debug("MockUser Class")
     
if __name__ == "__main__":
    locust_file = os.path.abspath(__file__)
    os.system(f"locust -f {locust_file} --host {LOCUST_HOST} --headless --users 2 --spawn-rate 2 --run-time 1s")