'''
Copyright 2019 Nishit Joseph

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import json
import random
import requests as rqs

class _App():
    def __init__(self, api_key):
        self._api_key = api_key
        self.endpoint = 'https://api.clockify.me/api'
        self.v1_endpoint = 'https://api.clockify.me/api/v1'
        self.working_endpoint = False
        self.path = '/'
        self.parmas = {}
        self.body = {}
        self.method = 'get'

    @property
    def uri(self):
        endpoint = self.endpoint if self.working_endpoint else self.v1_endpoint
        return ''.join([endpoint, self.path])

    @property
    def headers(self):
        return {
            'X-Api-Key' : self._api_key
            }

    def execute(self):
        if self.method.lower() == 'get':
            response = rqs.get(self.uri, params=self.parmas, headers=self.headers)
        elif self.method.lower() == 'put':
            response = rqs.put(self.uri, data=self.body, params=self.parmas, headers=self.headers)
        elif self.method.lower() == 'post':
            response = rqs.post(self.uri, json=self.body, headers=self.headers)
        else:
            raise NotImplemented
        response.raise_for_status()            
        return response.json()


class Clockify():
    api_key = ''

    def get_color():
        r = lambda: random.randint(0,255)
        return '#%02X%02X%02X' % (r(),r(),r())

    def create_project(name, workspace_id, client_id, user_id):
        app = _App(Clockify.api_key)
        app.method = 'post'
        app.path = f'/workspaces/{workspace_id}/projects'
        app.body = {
            "name": name,
            "clientId": client_id,
            "isPublic": False,
            "billable": True,
            "color" : Clockify.get_color(),
            "memberships": [ {
                "userId": user_id,
                "membershipStatus" : "ACTIVE",
                "membershipType" : "PROJECT" }]}
        return app.execute()

    def close_project(workspace_id, project_id):
        app = _App(Clockify.api_key)
        app.working_endpoint = True
        # add a time delay
        app.path = f'/workspaces/{workspace_id}/projects/{project_id}/archive'
        result = app.execute()

    def reopen_project(workspace_id, project_id):
        app = _App(Clockify.api_key)
        app.working_endpoint = True
        app.path = f'/workspaces/{workspace_id}/projects/{project_id}/restore'
        result = app.execute()

    def create_user():
        raise NotImplementedError

    def create_client():
        raise NotImplementedError