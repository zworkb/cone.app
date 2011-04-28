from plumber import (
    Part,
    default,
    plumb,
)
from cone.tile import (
    tile,
    Tile,
    render_tile,
)
from webob.exc import HTTPFound
from cone.app.model import AppSettings
from cone.app.browser.utils import make_url
from cone.app.browser.ajax import (
    AjaxAction,
    ajax_form_fiddle,
)


@tile('content', 'templates/settings.pt',
      interface=AppSettings, permission='manage')
class AppSettings(Tile):
    
    @property
    def tabs(self):
        ret = list()
        for key, value in self.model.items():
            ret.append({
                'title': value.metadata.title,
                'content': render_tile(value, self.request, 'content'),
                'css': value.__name__,
            })
        return ret


class SettingsPart(Part):
    """Particular settings object form part.
    """
    
    @plumb
    def prepare(_next, self):
        _next(self)
        selector = '#form-%s' % '-'.join(self.form.path)
        ajax_form_fiddle(self.request, selector, 'replace')
    
    @default
    def next(self, request):
        if self.ajax_request:
            url = make_url(request.request, node=self.model)
            selector = '.%s' % self.model.__name__
            return [
                AjaxAction(url, 'content', 'inner', selector),
            ]
        url = make_url(request.request, node=self.model.__parent__)
        return HTTPFound(location=url)