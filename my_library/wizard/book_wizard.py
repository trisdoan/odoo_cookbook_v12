

from odoo import api, models, fields


class LibraryRentWizard(models.TransientModel):
    _name = 'library.rent.wizard'
    borrower_id = fields.Many2one('res.partner', string='Borrower')
    # do not add One2many from transient to normal model
    book_ids = fields.Many2many('library.book', string='Books')

    def add_book_rents(self):
        self.ensure_one()
        rentModel = self.env['library.book.rent']
        for wiz in self:
            for book in wiz.book_ids:
                rentModel.create({
                    'borrower_id': wiz.borrower_id.id,
                    'book_id': book.id
                })

        borrowers = self.mapped('borrower_id')
        action = borrowers.get_formview_action()
        if len(borrowers.ids) > 1:
            action['domain'] = [('id', 'in', tuple(borrowers.ids))]
            action['view_mode'] = 'tree,form'
        return action


class LibraryReturnWizard(models.TransientModel):
    _name = 'library.return.wizard'
    borrower_id = fields.Many2one('res.partner', string='Borrower')
    book_ids = fields.Many2many('library.book', string='Books')

    def books_returns(self):
        loan = self.env['library.book.rent']
        for rec in self:
            loans = loan.search(
                [('state', '=', 'ongoing'),
                 ('book_id', 'in', rec.book_ids.ids),
                 ('borrower_id', '=', rec.borrower_id.id)]
            )
            for loan in loans:
                loan.book_return()

    @api.onchange('borrower_id')
    def onchange_borrower_id(self):
        loan = self.env['library.book.rent']
        books_on_rent = loan.search(
            [('state', '=', 'ongoing'),
             ('borrower_id', '=', self.borrower_id.id)]
        )
        self.book_ids = books_on_rent.mapped('book_id')
        result = {
            'domain': {'book_ids': [
                ('id', 'in', self.book_ids.ids)
            ]}
        }
        late_domain = [
            ('id', 'in', books_on_rent.ids),
            ('return_date', '<', fields.Date.today())
        ]
        late_books = loan.search(late_domain)
        if late_books:
            message = ('Warn the member that the following books are late:\n')
            titles = late_books.mapped('book_id.name')
            result['warning'] = {
                'title': 'Late books',
                'message': message + '\n'.join(titles)
            }
        return result

    @api.multi
    def return_all_books(self):
        self.ensure_one()
        wizard = self.env['library.return.wizard']
        values = {
            'borrower_id': self.env.user.partner_id.id,
        }
        specs = wizard._onchange_spec()
        updates = wizard.onchange(values, ['borrower_id'], specs)
        value = updates.get('value', {})
        for name, val in value.items():
            if isinstance(val, tuple):
                value[name] = val[0]
        values.update(value)
        wiz = wizard.create(values)
        return wiz.sudo().books_returns()
