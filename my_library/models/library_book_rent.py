# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class LibraryBookRent(models.Model):
    _name = 'library.book.rent'

    book_id = fields.Many2one('library.book', 'Book', required=True)
    borrower_id = fields.Many2one('res.partner', 'Borrower', required=True)
    state = fields.Selection([('ongoing', 'Ongoing'), ('returned', 'Returned'), ('lost', 'Lost')],
                             'State', default='ongoing', required=True)
    rent_date = fields.Date(default=fields.Date.today)
    return_date = fields.Date()

    @api.model
    def create(self, vals):
        book_rec = self.env['library.book'].browse(
            vals['book_id'])  # returns record set from for given id
        book_rec.make_borrowed()
        return super(LibraryBookRent, self).create(vals)

    def book_return(self):
        self.ensure_one()
        self.book_id.make_available()
        self.write({
            'state': 'returned',
            'return_date': fields.Date.today()
        })

    def book_rent(self):
        self.ensure_one()
        if self.state != 'available':
            raise UserError(_('Book is not available'))
        rent_as_superuser = self.env['library.book.rent'].sudo()
        rent_as_superuser.create({
            'book_id': self.id,
            'borrower_id': self.env.user.partner_id.id,
        })

        #used for public user
        # public_user = self.env.ref('base.public_user')
        # public_book = self.env['library.book'].sudo(public_user)
        # self.env['library.book.rent'].create(public_book)

    def book_lost(self):
        self.ensure_one()
        self.state = 'lost'
        book_with_different_context = self.book_id.with_context(avoid_deactivate=True)
        book_with_different_context.make_lost()
    
        #alternative
        # new_context = self.env.context.copy()
        # new_context.update({'avoid_deactivate': True})
        # book_with_different_context = self.book_id.with_context(new_context)
        # book_with_different_context.make_lost()