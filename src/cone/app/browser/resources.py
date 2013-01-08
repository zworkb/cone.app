import os
import pkg_resources
import cone.app
from webob import Response
from paste.urlparser import StaticURLParser
from pyramid.static import PackageURLParser
from pyramid.view import view_config
from pyramid.security import authenticated_userid
from cone.tile import (
    tile,
    Tile,
)
from cone.app.utils import app_config


class MergedResources(object):

    def __init__(self, request):
        self.request = request

    def merged_resources(self, resources):
        data = ''
        for view, subpath in resources:
            if isinstance(view.app, PackageURLParser):
                path = pkg_resources.resource_filename(
                    view.app.package_name,
                    os.path.join(view.app.resource_name, subpath))
            elif isinstance(view.app, StaticURLParser):
                path = os.path.join(view.app.directory, subpath)
            else:
                raise ValueError(
                    u"Unknown resources view app %s" % str(view.app))
            with open(path, 'r') as file:
                data += file.read() + '\n\n'
        return data


@view_config('cone.js')
def cone_js(model, request):
    resources = MergedResources(request)
    cfg = app_config()
    data = resources.merged_resources(cfg.js.core_merged)
    data += resources.merged_resources(cfg.js.public_merged)
    if authenticated_userid(request):
        data += resources.merged_resources(cfg.js.protected_merged)
    return Response(data)


@view_config('cone.css')
def cone_css(model, request):
    resources = MergedResources(request)
    cfg = app_config()
    data = resources.merged_resources(cfg.css.core_merged)
    data += resources.merged_resources(cfg.css.public_merged)
    if authenticated_userid(request):
        data += resources.merged_resources(cfg.css.protected_merged)
    response = Response(data)
    response.headers['Content-Type'] = 'text/css'
    return response


@view_config('print.css')
def print_css(model, request):
    resources = MergedResources(request)
    cfg = app_config()
    data = resources.merged_resources(cfg.css.public_print)
    if authenticated_userid(request):
        data += resources.merged_resources(cfg.css.protected_print)
    response = Response(data)
    response.headers['Content-Type'] = 'text/css'
    return response


@tile('resources', 'templates/resources.pt', permission='login')
class Resources(Tile):
    """Resources tile.
    """

    @property
    def authenticated(self):
        return authenticated_userid(self.request)

    @property
    def cfg(self):
        return app_config()

    def resource_url(self, resource):
        if resource.startswith('http'):
            return resource
        return '%s/%s' % (self.request.application_url, resource)
