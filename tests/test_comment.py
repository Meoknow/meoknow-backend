import os
import unittest, json
from meoknow import create_app, db
from meoknow.model import CatInfo, Comment

class TestComment(unittest.TestCase):

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
        Bob, BobUserId = self.get_token("Bob", False)
        Carol, CarolUserId = self.get_token("Carol", False)
        Dave, DaveUserId = self.get_token("Dave", False)
        Eve, EveUserId = self.get_token("Eve", False)
        
        with self.app.app_context():
            # db.create_all()

            cat = CatInfo(
                name="name",
                img_url="",
                gender="",
                health_status="",
                desexing_status="",
                description=""
            )
            db.session.add(cat)

            for user in [AliceUserId, BobUserId, CarolUserId, DaveUserId, EveUserId]:
                for i in range(6):
                    comment = Comment(
                        like=0,
                        owner=user,
                        cat_id=1,
                        content="content",
                        images_path="[]",
                        is_hidden=False,
                    )
                    db.session.add(comment)
            
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

    def test_new_comments(self):

        correct_headers = {
            "Auth-Token": self.get_token("Alice", is_admin=False)[0]
        }
        wrong_headers = {"Auth-Token": "nfjigqripqwrt"}

        correct_contents = [
            {
                "content": "comments",
                "images": [self.gen_image()]
            },
            {
                "content": "comments",
                "images": []
            },
            {
                "content": "comments",
                "images": [self.gen_image() for i in range(9)]
            }
        ]

        wrong_cases = [
            {
                "payload": {
                    "content": 1
                },
                "expected": {
                    "code": 101,
                    "msg": "Invalid Content.",
                    "data": {}
                }
            },
            {
                "payload": {
                    "content": None
                },
                "expected": {
                    "code": 101,
                    "msg": "Invalid Content.",
                    "data": {}
                }
            },
            {
                "payload": {
                    "content": []
                },
                "expected": {
                    "code": 101,
                    "msg": "Invalid Content.",
                    "data": {}
                }
            },
            {
                "payload": {
                    "content": ""
                },
                "expected": {
                    "code": 101,
                    "msg": "Invalid Content.",
                    "data": {}
                }
            },
            {
                "payload": {
                    "content": "123",
                    "images": ""
                },
                "expected": {
                    "code": 102,
                    "msg": "Invalid Image.",
                    "data": {}
                }
            },
            {
                "payload": {
                    "content": "123",
                    "images": ["123"]
                },
                "expected": {
                    "code": 102,
                    "msg": "Invalid Image.",
                    "data": {}
                }
            },
            {
                "payload": {
                    "content": "123",
                    "images": [self.gen_image()] * 10
                },
                "expected": {
                    "code": 102,
                    "msg": "Invalid Image.",
                    "data": {}
                }
            }
        ]

        resp = self.client.post("/cats/1/comments/")
        self.myAssertAuthFailed(resp)

        resp = self.client.post("/cats/1/comments/", headers=wrong_headers)
        self.myAssertAuthFailed(resp)

        for case in wrong_cases:
            payload, expected = case["payload"], case["expected"]
            resp = self.client.post(
                "/cats/1/comments/",
                data=json.dumps(payload),
                content_type='application/json',
                headers=correct_headers
            )
            self.assertEqual(json.loads(resp.data), expected)

        for content in correct_contents:
            resp = self.client.post(
                "/cats/1/comments/",
                data=json.dumps(content),
                content_type='application/json',
                headers=correct_headers
            )
            data = json.loads(resp.data)
            self.assertEqual(data, {
                "code": 0,
                "msg": "",
                "data": {}
            })

            resp = self.client.post(
                "/cats/2/comments/",
                data=json.dumps(content),
                content_type='application/json',
                headers=correct_headers
            )
            data = json.loads(resp.data)
            self.assertEqual(data, {
                "code": 100,
                "msg": "Invalid parameter: cat_id.",
                "data": {}
            })

    def test_get_comments(self):
        
        correct_headers = {
            "Auth-Token": self.get_token("Alice", is_admin=False)[0]
        }
        wrong_headers = {"Auth-Token": "nfjigqripqwrt"}

        resp = self.client.get("/cats/1/comments/")
        self.myAssertAuthFailed(resp)

        resp = self.client.get("/cats/1/comments/", headers=wrong_headers)
        self.myAssertAuthFailed(resp)

        resp = self.client.get("/cats/2/comments/", query_string={
            "page_size": 20,
            "page": 1
        }, headers=correct_headers)
        data = json.loads(resp.data)
        self.assertEqual(data, {
            "code": 100,
            "msg": "Invalid parameter: cat_id.",
            "data": {}
        })

        test_cases = [
            {
                "page_size": "",
                "page": 1
            },
            {
                "page_size": "f",
                "page": 1
            },
            {
                "page_size": 0,
                "page": 1
            },
            {
                "page_size": 14,
                "page": "f"
            },
            {
                "page_size": -1,
                "page": 1
            },
            {
                "page_size": 1,
                "page": -1
            }
        ]

        for payload in test_cases:
            resp = self.client.get(
                "/cats/1/comments/",
                query_string=payload,
                headers=correct_headers
            )
            data = json.loads(resp.data)
            self.assertEqual(data, {
                "code": 101,
                "msg": "Invalid page_size or page.",
                "data": {}
            })

        resp = self.client.get("/cats/1/comments/", query_string={
            "page_size": 20,
            "page": 1
        }, headers=correct_headers)
        data = json.loads(resp.data)
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["msg"], "")
        self.assertEqual(data["data"]["total"], 30)
        self.assertEqual(len(data["data"]["comments"]), 20)
        for idx, comment in enumerate(data["data"]["comments"]):
            self.assertEqual(comment["comment_id"], 30 - idx)
        
        resp = self.client.get("/cats/1/comments/", query_string={
            "page_size": 20,
            "page": 2
        }, headers=correct_headers)
        data = json.loads(resp.data)
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["msg"], "")
        self.assertEqual(data["data"]["total"], 30)
        self.assertEqual(len(data["data"]["comments"]), 10)
        for idx, comment in enumerate(data["data"]["comments"]):
            self.assertEqual(comment["comment_id"], 10 - idx)
        
        resp = self.client.get("/cats/1/comments/", query_string={
            "page_size": 30,
            "page": 1
        }, headers=correct_headers)
        data = json.loads(resp.data)
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["msg"], "")
        self.assertEqual(data["data"]["total"], 30)
        self.assertEqual(len(data["data"]["comments"]), 30)
        for idx, comment in enumerate(data["data"]["comments"]):
            self.assertEqual(comment["comment_id"], 30 - idx)
        
        resp = self.client.get("/cats/1/comments/", query_string={
            "page_size": 30,
            "page": 2
        }, headers=correct_headers)
        data = json.loads(resp.data)
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["msg"], "")
        self.assertEqual(data["data"]["total"], 30)
        self.assertEqual(len(data["data"]["comments"]), 0)
    
        resp = self.client.get("/cats/1/comments/", query_string={
            "page_size": 1,
            "page": 25
        }, headers=correct_headers)
        data = json.loads(resp.data)
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["msg"], "")
        self.assertEqual(data["data"]["total"], 30)
        self.assertEqual(len(data["data"]["comments"]), 1)
        self.assertEqual(data["data"]["comments"][0]["comment_id"], 6)
    
    def test_delete_comment(self):
        correct_headers = {"Auth-Token": self.get_token("Alice", is_admin=True)[0]}
        wrong_headers_1 = {"Auth-Token": self.get_token("Alice", is_admin=False)[0]}
        wrong_headers_2 = {"Auth-Token": "nfjigqripqwrt"}

        resp = self.client.delete("/comments/1")
        self.myAssertAuthFailed(resp)

        resp = self.client.delete("/comments/1", headers=wrong_headers_1)
        self.myAssertPermissionDenied(resp)

        resp = self.client.delete("/comments/1", headers=wrong_headers_2)
        self.myAssertAuthFailed(resp)

        resp = self.client.delete("/comments/1", headers=correct_headers)
        self.assertEqual(
            json.loads(resp.data), {
                "code": 0,
                "msg": "",
                "data": {}
            }
        )

        wrong_cases = ["31", "0", "2147483647"]
        for comment_id in wrong_cases:
            resp = self.client.delete("/comments/" + comment_id, headers=correct_headers)
            self.assertEqual(
                json.loads(resp.data), {
                    "code": 100,
                    "msg": "Invalid parameter: comment_id.",
                    "data": {}
                }
            )
    
    def test_like_and_unlike(self):
        correct_headers_1 = {"Auth-Token": self.get_token("Alice", is_admin=False)[0]}
        correct_headers_2 = {"Auth-Token": self.get_token("Bob", is_admin=False)[0]}
        wrong_headers = {"Auth-Token": "nfjigqripqwrt"}

        resp = self.client.put("/comments/1/like")
        self.myAssertAuthFailed(resp)

        resp = self.client.delete("/comments/1/like")
        self.myAssertAuthFailed(resp)

        resp = self.client.put("/comments/1/like", headers=wrong_headers)
        self.myAssertAuthFailed(resp)

        resp = self.client.delete("/comments/1/like", headers=wrong_headers)
        self.myAssertAuthFailed(resp)

        resp = self.client.put("/comments/31/like", headers=correct_headers_1)
        self.assertEqual(
            json.loads(resp.data), {
                "code": 100,
                "msg": "Invalid parameter: comment_id.",
                "data": {}
            }
        )

        resp = self.client.delete("/comments/31/like", headers=correct_headers_2)
        self.assertEqual(
            json.loads(resp.data), {
                "code": 100,
                "msg": "Invalid parameter: comment_id.",
                "data": {}
            }
        )

        actions = [
            {
                "action": "put",
                "headers": correct_headers_1,
                "like": 1
            },
            {
                "action": "put",
                "headers": correct_headers_1,
                "like": 1
            },
            {
                "action": "put",
                "headers": correct_headers_2,
                "like": 2
            },
            {
                "action": "delete",
                "headers": correct_headers_2,
                "like": 1
            },
            {
                "action": "delete",
                "headers": correct_headers_2,
                "like": 1
            },
            {
                "action": "delete",
                "headers": correct_headers_1,
                "like": 0
            }
        ]

        for action in actions:
            if action["action"] == "put":
                method = self.client.put
            else:
                assert action["action"] == "delete"
                method = self.client.delete
            resp = method("/comments/1/like", headers=action["headers"])
            self.assertEqual(
                json.loads(resp.data), {
                    "code": 0,
                    "msg": "",
                    "data": {
                        "like": action["like"]
                    }
                }
            )
        
    def test_recent_liked(self):
        correct_headers_1 = {"Auth-Token": self.AliceToken}
        correct_headers_2 = {"Auth-Token": self.get_token("Bob", is_admin=False)[0]}
        correct_headers_3 = {"Auth-Token": self.get_token("Carol", is_admin=False)[0]}
        correct_headers_4 = {"Auth-Token": self.get_token("Dave", is_admin=False)[0]}
        wrong_headers = {"Auth-Token": "nfjigqripqwrt"}

        resp = self.client.get("/status/likes")
        self.myAssertAuthFailed(resp)

        resp = self.client.get("/status/likes", headers=wrong_headers)
        self.myAssertAuthFailed(resp)

        resp = self.client.get("/status/likes", headers=correct_headers_1)
        self.assertEqual(
            json.loads(resp.data), {
                "code": 0,
                "msg": "",
                "data": {
                    "count": 0,
                    "likes": []
                }
            }
        )

        self.client.put("/comments/1/like", headers=correct_headers_2)
        self.client.put("/comments/1/like", headers=correct_headers_3)
        self.client.put("/comments/1/like", headers=correct_headers_4)

        resp = self.client.get("/status/likes", headers=correct_headers_1)
        data = json.loads(resp.data)
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["msg"], "")
        self.assertEqual(data["data"]["count"], 3)
        self.assertEqual(data["data"]["likes"][0]["username"], "Dave")
        self.assertEqual(data["data"]["likes"][1]["username"], "Carol")
        self.assertEqual(data["data"]["likes"][2]["username"], "Bob")

        resp = self.client.get("/status/likes", query_string={
            "page_size": 1,
            "page": 3
        }, headers=correct_headers_1)
        data = json.loads(resp.data)
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["msg"], "")
        self.assertEqual(data["data"]["count"], 3)
        self.assertEqual(data["data"]["likes"][0]["username"], "Bob")
    
    def test_get_photo(self):
        correct_headers = {
            "Auth-Token": self.get_token("Alice", is_admin=False)[0]
        }
        resp = self.client.post(
            "/cats/1/comments/",
            data=json.dumps({
                "content": "123",
                "images": [self.gen_image()]
            }),
            content_type='application/json',
            headers=correct_headers
        )

        resp = self.client.get("/cats/1/comments/", headers=correct_headers)
        url = json.loads(resp.data)["data"]["comments"][0]["images"][0]
        self.assertEqual(len(self.client.get(url).data), 651) # image size

    def test_get_comment(self):
        correct_headers = {
            "Auth-Token": self.get_token("Alice", is_admin=False)[0]
        }
        wrong_headers = {"Auth-Token": "nfjigqripqwrt"}

        resp = self.client.get("/comments/1")
        self.myAssertAuthFailed(resp)

        resp = self.client.get("/comments/1", headers=wrong_headers)
        self.myAssertAuthFailed(resp)

        resp = self.client.get("/comments/1", headers=correct_headers)
        data = json.loads(resp.data)
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["msg"], "")

        resp = self.client.get("/comments/31", headers=correct_headers)
        self.assertEqual(
            json.loads(resp.data), {
                "code": 100,
                "msg": "Invalid parameter: comment_id.",
                "data": {}
            }
        )


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromModule(TestComment())
    results = unittest.TextTestRunner(verbosity=2).run(suite)
    print(results)