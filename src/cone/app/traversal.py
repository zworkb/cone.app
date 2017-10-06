from node.interfaces import INode
from pyramid.traversal import ResourceTreeTraverser
from zope.component import adapter


@adapter(INode)
class NodeTraverser(ResourceTreeTraverser):

    def __call__(self, request):
        # XXX: quote / inside path element
        #      related: cone.tile.Tile.nodeurl
        #      related: cone.app.browser.utils.make_url
        #      related: cone.app.browser.utils.make_query
        # XXX: check INode.providedBy(ob)
        return super(NodeTraverser, self).__call__(request)

        environ = request.environ
        matchdict = request.matchdict
        if matchdict is not None:
            path = matchdict.get('traverse', slash) or slash
            if is_nonstr_iter(path):
                # this is a *traverse stararg (not a {traverse})
                # routing has already decoded these elements, so we just
                # need to join them
                path = '/' + slash.join(path) or slash
            subpath = matchdict.get('subpath', ())
            if not is_nonstr_iter(subpath):
                # this is not a *subpath stararg (just a {subpath})
                # routing has already decoded this string, so we just need
                # to split it
                subpath = split_path_info(subpath)
        else:
            # this request did not match a route
            subpath = ()
            try:
                # empty if mounted under a path in mod_wsgi, for example
                path = request.path_info or slash
            except KeyError:
                # if environ['PATH_INFO'] is just not there
                path = slash
            except UnicodeDecodeError as e:
                raise URLDecodeError(
                    e.encoding, e.object, e.start, e.end, e.reason)
        if self.VH_ROOT_KEY in environ:
            # HTTP_X_VHM_ROOT
            vroot_path = decode_path_info(environ[self.VH_ROOT_KEY])
            vroot_tuple = split_path_info(vroot_path)
            vpath = vroot_path + path # both will (must) be unicode or asciistr
            vroot_idx = len(vroot_tuple) - 1
        else:
            vroot_tuple = ()
            vpath = path
            vroot_idx = -1
        root = self.root
        ob = vroot = root
        if vpath == slash: # invariant: vpath must not be empty
            # prevent a call to traversal_path if we know it's going
            # to return the empty tuple
            vpath_tuple = ()
        else:
            # we do dead reckoning here via tuple slicing instead of
            # pushing and popping temporary lists for speed purposes
            # and this hurts readability; apologies
            i = 0
            view_selector = self.VIEW_SELECTOR
            vpath_tuple = split_path_info(vpath)
            for segment in vpath_tuple:
                if segment[:2] == view_selector:
                    return {
                        'context': ob,
                        'view_name': segment[2:],
                        'subpath': vpath_tuple[i + 1:],
                        'traversed': vpath_tuple[:vroot_idx + i + 1],
                        'virtual_root': vroot,
                        'virtual_root_path': vroot_tuple,
                        'root': root
                    }
                def current():
                    return {
                        'context': ob,
                        'view_name': segment,
                        'subpath': vpath_tuple[i + 1:],
                        'traversed': vpath_tuple[:vroot_idx + i + 1],
                        'virtual_root': vroot,
                        'virtual_root_path': vroot_tuple,
                        'root': root
                    }
                try:
                    getitem = ob.__getitem__
                except AttributeError:
                    return current()
                try:
                    next = getitem(segment)
                    if not INode.providedBy(next):
                        return current()
                except KeyError:
                    return current()
                if i == vroot_idx:
                    vroot = next
                ob = next
                i += 1
        return {
            'context': ob,
            'view_name': empty,
            'subpath': subpath,
            'traversed': vpath_tuple,
            'virtual_root': vroot,
            'virtual_root_path': vroot_tuple,
            'root': root
        }
