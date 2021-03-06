import os
from datetime import date, datetime
import time
import unittest, json
from meoknow import create_app, db
from meoknow.model import CatInfo, Comment

TEST_PERF_ITER = 20
TEST_STRESS_NUM = 10

class TestCats(unittest.TestCase):

    def get_token(self, username, is_admin):
        params = {"nickname": username}
        if is_admin:
            params["admin"] = True
        resp = self.client.get("/gensession", query_string=params)
        data = json.loads(resp.data)
        return data["data"]["token"], data["data"]["user_id"]

    def gen_image(self):
        return '''
        data:image/jpg;base64,
        /9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
        HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
        MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wgARCAARACoDASIA
        AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAb/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/9oADAMB
        AAIQAxAAAAG/AAAAAB//xAAUEAEAAAAAAAAAAAAAAAAAAABA/9oACAEBAAEFAhf/xAAUEQEAAAAA
        AAAAAAAAAAAAAAAg/9oACAEDAQE/AV//xAAUEQEAAAAAAAAAAAAAAAAAAAAg/9oACAECAQE/AV//
        xAAUEAEAAAAAAAAAAAAAAAAAAABA/9oACAEBAAY/Ahf/xAAUEAEAAAAAAAAAAAAAAAAAAABA/9oA
        CAEBAAE/IRf/2gAMAwEAAgADAAAAEPPPPPPP/8QAFBEBAAAAAAAAAAAAAAAAAAAAIP/aAAgBAwEB
        PxBf/8QAFBEBAAAAAAAAAAAAAAAAAAAAIP/aAAgBAgEBPxBf/8QAFBABAAAAAAAAAAAAAAAAAAAA
        QP/aAAgBAQABPxAX/9k=
        '''.replace("\n", "").replace(" ", "")

    def setUp(self):
        test_instance_path = os.path.join(os.getcwd(), "test_instance")
        self.app = create_app({"instance_path":test_instance_path})
        self.app.testing = True
        self.client = self.app.test_client()
        
        self.AliceToken, AliceUserId = self.get_token("Alice", False)
        
        with self.app.app_context():
            db.create_all()
            names = ["杜若", "麈尾", "雪风", "小宝","姜丝鸭", "小尾巴"]
            for name in names:
                cat = CatInfo(
                    name=name,
                    img_url=name + "_url"
                )
                db.session.add(cat)
        
            db.session.commit()

        
    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def myAssertAuthFailed(self, resp):
        data = json.loads(resp.data)
        self.assertEqual(data, {
            "code": 1,
            "msg": "Invalid token.",
            "data": {}
        })

    def myAssertPermissionDenied(self, resp):
        data = json.loads(resp.data)
        self.assertEqual(data, {
            "code": 3,
            "msg": "Permission Denied.",
            "data": {}
        })

    def test_get_cats(self):
        correct_header = {
            "Auth-Token": self.get_token("Alice", is_admin=False)[0]
        }

        resp = self.client.get(
            "/cats/",
            headers=correct_header
        )
        resp_str = str(json.loads(resp.data))
        # print(resp_str)
        self.assertIn("麈尾", resp_str)

        # correct cat number
        resp = self.client.get(
            "/cats/1",
            headers=correct_header
        )
        resp_str = str(json.loads(resp.data))
        self.assertIn("杜若", resp_str)

        # wrong cat number
        resp = self.client.get(
            "/cats/100",
            headers=correct_header
        )
        resp_str = str(json.loads(resp.data))
        self.assertIn("Invalid", resp_str)

    def test_put_cats(self):
        correct_header = {
            "Auth-Token": self.get_token("Alice", is_admin=True)[0]
        }
        wrong_header = {
            "Auth-Token": self.get_token("Bob", is_admin=False)[0]
        }

        correct_payloads = [
            {
                "name":"1",
                "image":self.gen_image(),
            },
            {
                "name":"2",
                "image":self.gen_image() + "1234",
                "gender":"a",
                "health_status":"b",
                "desexing_status":"c",
                "description":"d"
            }
        ]

        wrong_payloads = [
            {
                "name":"1",
                "image":self.gen_image()
            },
            {
                "name":"3"
            },
            {
                "name":"4",
                "image":"a"
            },
            {
                "image":"2",
                "gender":"a",
                "health_status":"b",
                "desexing_status":"c",
                "description":"d"
            }
        ]
        # Permission denied
        resp = self.client.post(
            "/cats/",
            data=json.dumps(correct_payloads[0]),
            content_type='application/json',
            headers=wrong_header
        )
        self.assertIsNotNone(resp.data)
        resp = str(json.loads(resp.data))
        self.assertIn("Permission", resp)

        for payload in correct_payloads:
            resp = self.client.post(
                "/cats/",
                data=json.dumps(payload),
                content_type='application/json',
                headers=correct_header
            )
            self.assertIsNotNone(resp.data)
            # print(resp.data)
            resp = json.loads(resp.data)
            self.assertDictContainsSubset({
                "code":0,
                "msg":""
            }, resp)
        
        for payload in wrong_payloads:
            resp = self.client.post(
                "/cats/",
                data=json.dumps(payload),
                content_type='application/json',
                headers=correct_header
            )
            # print(resp.data)
            resp = json.loads(resp.data)
            self.assertDictContainsSubset({
                "code":100,
            }, resp)


    def test_identify_perf(self):

        correct_header = {
            "Auth-Token": self.get_token("Alice", is_admin=False)[0]
        }
        # print(correct_header)
        wrong_headers = {"Auth-Token": "nfjigqripqwrt"}

        with open(self.app.instance_path + "/64.txt", "r") as f:
            image = f.readline()
        correct_content = {
            "image": image
        }

        start_time = time.time()
        for iter in range(0, TEST_PERF_ITER):
            
            resp = self.client.post(
                "/identify/",
                data=json.dumps(correct_content),
                content_type='application/json',
                headers=correct_header
            )
            data = json.loads(resp.data)
            self.assertDictContainsSubset({
                "code": 0,
                "msg": ""
            }, data)
        finish_time = time.time()
        print(start_time)
        print(finish_time)
        time_duration = finish_time - start_time
        print("Iter ", TEST_PERF_ITER, " - total time used :", time_duration, "\n average : ", time_duration/TEST_PERF_ITER)
        
        
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromModule(TestCats())
    results = unittest.TextTestRunner(verbosity=2).run(suite)
    print(results)
