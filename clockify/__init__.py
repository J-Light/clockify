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

class _App():
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=missing-docstring
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
            response = rqs.put(self.uri, json=self.body, params=self.parmas, headers=self.headers)
        elif self.method.lower() == 'post':
            response = rqs.post(self.uri, json=self.body, headers=self.headers)
        elif self.method.lower() == 'delete':
            response = rqs.delete(self.uri, params=self.parmas, headers=self.headers)
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
    ranfn = lambda: random.randint(0, 255)
    return '#%02X%02X%02X' % (ranfn(), ranfn(), ranfn())

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
            "color" : _get_color(),
            "memberships": [
                {
                    "userId": user_id,
                    "membershipStatus" : "ACTIVE",
                    "membershipType" : "PROJECT"
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
        proj = Clockify.get_project(workspace_id, project_id)
        app = _App(Clockify.api_key)
        app.path = f'/workspaces/{workspace_id}/projects/{project_id}'
        app.method = 'put'
        app.body = {
            "id": proj['id'],
            "name": proj['name'],
            "color": proj['color'],
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
        app.working_endpoint = True
        app.path = f'/workspaces/{workspace_id}/projects/{project_id}/restore'
        return app.execute()

    def get_project_users(workspace_id, project_id):
        '''
        Get all project users
        '''
        app = _App(Clockify.api_key)
        app.working_endpoint = True
        app.path = f'/workspaces/{workspace_id}/projects/{project_id}/users'
        return app.execute()


    def add_project_member(workspace_id, project_id, user_id):
        '''
        Add member to project
        '''
        app = _App(Clockify.api_key)
        app.method = 'post'
        app.working_endpoint = True
        app.path = f'/workspaces/{workspace_id}/projects/{project_id}/team'
        app.body = {
            "userIds": [user_id],
            "userGroupIds": []}
        return app.execute()

    def remove_project_member(workspace_id, project_id, user_id):
        '''
        Remove member from project
        '''
        app = _App(Clockify.api_key)
        app.method = 'delete'
        app.working_endpoint = True
        app.path = f'/workspaces/{workspace_id}/projects/{project_id}/users/{user_id}/membership'
        return app.execute()

    def update_project_name(new_name, workspace_id, project_id):
        '''
        Update a projects name'
        '''
        proj = Clockify.get_project(workspace_id, project_id)
        app = _App(Clockify.api_key)
        app.working_endpoint = True
        app.method = 'put'
        app.path = f'/workspaces/{workspace_id}/projects/{project_id}'
        app.body = {
            "id": proj['id'],
            "name": new_name,
            "hourlyRate": proj['hourlyRate'],
            "clientId": proj['clientId'],
            "billable": proj['billable'],
            "color": proj['color'],
            "estimate": proj['estimate'],
            "isPublic":proj['public']}
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
            app.parmas = {'page' : page}
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
            'email' : email_id,
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
            'name' : name
        }
        clients = app.execute()
        for client in clients:
            if client['name'] == name:
                return client       

    def create_client(name, workspace_id):
        '''
        Create a new Client
        '''
        app = _App(Clockify.api_key)
        app.method = 'post'
        app.path = f'/workspaces/{workspace_id}/clients'
        app.body = {
            'name' : name
        }
        return app.execute()
