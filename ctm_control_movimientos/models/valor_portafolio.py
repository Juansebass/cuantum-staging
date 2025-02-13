from odoo import models, fields, api  # type: ignore
from odoo.exceptions import ValidationError  # type: ignore
import base64


class ValorPortafolio(models.Model):
    _name = 'ctm.valor_portafolio'
    _description = 'Valor Portafolio'

    name = fields.Char(string='Nombre')
    fecha_corte = fields.Date(string='Fecha de Corte', required=True)
    client_file = fields.Binary('Archivo')
    file_content = fields.Text('Texto archivo')
    delimiter = fields.Char('Delimitador', default=";")
    responsable = fields.Many2one('res.partner', 'Responsable de proceso')
    state = fields.Selection(
        selection=[('draft', 'Borrador'), ('processed', 'Procesado')],
        string='Estado',
        default='draft'
    )
    skip_first_line = fields.Boolean('Saltar primera linea', default=True)
    cliente_ids = fields.One2many('ctm.valor_portafolio_clientes', 'valor_portafolio_id', 'Clientes')
    informe_cliente_ids = fields.One2many('ctm.valor_portafolio_informe_clientes', 'valor_portafolio_id', 'Informe Clientes')

    @api.model
    def create(self, var):
        res = super(ValorPortafolio, self).create(var)
        res.name = 'Valor Portafolio ' + res.fecha_corte.strftime('%Y-%m-%d')
        return res

    def action_cargar_clientes(self):
        self.ensure_one()
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.client_file:
            raise ValidationError('Debe seleccionar el archivo')

        self.file_content = base64.decodebytes(self.client_file)
        content = self.file_content.replace('\n', '')
        lines = content.split('\r')

        for cliente in self.cliente_ids:
            cliente.unlink()

        for i, line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)
            partner_name = lista[0]
            partner = self.env['res.partner'].search([('name', '=', partner_name)], limit=1)
            if not partner:
                raise ValidationError('No se encontró el cliente {0}'.format(partner_name))
            self.env['ctm.valor_portafolio_clientes'].create({
                'valor_portafolio_id': self.id,
                'partner_id': partner.id
            })

    def crear_valor_portafolio(self):
        pass


class ValorPortafolioClientes(models.Model):
    _name = 'ctm.valor_portafolio_clientes'
    _description = 'Clientes del Valor Portafolio'

    valor_portafolio_id = fields.Many2one('ctm.valor_portafolio', 'Valor Portafolio')
    partner_id = fields.Many2one('res.partner', 'Cliente')


class ValorPortafolioInformeClientes(models.Model):
    _name = 'ctm.valor_portafolio_informe_clientes'
    _description = 'Informe de Clientes del Valor Portafolio'

    valor_portafolio_id = fields.Many2one('ctm.valor_portafolio', 'Valor Portafolio')
    partner_id = fields.Many2one('res.partner', 'Cliente')
    freelance_id = fields.Many2one('res.partner', 'Freelance')
    factoring_csf = fields.Float('Factoring CSF')
    libranzas_csf = fields.Float('Libranzas CSF')
    sentencias_csf = fields.Float('Sentencias CSF')
    mutuo_csf = fields.Float('Mutuo CSF')
    rpr_csf = fields.Float('RPR CSF')
    libranzas_fcl = fields.Float('Libranzas FCL')
    rpr_fcl = fields.Float('RPR FCL')
    statum_fcl = fields.Float('Statum FCL')
    sentencias_fcl = fields.Float('Sentencias FCL')
    s1_fcl = fields.Float('S1 FCL')
    s2_fcl = fields.Float('S2 FCL')
    rpr_fcl = fields.Float('RPR FCL')
    total = fields.Float('Total')
