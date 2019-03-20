from cone.app import testing
from cone.app.browser.contents import ContentsTile
from cone.app.browser.table import TableSlice
from cone.app.browser.utils import make_url
from cone.app.model import BaseNode
from cone.app.testing.mock import CopySupportNode
from cone.tile import render_tile
from cone.tile.tests import TileTestCase
from datetime import datetime
from datetime import timedelta
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Deny
from pyramid.security import Everyone
from pyramid.security import has_permission
import urllib


class NeverShownChild(BaseNode):
    __acl__ = [(Deny, Everyone, ALL_PERMISSIONS)]


class TestBrowserContents(TileTestCase):
    layer = testing.security

    def create_dummy_model(self):
        created = datetime(2011, 3, 14)
        delta = timedelta(1)
        modified = created + delta
        model = BaseNode()
        for i in range(19):
            model[str(i)] = BaseNode()
            model[str(i)].properties.action_view = True
            model[str(i)].properties.action_edit = True
            model[str(i)].properties.action_delete = True
            model[str(i)].metadata.title = str(i) + ' Title'
            model[str(i)].metadata.creator = 'admin ' + str(19 - i)
            model[str(i)].metadata.created = created
            model[str(i)].metadata.modified = modified
            created = created + delta
            modified = modified + delta
        model['nevershown'] = NeverShownChild()
        return model

    def test_sorted_rows(self):
        tmpl = 'cone.app:browser/templates/table.pt'
        contents = ContentsTile(tmpl, None, 'contents')
        contents.model = self.create_dummy_model()
        contents.request = self.layer.new_request()

        # ``sorted_rows`` returns sorted listing items. ``start``, ``end``,
        # ``sort`` and ``order`` are expected by this function
        with self.layer.authenticated('manager'):
            res = contents.sorted_rows(None, None, 'created', 'desc')[0]['title']
            self.checkOutput('...0 Title...', res)

            res = contents.sorted_rows(None, None, 'created', 'desc')[-1]['title']
            self.checkOutput('...18 Title...', res)

            res = contents.sorted_rows(None, None, 'created', 'asc')[0]['title']
            self.checkOutput('...18 Title...', res)

            res = contents.sorted_rows(None, None, 'created', 'asc')[-1]['title']
            self.checkOutput('...0 Title...', res)

    def test_slice(self):
        tmpl = 'cone.app:browser/templates/table.pt'
        contents = ContentsTile(tmpl, None, 'contents')
        contents.model = self.create_dummy_model()
        request = contents.request = self.layer.new_request()

        # ``contents.slice.slice`` return current batch start and positions
        self.assertTrue(isinstance(contents.slice, TableSlice))
        self.assertEqual(contents.slice.slice, (0, 15))

        request.params['b_page'] = '1'
        self.assertEqual(contents.slice.slice, (15, 30))

        del request.params['b_page']

        # ``contents.slice.rows`` return the current sorted row data for listing.
        with self.layer.authenticated('manager'):
            # Items returned by default sorting
            res = contents.slice.rows[0]['title']
            self.checkOutput('...0 Title...', res)

            res = contents.slice.rows[-1]['title']
            self.checkOutput('...14 Title...', res)

            # Inverse order
            request.params['order'] = 'asc'
            res = contents.slice.rows[0]['title']
            self.checkOutput('...18 Title...', res)

            res = contents.slice.rows[-1]['title']
            self.checkOutput('...4 Title...', res)

            # Switch batch page with inversed order
            request.params['b_page'] = '1'
            res = contents.slice.rows[0]['title']
            self.checkOutput('...3 Title...', res)

            res = contents.slice.rows[-1]['title']
            self.checkOutput('...0 Title...', res)

            # Reset order and batch page
            del request.params['order']
            del request.params['b_page']

            # Sort by creator
            request.params['sort'] = 'creator'
            self.assertEqual([row['creator'] for row in contents.slice.rows], [
                'admin 1', 'admin 10', 'admin 11', 'admin 12', 'admin 13',
                'admin 14', 'admin 15', 'admin 16', 'admin 17', 'admin 18',
                'admin 19', 'admin 2', 'admin 3', 'admin 4', 'admin 5'
            ])

            request.params['b_page'] = '1'
            self.assertEqual([row['creator'] for row in contents.slice.rows], [
                'admin 6', 'admin 7', 'admin 8', 'admin 9'
            ])

            # Sort by created
            request.params['b_page'] = '0'
            request.params['sort'] = 'created'

            self.assertEqual(
                contents.slice.rows[0]['created'],
                datetime(2011, 3, 14, 0, 0)
            )
            self.assertEqual(
                contents.slice.rows[-1]['created'],
                datetime(2011, 3, 28, 0, 0)
            )

            request.params['b_page'] = '1'
            request.params['sort'] = 'modified'

            self.assertEqual(
                contents.slice.rows[0]['modified'],
                datetime(2011, 3, 30, 0, 0)
            )

            self.assertEqual(
                contents.slice.rows[-1]['modified'],
                datetime(2011, 4, 2, 0, 0)
            )

            del request.params['b_page']
            del request.params['sort']
"""
Test batch::

    >>> rendered = contents.batch
    >>> rendered = contents.batch
    >>> expected = '<li class="active">\n          <a href="javascript:void(0)">1</a>'
    >>> rendered.find(expected) != -1
    True

    >>> rendered.find('http://example.com/?sort=created&amp;order=desc&amp;b_page=1&amp;size=15') != -1
    True

Change page::

    >>> request.params['b_page'] = '1'
    >>> rendered = contents.batch
    >>> expected = '<li class="active">\n          <a href="javascript:void(0)">2</a>'
    >>> rendered.find(expected) != -1
    True

    >>> rendered.find('http://example.com/?sort=created&amp;order=desc&amp;b_page=0&amp;size=15') != -1
    True

Change sort and order. Sort is proxied by batch::

    >>> request.params['sort'] = 'modified'
    >>> rendered = contents.batch
    >>> rendered.find('http://example.com/?sort=modified&amp;order=desc&amp;b_page=0&amp;size=15') != -1
    True

Rendering fails unauthorized, 'list' permission is required::

    >>> layer.logout()
    >>> request = layer.new_request()

    >>> has_permission('list', model, request)
    <ACLDenied instance at ... with msg "...">

    >>> render_tile(model, request, 'contents')
    Traceback (most recent call last):
      ...
    HTTPForbidden: Unauthorized: tile 
    <cone.app.browser.contents.ContentsTile object at ...> failed 
    permission check

Render authenticated::

    >>> layer.login('manager')
    >>> request = layer.new_request()
    >>> request.params['sort'] = 'modified'
    >>> request.params['b_page'] = '1'
    >>> rendered = render_tile(model, request, 'contents')
    >>> expected = \
    ... '<a href="http://example.com/?sort=title&amp;order=desc&amp;b_page=1&amp;size=15"'
    >>> rendered.find(expected) != -1
    True

Copysupport Attributes::

    >>> model = CopySupportNode()
    >>> model['child'] = CopySupportNode()
    >>> request = layer.new_request()
    >>> rendered = render_tile(model, request, 'contents')
    >>> expected = 'class="selectable copysupportitem"'
    >>> rendered.find(expected) > -1
    True

    >>> request = layer.new_request()
    >>> cut_url = urllib.quote(make_url(request, node=model['child']))
    >>> request.cookies['cone.app.copysupport.cut'] = cut_url
    >>> rendered = render_tile(model, request, 'contents')
    >>> expected = 'class="selectable copysupportitem copysupport_cut"'
    >>> rendered.find(expected) > -1
    True

    >>> layer.logout()

"""