from odoo import fields, models


class ColGenre(models.Model):
    _name = "col.genre"
    _description = "Content Genre"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    _sql_constraints = [("name_uniq", "unique(name)", "Genre must be unique.")]


class ColTag(models.Model):
    _name = "col.tag"
    _description = "Content Tag / Sub-genre"
    _order = "name"

    name = fields.Char(required=True)
    color = fields.Integer()


class ColLanguage(models.Model):
    _name = "col.language"
    _description = "Content Language"
    _order = "name"

    name = fields.Char(required=True)        # English, Chinese, Korean, Thai...
    code = fields.Char()                     # EN, CN, KO, TH, ID
    _sql_constraints = [("code_uniq", "unique(code)", "Language code must be unique.")]


class ColMedia(models.Model):
    _name = "col.media"
    _description = "Media / Platform Type"
    _order = "name"

    name = fields.Char(required=True)        # SVOD, AVOD, Telco/Carrier, FAST, CTV...
    code = fields.Char()
    _sql_constraints = [("code_uniq", "unique(code)", "Media code must be unique.")]
