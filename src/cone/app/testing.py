from pyramid.threadlocal import get_current_registry
from pyramid.interfaces import (
    IAuthenticationPolicy,
    IAuthorizationPolicy,
)
from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from plone.testing import Layer

def groups_callback(name, request):
    if name == 'viewer':
        return ['role:editor']
    if name == 'editor':
        return ['role:editor']
    if name == 'owner':
        return ['role:owner']
    if name == 'manager':
        return ['role:manager']
    return []

class Security(Layer):

    def authenticate(self, login):
        self.authn.unauthenticated_userid = lambda *args: login
        
    def logout(self):
        self.authn.unauthenticated_userid = lambda *args: None
    
    def setUp(self, args=None):
        self.authn = CallbackAuthenticationPolicy()
        self.authn.callback = groups_callback
        self.authn.unauthenticated_userid = lambda *args: None
        self.authz = ACLAuthorizationPolicy()
        self.registry = get_current_registry()
        self.registry.settings = dict()
        self.registry.registerUtility(self.authn, IAuthenticationPolicy)
        self.registry.registerUtility(self.authz, IAuthorizationPolicy)
        print "Security set up."

    def tearDown(self):
        self.registry.unregisterUtility(self.authn, IAuthenticationPolicy)
        self.registry.unregisterUtility(self.authz, IAuthorizationPolicy)
        print "Security torn down."