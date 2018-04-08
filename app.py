#!/usr/bin/env python3
import os

import tornado.ioloop
import tornado.web
import tornado.log

import markdown2
import queries

from jinja2 import \
  Environment, PackageLoader, select_autoescape

ENV = Environment(
  loader=PackageLoader('blog', 'templates'),
  autoescape=select_autoescape(['html', 'xml'])
)

class TemplateHandler(tornado.web.RequestHandler):
  def initialize(self):
    self.session = queries.Session(
      'postgresql://postgres@localhost:5432/blog')
      
  def render_template (self, tpl, context):
    template = ENV.get_template(tpl)
    self.write(template.render(**context))
    
class MainHandler(TemplateHandler):
  def get (self):
    posts = self.session.query('SELECT * FROM post')
    self.render_template("home.html", {'posts': posts})
    
class AuthorHandler(TemplateHandler):
  def get (self):
    authors = self.session.query('SELECT * FROM author')
    self.render_template("authors.html", {'authors': authors})
    
class BlogPostHandler(TemplateHandler):
  def get (self, slug):
    posts = self.session.query(
      'SELECT * FROM post INNER JOIN author ON post.author_id=author.id WHERE slug = %(slug)s',
      {'slug': slug}
    )
    #comments = self.session.query(
    #  'SELECT * FROM comments INNER JOIN post ON post.id=comments.post_id WHERE slug = %(slug)s',
    #  {'slug': slug}
    #  )
   # print(comments[0])
    
    html = markdown2.markdown(posts[0]['body'])
    context = {
      'post': posts[0],
      'html': html
    }
    self.render_template("post.html", context)
    
class CommentHandler(TemplateHandler):
  def get (self, slug):
    posts = self.session.query(
      'SELECT * FROM post WHERE slug = %(slug)s',
      {'slug': slug}
    )
    print(posts[0])
    self.render_template("comment.html", {'post': posts[0]})
    
  def post (self, slug):
    comment = self.get_body_argument('comment')
    posts = self.session.query(
      'SELECT * FROM post WHERE slug = %(slug)s',
      {'slug': slug}
    )
    self.session.query(
      'INSERT INTO comments VALUES(DEFAULT, %(post_id)s, %(comment)s)',
      {'post_id': posts[0]['id'], 'comment':comment}
    )
    self.redirect('/post/' + slug)
    
def make_app():
  return tornado.web.Application([
    (r"/", MainHandler),
    (r"/post/(.*)/comment", CommentHandler),
    (r"/post/(.*)", BlogPostHandler),
    (r"/authors", AuthorHandler),
    (r"/static/(.*)", 
      tornado.web.StaticFileHandler, {'path': 'static'}),
  ], autoreload=True)
  
if __name__ == "__main__":
  tornado.log.enable_pretty_logging()
  app = make_app()
  app.listen(int(os.environ.get('PORT', '8080')))
  tornado.ioloop.IOLoop.current().start()