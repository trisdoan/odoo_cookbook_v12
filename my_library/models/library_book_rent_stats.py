from odoo import models, fields, api, tools


class LibraryBookRentStats(models.Model):
    _name = "library.book.rent.stats"
    # manage data table by myself
    _auto = False

    book_id = fields.Many2one('library.book', 'Book', readonly=True)
    rent_count = fields.Integer(string="Times borrowed", readonly=True)
    avg_occupation = fields.Integer(
        string="Average Occupation (days)", readonly=True)

    # publisher_id = fields.Many2one(
    #     'res.partner', related='book_id.publisher_id', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            create or replace view library_book_rent_stats as (
            select
                lbr.book_id,
                count(lbr.id) as rent_count,
                avg(extract(epoch from age(return_date, rent_date))/86400))::int as avg_occupation
            from library_book_rent as lbr
            join library_book as lb on lb.id = lbr.book_id
            where lbr.state = 'returned'
            group by lbr.book_id
            )
        """
