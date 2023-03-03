# -*- coding: utf-8 -*-
from odoo import models, fields
import logging
from logging import Logger


class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'

    name = fields.Char('Title', required=True)
    date_release = fields.Date('Release Date')
    active = fields.Boolean(default=True)
    author_ids = fields.Many2many('res.partner', string='Authors')
    state = fields.Selection(
        [('available', 'Available'),
         ('borrowed', 'Borrowed'),
         ('lost', 'Lost')],
        'State', default="available")
    cost_price = fields.Float('Book Cost')
    category_id = fields.Many2one('library.book.category')

    def make_available(self):
        self.ensure_one()
        self.state = 'available'

    def make_borrowed(self):
        self.ensure_one()
        self.state = 'borrowed'

    def make_lost(self):
        self.ensure_one()
        self.state = 'lost'
        if not self.env.context.get('avoid_deactivate'):
            self.active = False

    def average_book_occupation(self):
        sql_query = """
            select
                lbr.name,
                avg((extract(epoch from age(return_date, rent_date)) / 86400))::int
            from library_book_rent as lib
            join library_book as lbr on lbr.id = lib.book_id
            where lib.state = 'returned'
            group by lbr.name; 
        """
        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchall()
        Logger.info("average book occupation: %s", result)
