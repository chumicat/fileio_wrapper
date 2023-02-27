import os
import shutil
import sys
import threading
import unittest
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
if os.getenv("GITHUB_ACTIONS"):
    from fileio_wrapper import Fileio
else:
    from src.fileio_wrapper import Fileio
from datetime import datetime, timedelta
from queue import Queue
from ratelimit import limits, sleep_and_retry


if os.path.exists('fileio_api_key.txt'):
    with open('fileio_api_key.txt', 'r') as f:
        fileio_api_key = f.read().strip()
elif os.path.exists('./tests/fileio_api_key.txt'):
    with open('./tests/fileio_api_key.txt', 'r') as f:
        fileio_api_key = f.read().strip()
else:
    fileio_api_key = os.environ.get('FILEIO_API_KEY')

if fileio_api_key:
    print("I ve got API key with length {}".format(len(fileio_api_key)))
fileio = Fileio(fileio_api_key)
rate = 3


@sleep_and_retry
@limits(calls=rate, period=1)
def threaded_function(q: Queue, c: callable, a: tuple):
    resp = c(*a)
    print(resp)
    q.put(resp)
    return


class TestFileioWrapper(unittest.TestCase):
    def setUp(self):
        os.makedirs('./tt', exist_ok=True)
        with open('a.txt', "w") as f:
            f.write("Hello")
        with open('b.txt', "w") as f:
            f.write("Hello")

    def tearDown(self):
        shutil.rmtree('./tt')
        os.remove('a.txt')
        for file in ['a.txt', 'b.txt', 'aaa.cc', '_aaa.cc']:
            if os.path.exists(file):
                os.remove(file)

    @unittest.skip("Not threading test. As an code Archived.")
    def test_upload_no_auth_no_threading(self):
        self.assertTrue(Fileio.upload('a.txt')['success'])
        self.assertTrue(Fileio.upload('a.txt', '5m')['success'])
        self.assertTrue(Fileio.upload('a.txt', (datetime.now() + timedelta(seconds=300)).isoformat())['success'])
        self.assertTrue(Fileio.upload('a.txt', datetime.now() + timedelta(seconds=300))['success'])
        self.assertTrue(Fileio.upload('a.txt', timedelta(seconds=300))['success'])
        self.test_delete()

    def test_upload_no_auth_with_threading(self):
        q = Queue()
        threading_list = []
        threading_list.append(threading.Thread(target=threaded_function, args=(q, Fileio.upload, ('a.txt',))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, Fileio.upload, ('a.txt', '5m'))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, Fileio.upload, ('a.txt', (datetime.now() + timedelta(seconds=300)).isoformat()))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, Fileio.upload, ('a.txt', datetime.now() + timedelta(seconds=300)))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, Fileio.upload, ('a.txt', timedelta(seconds=300)))))

        for t in threading_list:
            t.start()

        for t in threading_list:
            t.join()
            self.assertTrue(q.get()['success'])

        self.test_delete()

    @unittest.skip("Not threading test. As an code Archived.")
    def test_upload_with_auth_no_threading(self):
        self.assertTrue(fileio.upload('a.txt')['success'])
        self.assertTrue(fileio.upload('a.txt', '5m')['success'])
        self.assertTrue(fileio.upload('a.txt', (datetime.now() + timedelta(seconds=300)).isoformat())['success'])
        self.assertTrue(fileio.upload('a.txt', datetime.now() + timedelta(seconds=300))['success'])
        self.assertTrue(fileio.upload('a.txt', timedelta(seconds=300))['success'])
        self.test_delete()

    def test_upload_with_auth_with_threading(self):
        q = Queue()
        threading_list = []
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.upload, ('a.txt',))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.upload, ('a.txt', '5m'))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.upload, ('a.txt', (datetime.now() + timedelta(seconds=300)).isoformat()))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.upload, ('a.txt', datetime.now() + timedelta(seconds=300)))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.upload, ('a.txt', timedelta(seconds=300)))))

        for t in threading_list:
            t.start()

        for t in threading_list:
            t.join()
            self.assertTrue(q.get()['success'])

        self.test_delete()

    def test_me(self):
        self.assertTrue(fileio.me()['success'])

    def test_list(self):
        self.assertTrue(fileio.list()['success'])
        self.assertTrue(fileio.list(search='txt', sort='expires', offset=4, limit=5)['success'])

    @unittest.skip("Not threading test. As an code Archived.")
    def test_download_no_threading(self):
        resp = fileio.list()
        self.assertTrue(fileio.upload('a.txt')['success'])
        self.assertTrue(fileio.upload('a.txt')['success'])
        self.assertTrue(fileio.upload('a.txt')['success'])
        self.assertTrue(fileio.upload('a.txt')['success'])
        self.assertTrue(fileio.upload('a.txt')['success'])
        self.assertTrue(fileio.upload('a.txt')['success'])
        self.assertTrue(fileio.upload('a.txt')['success'])
        self.assertTrue(fileio.upload('a.txt')['success'])
        self.assertEqual(b'Hello', Fileio.download(resp['nodes'][0]['key'])['content'])
        self.assertTrue(Fileio.download(resp['nodes'][1]['key'], "aaa.cc"))
        self.assertTrue(Fileio.download(resp['nodes'][2]['key'], "tt"))
        self.assertTrue(Fileio.download(resp['nodes'][3]['key'], "tt/bbb.dd"))
        self.assertEqual(b'Hello', fileio.download(resp['nodes'][4]['key'])['content'])
        self.assertTrue(fileio.download(resp['nodes'][5]['key'], "_aaa.cc"))
        self.assertTrue(fileio.download(resp['nodes'][6]['key'], "tt"))
        self.assertTrue(fileio.download(resp['nodes'][7]['key'], "tt/_bbb.dd"))

    def test_download_threading(self):
        q = Queue()
        threading_list = []
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.upload, ('a.txt',))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.upload, ('a.txt',))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.upload, ('a.txt',))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.upload, ('a.txt',))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.upload, ('a.txt',))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.upload, ('a.txt',))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.upload, ('a.txt',))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.upload, ('a.txt',))))

        for t in threading_list:
            t.start()

        for t in threading_list:
            t.join()
            resp = q.get()
            self.assertTrue(resp['success'])
        threading_list = []

        resp = fileio.list()
        threading_list.append(threading.Thread(target=threaded_function, args=(q, Fileio.download, (resp['nodes'][0]['key'], ))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, Fileio.download, (resp['nodes'][1]['key'], "aaa.cc"))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, Fileio.download, (resp['nodes'][2]['key'], "tt"))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, Fileio.download, (resp['nodes'][3]['key'], "tt/bbb.dd"))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.download, (resp['nodes'][4]['key'], ))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.download, (resp['nodes'][5]['key'], "_aaa.cc"))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.download, (resp['nodes'][6]['key'], "tt"))))
        threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.download, (resp['nodes'][7]['key'], "tt/_bbb.dd"))))

        for t in threading_list:
            t.start()

        success_cnt = 0
        for t in threading_list:
            t.join()
            resp = q.get()
            self.assertTrue(resp['success'])
            success_cnt += 1 if 'content' in resp and resp['content'] == b'Hello' else 0
        self.assertEqual(2, success_cnt)

    def test_update(self):
        self.assertTrue(fileio.upload('a.txt')['success'])
        resp = fileio.list()
        self.assertTrue(fileio.update(resp['nodes'][0]['key'], file='b.txt', expires='20m', max_downloads=1, \
                                      auto_delete=True, mode='replace_all'))
        self.assertTrue(fileio.update(resp['nodes'][0]['key'], expires=timedelta(seconds=60000), mode='replace_partial'))
        self.assertTrue(fileio.update(resp['nodes'][0]['key'], file='a.txt'))
        self.test_delete()

    def test_delete(self):
        q = Queue()
        threading_list = []
        for item in fileio.list()['nodes']:
            threading_list.append(threading.Thread(target=threaded_function, args=(q, fileio.delete, (item['key'],))))

        for t in threading_list:
            t.start()

        for t in threading_list:
            t.join()
            self.assertTrue(q.get()['success'])


if __name__ == '__main__':
    unittest.main()

