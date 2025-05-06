# -*- coding: utf-8 -*-

from odoo import models, fields, api   # type: ignore
from odoo.exceptions import ValidationError  # type: ignore


class Sentencias(models.Model):
    _name = 'ctm.sentencias'
    _description = "Sentencias Cuantum"
    _inherit = []

    name = fields.Char('Nombre', required=1)
    emisor = fields.Many2one('res.partner', 'Emisor', required=1)
    pagador = fields.Many2one('res.partner', 'Pagador', required=1)
    codigo = fields.Char('Código', required=1)
    statum = fields.Selection(
        string='Statum',
        selection=[
            ('CSF', 'CSF'),
            ('Statum Compartimento 1', 'Statum Compartimento 1'),
            ('Statum Compartimento 2', 'Statum Compartimento 2'),
            ('Statum Compartimento 3', 'Statum Compartimento 3'),
            ('Statum Compartimento 4', 'Statum Compartimento 4'),
            ('Statum Compartimento 5', 'Statum Compartimento 5'),
            ('Statum Compartimento 6', 'Statum Compartimento 6'),
            ('Statum Compartimento 7', 'Statum Compartimento 7'),
            ('Statum Compartimento 8', 'Statum Compartimento 8'),
            ('Statum Compartimento 9', 'Statum Compartimento 9'),
        ],
        default='CSF',
        required=True
    )
    fecha_ejecutoria = fields.Date('Fecha de Ejecutoría', required=1)
    fecha_cuenta_cobro = fields.Date('Fecha de Cuenta de Cobro', required=1)
    fecha_liquidar = fields.Date('Fecha a Liquidar', required=1)
    valor_condena = fields.Float('Valor Condena', required=1)
    nit_fcp_statum = fields.Char('NIT FCP STATUM (Comp 1)')
    vendedor = fields.Char('Vendedor')
    nemotecnico = fields.Char('Nemotecnico')
    fecha_vencimiento = fields.Date('Fecha de Vencimiento')
    valor_giro = fields.Float('Valor Giro')
    comision = fields.Float('Comisión', default=0.0)
    valor_contable_ayer = fields.Float('Valor Contable Ayer')
    precio = fields.Float('Precio', required=1)
    costas = fields.Float('Costas')

    #  Descuentos
    retencion_total = fields.Float('Retención Total')
    estructuracion = fields.Float('Estructuración')
    intermediacion = fields.Float('Intermediación')
    descuento_diluido = fields.Float('Descuento Diluido')
    comision_gestion_cuantum = fields.Float('Comisión Gestión Cuantum')
    ingreso_anticipado_cuantum = fields.Float('Ingreso Anticipado Cuantum')
    comision_interna = fields.Float('Comisión Interna')
    # Poner regla cada nueva fecha debe ser mayor a las anteriores
    fecha_liquidar_neutral = fields.Date('Fecha a Liquidar Neutral')
    fecha_liquidar_optimista = fields.Date('Fecha a Liquidar Optimista')
    fecha_compra = fields.Date('Fecha de Compra')
    fecha_liquidar_acido = fields.Date('Fecha a Liquidar Ácido')

    state = fields.Selection(
        string='Estado',
        selection=[
            ('negociacion', 'Negociación'),
            ('proyeccion', 'Proyección'),
            ('venta_completa', 'Venta Completa'),
        ],
        default='negociacion',
        required=True
    )
    proyeccion_ids = fields.One2many('ctm.proyecciones', 'sentencia_id', string='Proyecciones')

    @api.model
    def create(self, vals):
        res = super(Sentencias, self).create(vals)

        if res.statum != 'CSF':
            if not res.nit_fcp_statum:
                raise ValidationError('Debe ingresar el NIT FCP STATUM')
            if not res.vendedor:
                raise ValidationError('Debe ingresar el Vendedor')
            if not res.nemotecnico:
                raise ValidationError('Debe ingresar el Nemotecnico')
            if not res.fecha_vencimiento:
                raise ValidationError('Debe ingresar la Fecha de Vencimiento')
            if not res.fecha_compra:
                raise ValidationError('Debe ingresar la Fecha de Compra')
        elif res.statum == 'CSF':
            if not res.fecha_liquidar_neutral:
                raise ValidationError('Debe ingresar la Fecha a Liquidar Neutral')
            if not res.fecha_liquidar_optimista:
                raise ValidationError('Debe ingresar la Fecha a Liquidar Optimista')
            if not res.fecha_liquidar_acido:
                raise ValidationError('Debe ingresar la Fecha a Liquidar Ácido')
        return res

    def write(self, vals):
        res = super(Sentencias, self).write(vals)
        if self.statum != 'CSF':
            if not self.nit_fcp_statum:
                raise ValidationError('Debe ingresar el NIT FCP STATUM')
            if not self.vendedor:
                raise ValidationError('Debe ingresar el Vendedor')
            if not self.nemotecnico:
                raise ValidationError('Debe ingresar el Nemotecnico')
            if not self.fecha_vencimiento:
                raise ValidationError('Debe ingresar la Fecha de Vencimiento')
            if not self.fecha_compra:
                raise ValidationError('Debe ingresar la Fecha de Compra')
        elif self.statum == 'CSF':
            if not self.fecha_liquidar_neutral:
                raise ValidationError('Debe ingresar la Fecha a Liquidar Neutral')
            if not self.fecha_liquidar_optimista:
                raise ValidationError('Debe ingresar la Fecha a Liquidar Optimista')
            if not self.fecha_liquidar_acido:
                raise ValidationError('Debe ingresar la Fecha a Liquidar Ácido')
        return res

    def generar_proyeccion(self):
        for record in self:
            record.proyeccion_ids.unlink()
            proyeccion_id = self.env['ctm.proyecciones'].create({
                'name': f"Proyección Sentencia - {record.name}",
                'sentencia_id': record.id,
            })
            proyeccion_id.calcular_proyeccion()
            record.write({'state': 'proyeccion'})

    def action_view_proyecciones(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Proyecciones',
            'view_mode': 'tree,form',
            'res_model': 'ctm.proyecciones',
            'domain': [('sentencia_id', '=', self.id)],
            'context': "{'create': False, 'delete': False, 'open': True}",
        }

    def vendida(self):
        self.write({'state': 'venta_completa'})

    def generar_proyecciones(self):
        for record in self:
            record.generar_proyeccion()
