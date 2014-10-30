#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python imports

# GAE imports
import webapp2
from webapp2_extras import jinja2

# local imports


class BaseHandler(webapp2.RequestHandler):
    """
    Simple base handler for Jinja2 template rendering.
    """

    @webapp2.cached_property
    def jinja2(self):
        """
        Cached property holding a Jinja2 instance.
        :return:
        A Jinja2 object for the current app.
        """
        return jinja2.get_jinja2(app=self.app)

    def render_template(self, template, **kwargs):
        """
        Use Jinja2 instance to render template and write to output.
        :param template: filename (relative to $PROJECT/templates) that we're rendering
        :param kwargs: keyword arguments corresponding to variables in template.
        """
        self.response.write(self.jinja2.render_template(template, **kwargs))
