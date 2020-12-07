
# -*- coding: utf-8 -*-


from odoo import api, fields, models, _

from datetime import datetime

import time

import logging
_logger = logging.getLogger(__name__)


class inheritEmployeeTms(models.Model):
    _inherit = 'hr.employee'

    
    def service_view(self):
        self.ensure_one()
        domain = [
            ('employee', '=', self.id)]
        return {
            'name': _('Services'),
            'domain': domain,
            'res_model': 'services.tms',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Documents
                        </p>'''),
            'limit': 80,
            'context': "{'default_employee': '%s'}" % self.id
        }

    def return_action_to_open(self):
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('tms', xml_id)
            res.update(
                context=dict(self.env.context, default_employee=self.id, group_by=False),
                domain=[('employee', '=', self.id)]
            )
            return res
        return False


    def _service_count(self):
        for each in self:
            service_ids = self.env['services.tms'].search([('employee', '=', each.id)])
            each.service_count = len(service_ids)
            
    document_count = fields.Integer(compute='_document_count', string='# Documentos')
    
    service_count = fields.Integer(compute='_service_count', string='# Servicios')
    

class resumenMensualEmployee(models.Model):
    _name = 'resumen.hr.employee'

    name = fields.Char(string="Mes")
    date_start = fields.Date(string='Inicio')
    date_stop = fields.Date(string='Fin')
    employee = fields.Many2one('hr.employee', string='Empleado')
    
    lista_servicios = fields.Many2many('services.tms', compute="_compute_data",string="Servicios")



    @api.depends('date_start', 'date_stop', 'employee')
    def _compute_data(self):
        # Definimos el dominio con el cual queremos filtrar los datos que vamos a traer de la clase service.services
        servicios_domain = [
            ('employee', 'in', self.employee.ids),
            ('date_start', '>=', self.date_start),
            ('date_start', '<=', self.date_stop),
        ]
        # Traemos los servicios de dicha clase y los ordenamos por los valores que querramos, en caso de querer ordenar por mas valores, seguir con una coma ingresar el campo y el orden
        servicios = self.env['services.tms'].search(servicios_domain, order='date_start asc')
        self.lista_servicios = servicios
