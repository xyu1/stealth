import falcon

from tests import V1Base


class TestRootController(V1Base):

    def test_get(self):
        response = self.simulate_get('/', headers={})
        self.assertEqual(self.srmock.status, falcon.HTTP_404)

        response = self.simulate_get('/',
                                     headers={'x-project-id':
                                              self.create_project_id()})
        self.assertEqual(self.srmock.status, falcon.HTTP_404)

    def test_get_not_found(self):

        response = self.simulate_get('/a/bogus/url',
                                     headers={'x-project-id':
                                              self.create_project_id()})
        self.assertEqual(self.srmock.status, falcon.HTTP_404)
