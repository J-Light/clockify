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
import logging
import random
import requests as rqs

LOG = logging.getLogger('clockify')


class ClockifyUserExistError(Exception):
    "User does not exist"
    def __init__(self):
        super().__init__()
        self.message = 'User does not exist'


class ClockifyClientExistError(Exception):
    "Client does not exist"
    def __init__(self):
        super().__init__()
        self.message = 'Client does not exist'


class _App():
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=missing-docstring
    def __init__(self, api_key):
        self._api_key = api_key
        self.endpoint = 'https://api.clockify.me/api/v1'
        self.working_endpoint = False
        self.path = '/'
        self.parmas = {}
        self.body = {}
        self.method = 'get'

    @property
    def uri(self):
        return ''.join([self.endpoint, self.path])

    @property
    def headers(self):
        return {
            'X-Api-Key': self._api_key
        }

    def execute(self):
        if self.method.lower() == 'get':
            response = rqs.get(
                self.uri,
                params=self.parmas,
                headers=self.headers)
        elif self.method.lower() == 'put':
            response = rqs.put(
                self.uri,
                json=self.body,
                params=self.parmas,
                headers=self.headers)
        elif self.method.lower() == 'post':
            response = rqs.post(self.uri, json=self.body, headers=self.headers)
        elif self.method.lower() == 'delete':
            response = rqs.delete(
                self.uri,
                params=self.parmas,
                headers=self.headers)
        elif self.method.lower() == 'patch':
            response = rqs.patch(
                self.uri,
                json=self.body,
                params=self.parmas,
                headers=self.headers)
        else:
            raise NotImplementedError
        try:
            response.raise_for_status()
        except Exception as ex:
            LOG.error('Failed with error: %s', response.text)
            raise ex
        return response.json()


def _get_color():
    'Gen color code'
    idx = random.randint(0, len(COLORS))
    return '#%02X%02X%02X' % COLORS[idx]


class Clockify():
    '''
    Main app to implement Clockify methods
    '''
    # pylint: disable=no-self-argument
    api_key = ''

    def create_project(name, workspace_id, client_id, user_ids):
        '''
        Create project:
           create_project(name, workspace_id, client_id, user_ids)
        '''
        app = _App(Clockify.api_key)
        app.method = 'post'
        app.path = f'/workspaces/{workspace_id}/projects'
        app.body = {
            "name": name,
            "clientId": client_id,
            "isPublic": False,
            "billable": True,
            "color": _get_color(),
            "memberships": [
                {
                    "userId": user_id,
                    "membershipStatus": "ACTIVE",
                    "membershipType": "PROJECT"
                }
                for user_id in user_ids
            ]
        }
        return app.execute()

    def get_project(workspace_id, project_id):
        '''
        Get an existing project
        args: workspaceId
              projectId
        '''
        app = _App(Clockify.api_key)
        app.path = f'/workspaces/{workspace_id}/projects/{project_id}'
        return app.execute()

    def archive_project(workspace_id, project_id):
        '''
        Archive existing project
        args: workspaceId
              projectId
        '''
        app = _App(Clockify.api_key)
        app.path = f'/workspaces/{workspace_id}/projects/{project_id}'
        app.method = 'put'
        app.body = {
            "archived": True
        }
        return app.execute()

    def restore_project(workspace_id, project_id):
        '''
        Re-Open existing project
        args: workspaceId
              projectId
        '''
        app = _App(Clockify.api_key)
        app.path = f'/workspaces/{workspace_id}/projects/{project_id}'
        app.method = 'put'
        app.body = {
            "archived": False
        }
        return app.execute()

    def get_project_members(workspace_id, project_id):
        '''
        Get all project users
        '''
        app = _App(Clockify.api_key)
        app.path = f'/workspaces/{workspace_id}/projects/{project_id}'
        result = app.execute()
        return [x['userId'] for x in result['memberships']]

    def add_project_member(workspace_id, project_id, user_id):
        '''
        Append user to project
        '''
        members = Clockify.get_project_members(workspace_id, project_id)
        members.append(user_id)
        user_ids = list(set(members))
        return Clockify.set_project_members(workspace_id, project_id, user_ids)

    def set_project_members(workspace_id, project_id, user_ids):
        '''
        Set projects members
        '''
        app = _App(Clockify.api_key)
        app.method = 'patch'
        app.path = (f'/workspaces/{workspace_id}'
                    f'/projects/{project_id}/memberships')
        app.body = {
            "memberships": [
                {
                    "userId": user_id
                }
                for user_id in user_ids]
        }
        return app.execute()

    def update_project_name(new_name, workspace_id, project_id):
        '''
        Update a projects name'
        '''
        app = _App(Clockify.api_key)
        app.method = 'put'
        app.path = f'/workspaces/{workspace_id}/projects/{project_id}'
        app.body = {
            "name": new_name
        }
        return app.execute()

    def get_users(workspace_id):
        '''
        Get all users on workspace
        '''
        app = _App(Clockify.api_key)
        app.path = f'/workspaces/{workspace_id}/users'

        page = 1
        users = []
        while True:
            app.parmas = {'page': page}
            resp = app.execute()
            if not resp:
                break
            users.extend(resp)
            page = page + 1
        return users

    def get_user(workspace_id, email_id):
        '''
        Get users on workspace with email_id
        '''
        app = _App(Clockify.api_key)
        app.path = f'/workspaces/{workspace_id}/users'

        app.parmas = {
            'email': email_id,
            'memberships': 'NONE'
        }
        resp = app.execute()
        if not resp:
            raise ClockifyUserExistError
        return resp[0]

    def get_client(name, workspace_id):
        '''
        Find a client by name
        '''
        app = _App(Clockify.api_key)
        app.path = f'/workspaces/{workspace_id}/clients'
        app.parmas = {
            'name': name
        }
        clients = app.execute()
        for client in clients:
            if client['name'] == name:
                return client
        raise ClockifyClientExistError

    def create_client(name, workspace_id):
        '''
        Create a new Client
        '''
        app = _App(Clockify.api_key)
        app.method = 'post'
        app.path = f'/workspaces/{workspace_id}/clients'
        app.body = {
            'name': name
        }
        return app.execute()


COLORS = [
    (0, 255, 0),
    (255, 0, 255),
    (0, 128, 255),
    (255, 128, 0),
    (125, 43, 134),
    (255, 0, 0),
    (7, 0, 245),
    (0, 128, 0),
    (0, 128, 128),
    (138, 89, 5),
    (0, 0, 128),
    (139, 93, 247),
    (135, 188, 1),
    (253, 55, 127),
    (9, 228, 110),
    (128, 0, 255),
    (128, 0, 0),
    (191, 124, 97),
    (48, 58, 63),
    (48, 81, 187),
    (59, 167, 63),
    (200, 3, 171),
    (5, 186, 197),
    (184, 29, 64),
    (102, 110, 93),
    (187, 81, 177),
    (103, 135, 173),
    (237, 69, 250),
    (73, 11, 189),
    (237, 60, 16),
    (23, 197, 10),
    (186, 141, 21),
    (49, 182, 136),
    (37, 56, 250),
    (79, 4, 91),
    (10, 60, 1),
    (251, 2, 88),
    (3, 63, 126),
    (0, 107, 62),
    (81, 126, 4),
    (2, 31, 180),
    (180, 40, 246),
    (29, 134, 199),
    (144, 154, 71),
    (118, 42, 60),
    (70, 114, 241),
    (13, 12, 65),
    (79, 47, 6),
    (100, 51, 224),
    (196, 73, 110),
    (253, 103, 66),
    (141, 13, 185),
    (193, 0, 7),
    (125, 88, 169),
    (187, 87, 47),
    (74, 72, 125),
    (33, 172, 247),
    (251, 44, 192),
    (165, 0, 123),
    (96, 153, 110),
    (61, 4, 8),
    (2, 182, 89),
    (71, 10, 243),
    (167, 44, 1),
    (3, 159, 37),
    (57, 211, 81)]
