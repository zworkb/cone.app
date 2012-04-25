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
from webob import Response
from pyramid.view import view_config
from pyramid.i18n import (
    TranslationStringFactory,
    get_localizer,
)
from cone.app.model import AppSettings
from cone.app.browser.utils import make_url
from cone.app.browser.ajax import (
    AjaxAction,
    ajax_form_fiddle,
)

_ = TranslationStringFactory('cone.app')


@view_config('settings_tab_content', xhr=True, permission='manage')
def settings_tab_content(model, request):
    """Used by jquerytools tabs plugin to get settings section content.
    """
    try:
        rendered = render_tile(model, request, 'content')
    except Exception, e:
        localizer = get_localizer(request)
        error = localizer.translate(_('error', 'Error'))
        rendered = '<div class="box">%s: %s</div>' % (error, str(e))
    return Response('<div class="%s">%s</div>' % (model.name, rendered))


@tile('content', 'templates/settings.pt',
      interface=AppSettings, permission='manage')
class AppSettings(Tile):
    
    @property
    def tabs(self):
        ret = list()
        for val in self.model.values():
            ret.append({
                'title': val.metadata.title,
                'target': make_url(self.request,
                                   node=val,
                                   resource='settings_tab_content'),
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
        url = make_url(request.request, node=self.model)
        selector = '.%s' % self.model.name
        return [
            AjaxAction(url, 'content', 'inner', selector),
        ]